import json
from flask import Blueprint, render_template, request, redirect, session, url_for, flash, Response, g
from models.sequence import Sequence
from models.component import Component
from models.user import User, SOFIEBIO_ACCOUNTID
from models.comment import Comment
from models.follower import Follower
from models.statuslog import StatusLog
from models.sequenceattachment import SequenceAttachment
from models.notification import Notification
from models.forum import Forum
from models.user import SOFIEBIO_USER
import modules.sfdc as sfdc
import models.model_helpers as model_helpers
import base64,zipfile,io,os
import modules
from sqlalchemy import or_, and_
import email_sender


db = modules.database.get_db()

def SOFIE_AUTO_FOLLOWING_USER_IDS():
    return os.getenv("SOFIE_AUTO_FOLLOWING_USERS", "").split(",")

issuecontroller = Blueprint("issuecontroller", __name__, url_prefix="/issue")

@issuecontroller.route('/<int:following_id>/can_reply')
def can_reply(following_id):
    follower = Follower.query.filter_by(FollowerID=following_id).first()
    resp = False
    if follower:
        may_reply = Follower.query.filter(and_(Follower.Type == follower.Type,
                                               Follower.ParentID == follower.ParentID,
                                               Follower.UserID != g.user.UserID)).count()
        resp = may_reply > 0

    return Response(json.dumps(resp), content_type='application/json')

@issuecontroller.route('/ignored/')
def get_ignored_issues():
    notes = []
    notifications = Notification.query.filter(Notification.UserID==g.user.UserID).all()
    for notification in notifications:
        if notification.Type == 'Comments':
            comment = Comment.query.filter(Comment.CommentID==notification.ParentID).first()
            if comment:
                note = notification.to_hash()
                note["comment"] = comment.to_hash()
                note["user"] = comment.user.to_hash()
                notes.append(note)
    return Response(json.dumps(notes), content_type="application/json")

@issuecontroller.route('/toggle/unsubscribe/<int:following_id>/', methods=['GET'])
def toggle_unsubscribe(following_id):
    follow = Follower.query.filter(Follower.FollowerID==following_id).first()
    if follow.UserID == g.user.UserID:
        follow.EmailSubscribed = not follow.EmailSubscribed
        follow.save()
    return "OK"

@issuecontroller.route("/",methods=["GET"])
def report_issue_forum():
    return render_template('/issue/edit.html',runninguser=json.dumps(g.user.to_hash()))

@issuecontroller.route("/",methods=["POST"])
def report_issue():
    data = json.loads(request.form['issue'])
    message = data['message']
    subject = data['title']
    subtitle = data['message']
    color = data['Color']
    sfdc_data = {}

    sfdc_data['assistanceRequest'] = data['assistanceRequest']
    sfdc_data['instrument'] = data['supportRequest']
    sfdc_data['elixysVersion'] = data['elixysVersion']

    num_images = int(request.form['numImages'])
    num_attachments = int(request.form['numAttachments'])


    forum, follow = generate_issue(g.user, subject, subtitle, message, num_images, num_attachments, color, sfdc_data)

    return Response(json.dumps({"ForumID" : forum.ForumID, "FollowerID": follow.FollowerID}), content_type='application/json')

