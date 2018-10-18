import json
from flask import Blueprint, render_template, request, redirect, session, url_for, flash, Response, g
from models.sequence import Sequence
from models.component import Component
from models.user import User, SOFIEBIO_ACCOUNTID
from models.forum import Forum
from models.comment import Comment
from models.follower import Follower
from models.statuslog import StatusLog
from models.sequenceattachment import SequenceAttachment
import models.model_helpers as model_helpers
import base64,zipfile,io,os
import modules
from sqlalchemy import or_, and_

db = modules.database.get_db()

commentcontroller = Blueprint("commentcontroller", __name__, template_folder="../templates/comment", url_prefix="/comment/")

@commentcontroller.route("<int:comment_id>/",methods=["DELETE"])
def delete_comment(comment_id):
    comment = Comment.query.filter_by(CommentID=comment_id).first()

    if not (g.user.UserID == comment.UserID or str(g.user.role.Type) == 'super-admin'):
        return Response({"error_details": "No Permissions Error"}, status=400, content_type="application/json")

    db.session.delete(comment)
    db.session.commit()
    attachments = SequenceAttachment.query.filter(and_(SequenceAttachment.Type=='comments',
                                                       SequenceAttachment.ParentID==comment_id)).all()
    for attachment in attachments:
        db.session.delete(attachment)
    db.session.commit()
    return "OK"

@commentcontroller.route("attachment", methods=["POST"])
def create_attachment():
    data = request.form
    image = request.files['file']
    name = image.filename
    contenttype = image.content_type
    image = image.stream.read()
    parentid = data['ParentID']
    type = data['Type']

    comment = Comment(ParentID=parentid,Type=type,Message="",RenderType='attachment',UserID=g.user.UserID)
    comment.save()

    print comment.CommentID

    attachment = SequenceAttachment(Attachment=image,ParentID=comment.CommentID,Type='comments',FileName=name, ContentType = contenttype)
    attachment.save()

    comment.Message = json.dumps({"url": "/comment/%s/attachment/%s/" % (comment.CommentID, attachment.SequenceAttachmentID),
                                  "name": name})
    comment.save()

    if comment.Type == 'Forums':
        forum = Forum.query.filter(Forum.ForumID==comment.ParentID).first()
        if forum and forum.SFDC_ID:
            attachment.create_case_attachment(forum.SFDC_ID)

    print comment.CommentID
    resp = comment.to_hash()
    resp = json.dumps(resp)

    return Response(resp,content_type='application/json')

@commentcontroller.route("image", methods=["POST"])
def create_image():
    file_name = 'SPN Image Attachment'
    if request.headers.get('Content-Type', "").startswith('application/json'):
        data = request.json
        data = request.json
        image = base64.b64decode(data['Image'])
    else:
        data = request.form
        image = request.files['file'].read()
        file_name = "Unknown_Image"#request.files['file']

    parentid = data['ParentID']
    type = data['Type']
    comment = Comment(ParentID=parentid,Type=type,Message="",RenderType='image',UserID=g.user.UserID)
    comment.save()

    print comment.CommentID

    attachment = SequenceAttachment(Attachment=image,ParentID=comment.CommentID,Type='comments',FileName=file_name)
    attachment.save()

    forum = Forum.query.filter(Forum.ForumID==parentid).first()

    if forum and forum.SFDC_ID:
        attachment.create_case_attachment(forum.SFDC_ID)

    print comment.CommentID
    resp = comment.to_hash()
    resp = json.dumps(resp)

    return Response(resp,content_type='application/json')

@commentcontroller.route("<parent_type>/<int:parent_id>/count/", methods=['GET'])
def get_comment_count(parent_type, parent_id):
    comments = Comment.query.filter(and_(Comment.Type==parent_type,
                                         Comment.ParentID==parent_id)).count()
    return Response(json.dumps(comments), content_type='application/json')

@commentcontroller.route("<int:parent_id>/attachment/<int:attachment_id>/", methods=['GET'])
def get_attachment(parent_id, attachment_id):
    comment = Comment.query.filter(Comment.CommentID==parent_id).first()

    if comment.Type == 'Forums':
        # if the user does not follow the forum, do not allow them to download it
        follower = Follower.query.filter(and_(Follower.Type=='Forums',
                                      Follower.ParentID==comment.ParentID,
                                      Follower.UserID==g.user.UserID)).first()
        if not follower:
            return Response("You do not have access to this attachment", 401)

    attachment = SequenceAttachment.query.filter(and_(SequenceAttachment.SequenceAttachmentID==attachment_id,
                                                      SequenceAttachment.Type=='comments'
                                                 )).first()
    resp = Response(attachment.Attachment)
    resp.headers['Content-Disposition'] = "attachment; filename="+ '"' +attachment.FileName+'"'
    resp.headers['Content-Type'] = attachment.ContentType
    return resp


@commentcontroller.route("<int:comment_id>/image", methods=["GET"])
def get_image(comment_id):
    attachment = SequenceAttachment.query.filter(and_(SequenceAttachment.ParentID==comment_id,
                                                SequenceAttachment.Type=='comments')).first()
    if attachment is not None and attachment.Attachment:
        return attachment.Attachment
    default_image = open("static/img/default-user.png", "rb")
    return default_image.read()

@commentcontroller.route("",methods=["POST"])
def make_comment():
    data = request.form
    parent_id = data["ParentID"]
    comment_type = data["Type"]
    msg = data["Message"]
    user_id = session["userid"]
    comm = Comment(Message=msg, UserID=user_id, ParentID=parent_id, Type=comment_type)
    comm.save()
    ## Printing this  otherwise to_hash does not include the comment id
    print comm.CommentID
    ## Do not remove the print above, otherwise to_hash will not include the comment id
    resp = comm.to_hash()
    running_user = User.query.filter_by(UserID=user_id).first()
    #email_sender.comment_on_probe(running_user, sequence, msg)
    return json.dumps(resp)

@commentcontroller.route("<type>/<int:parent_id>/comments",methods=["GET"])
def get_comments(type, parent_id):
    offset = request.args.get('offset', 0)
    pagination_size = 10
    type = str(type)
    if type == "Comments":
        ordering = Comment.CreationDate.asc()
    else:
        ordering = Comment.CreationDate.desc()

    if type=='Forums' and g.user.AccountID != SOFIEBIO_ACCOUNTID:
        forum = Forum.query.filter(and_(Forum.ForumID==parent_id,
                                        or_(Forum.AccountID==g.user.AccountID, Forum.AccountID==SOFIEBIO_ACCOUNTID)
                                   )).first()
        if not forum:
            return Response("You are not allowed to view these comments", 402)

    comments = Comment.query.filter(and_(Comment.ParentID == parent_id,
                                         Comment.Type == type)).order_by(ordering).offset(offset).limit(pagination_size+1).all()
    has_more = len(comments) == pagination_size + 1
    comments = comments[0:pagination_size]
    comments = [comment.to_hash() for comment in comments]
    return Response(json.dumps({"comments": comments, "has_more": has_more}), headers={"Content-Type": "application/json"})