def generate_issue(user, subject, subtitle, message, num_images, num_attachments, color, sfdc_data=None):
    forum = Forum(Subject=subject, AccountID=user.AccountID, UserID=user.UserID, Color=color, Subtitle=subtitle,Type='Issue')
    forum.save(sfdc_data)

    for image_id in xrange(num_images):
        img = request.files['image%s' % image_id]
        image = img.read()
        file_name = str(img.filename)
        comment = Comment(ParentID=forum.ForumID,Type='Forums',Message="",RenderType='image',UserID=user.UserID)
        comment.save()
        attachment = SequenceAttachment(Attachment=image,ParentID=comment.CommentID,Type='comments',FileName=file_name)
        attachment.save()

    for image_id in xrange(num_attachments):
        img = request.files['attachment%s' % image_id]
        image = img.read()
        file_name = str(img.filename)
        comment = Comment(ParentID=forum.ForumID,Type='Forums',Message="",RenderType='attachment',UserID=user.UserID)
        comment.save()
        attachment = SequenceAttachment(Attachment=image,ParentID=comment.CommentID,Type='comments',FileName=file_name)
        attachment.save()
        comment.Message = json.dumps({"url": "/comment/%s/attachment/%s" % (comment.CommentID, attachment.SequenceAttachmentID), "name": file_name})
        comment.save()

    print forum.ForumID

    team_members = user.account.users

    # Make all team members follow the issue
    for member in team_members:
        if user.UserID != member.UserID and str(member.UserID) not in SOFIE_AUTO_FOLLOWING_USER_IDS() and user.Active is True:
            team_follow = Follower(Type="Forums",ParentID=forum.ForumID,UserID=member.UserID,EmailSubscribed=False)
            team_follow.save()

    # Make the creator of the issue follow the case
    follow = Follower(Type="Forums",ParentID=forum.ForumID,UserID=user.UserID)
    follow.save()

    print follow.FollowerID

    sofie_users = User.query.filter(and_(User.UserID.in_(SOFIE_AUTO_FOLLOWING_USER_IDS()), User.Active==True))

    # Make all SOFIE members aware of the issue
    for sofie_user in sofie_users:
        sofie_userid = sofie_user.UserID
        if sofie_userid and user.UserID != sofie_userid:
            auto_follow = Follower(Type="Forums",ParentID=forum.ForumID,UserID=sofie_userid)
            auto_follow.save()

    Comment.make_comments(user.UserID, "Forums", forum.ForumID, message)

    return forum, follow

@issuecontroller.route("/close/<int:issue_id>",methods=["GET"])
def close_issue(issue_id):
    closed = do_close_issue(issue_id, g.user)
    if closed:
        return "OK"
    return Response("Cannot close", 401)

def testing():
    #temp function to update database 
    forums = Forum.query.all()
    sf = sfdc.get_instance()
    for forum in forums:
        try:
            case = sf.Case.get(str(forum.SFDC_ID))
            forum.ClosedDate = case['ClosedDate']
            forum.save()
            print "saving"
            print response
        except Exception as e:
            print "what??"
            err = str(e) + "\n Please reset your SFDC credentials"
            email_sender.auto_report_bug(err)

@issuecontroller.route("/delete/<int:issue_id>", methods=["GET"])
def delete_issue():
    #Delete o
    follower = Follower.query.filter(Follower.FollowerID==issue_id).first()
    if follower.Type == 'Forums':
        forum = Forum.query.filter(Forum.ForumID==follower.ParentID).first()
        running_users_role = g.user.role.Type
        if running_users_role == 'super-admin':
            forum.delete_salesforce_case()
            return True
    return False

def do_close_issue(issue_id, user):
    follower = Follower.query.filter(Follower.FollowerID==issue_id).first()
    if follower.Type == 'Forums':
        forum = Forum.query.filter(Forum.ForumID==follower.ParentID).first()
        can_close = user.AccountID == SOFIEBIO_ACCOUNTID

        if can_close:
            """
            followings = Follower.query.filter(and_(Follower.ParentID == forum.ForumID,
                                                    Follower.Type=='Forums')).all()
            for following in followings:
                if following.user.AccountID == SOFIEBIO_ACCOUNTID:
                    db.session.delete(following)
                elif forum.AccountID == following.user.AccountID and user.AccountID != forum.AccountID:
                    pass
                else:
                    db.session.delete(following)
            """
            msg = 'Closing Case'
            print msg
            comment = Comment(UserID=user.UserID, Message=msg, Type='Forums', ParentID=follower.ParentID)
            comment.save()
            forum.ReadOnly = True
            forum.close_salesforce_case()
            db.session.add(forum)
            db.session.commit()
            return True
    return False

@issuecontroller.route("/unfollow/<int:issue_id>",methods=["GET"])
def unfollow_issue(issue_id):
    follow = Follower.query.filter(Follower.FollowerID==issue_id).first()
    if follow.Type == 'Forums':
        forum = Forum.query.filter_by(ForumID=follow.ParentID).first()
        can_unfollow = forum.AccountID != SOFIEBIO_ACCOUNTID or g.user.AccountID == SOFIEBIO_ACCOUNTID
        owner = forum.AccountID == g.user.AccountID

        if owner:
            msg = 'Unfollowing case'
            comment = Comment(UserID=g.user.UserID ,Message=msg,Type='Forums',ParentID=forum.ForumID)
            comment.save()

        if can_unfollow:
            db.session.delete(follow)
            db.session.commit()
            return "OK"
    else:
        db.session.delete(follow)
        db.session.commit()
        return "OK"

    return Response("Cannot Unfollow", 401)

