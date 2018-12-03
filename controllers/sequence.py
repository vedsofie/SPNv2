import json
from flask import Blueprint, render_template, request, redirect, session, url_for, flash, Response, g, make_response
from models.sequence import Sequence
from models.user import User
from models.uniquesequencedownload import UniqueSequenceDownload
from models.comment import Comment
from models.component import Component
from models.statuslog import StatusLog
from models.molecule import Molecule
from models.follower import Follower
from models.keyword import Keyword
from models.account import Account
from models.model_helpers import SequenceImportException
from models.sobject import ValidationException, NoPermissionException
from models.sequenceattachment import SequenceAttachment
from back import back
import email_sender
import urllib
import models.model_helpers as model_helpers
import base64,zipfile,io,os
import modules
import datetime
from sqlalchemy import or_, and_, func
from sqlalchemy.sql.expression import alias
SOFIEBIO_USER = int(os.getenv("SOFIEBIO_USERID", 0))
db = modules.database.get_db()

sequencecontroller = Blueprint("sequencecontroller", __name__, template_folder="../templates/sequence")

@sequencecontroller.route("/sequence/<int:sequence_id>/", methods=["DELETE"])
def delete_sequence(sequence_id):
    seq = Sequence.query.filter_by(SequenceID=sequence_id).first()
    if g.user:
        can_delete = g.user.UserID == seq.SequenceID
        if not can_delete:
            owner = seq.owner
            running_user_type = g.user.role.Type
            can_delete = (g.user.AccountID == owner.AccountID and running_user_type== 'admin') or running_user_type == 'super-admin'

        if can_delete:
            seq.delete()
            return "Deleted"

    return "You do not have permission"

@sequencecontroller.route("/sequence/<int:sequence_id>/components", methods=["DELETE"])
def delete_sequence_components(sequence_id):
    seq = Sequence.query.filter_by(SequenceID=sequence_id).first()
    try:
        seq.can_save(g.user)
        seq.delete_sequence_file()
        return Response("OK")
    except NoPermissionException:
        return Response("No Permission", 403)

@sequencecontroller.route("/sequence/<int:sequence_id>/probe", methods=["GET"])
def get_probe(sequence_id):
    sequence = Sequence.query.filter(Sequence.SequenceID==sequence_id).first()
    resp = json.dumps(sequence.molecule.to_hash())
    return Response(resp, content_type="application/json")
    
@sequencecontroller.route("/sequence/new/", methods=["GET"])
def create_sequence():
    seq = Sequence()
    resp = json.dumps(seq.to_hash())
    return render_template("/sequence/edit.html",
                           sequence=resp,
                           runninguser=json.dumps(g.user.to_hash()))

@sequencecontroller.route("/sequence/module/list/", methods=["GET"])
def list_module_options():
    f = open('sequence_modules.txt')
    options = f.read()
    options = options.split('\n')
    f.close()
    return Response(json.dumps(options), content_type='application/json')

@sequencecontroller.route("/sequence/<int:sequence_id>/", methods=["GET"])
def get_details(sequence_id):
    edit_screen = request.args.get('edit', False)
    sequence = Sequence.query.filter(Sequence.SequenceID==sequence_id).first()
    if not sequence:
        message = urllib.quote("The sequence does not exist")
        return redirect('/user/dashboard?notificationMessage=%s' % message)

    resp = sequence.to_hash()
    running_user = g.user.to_hash()
    showNotification = request.args.get("showThankyou", False)
    showNotification = showNotification and not sequence.molecule.Approved
    components = sequence.components

    r_scheme = SequenceAttachment.query.filter(and_(SequenceAttachment.SequenceID==sequence_id, SequenceAttachment.Type=='ReactionScheme')).first()
    if r_scheme:
        reaction_scheme = Response(r_scheme.Attachment)
    else:
        reaction_scheme = r_scheme
    reagents_hash = []
    follower = Follower.query.filter(and_(Follower.ParentID == sequence_id, Follower.UserID == running_user['UserID'], Follower.Type == 'Sequences')).first()
    # get comments for this probe
    all_comments = []
    comments = Comment.query.filter(and_(Comment.ParentID == sequence_id,Comment.Type == 'Sequences')).order_by(Comment.CreationDate.asc()).all()
    for comment in comments:
        users_name = User.query.filter_by(UserID=comment.UserID).first()
        comments_aggr = comment.to_hash()
        comments_aggr['CreationDate'] = datetime.datetime.fromtimestamp(int(comments_aggr['CreationDate'] / 1000)).strftime('%m / %d / %Y')
        comments_aggr['username'] = users_name.username
        all_comments.append(comments_aggr)
    # Check if logged in user is following this probe
    for component in components:
        reagents = component.reagents
        for reagent in reagents:
            if reagent.Name:
                reagents_hash.append(reagent.Name)
    if request.headers.get("accept", "") == "application/json":
        return Response(resp, content_type='application/json')

    if edit_screen and sequence.can_save(g.user):
        return render_template("/sequence/edit.html",
                               sequence=resp,
                               runninguser=running_user)
    else:
        return render_template("/sequence/detail.html",
                               sequence=resp,
                               reagents = reagents_hash,
                               running_user=running_user,
                               runninguser=running_user,
                               follower = follower,
                               comments = all_comments,
                               reaction_scheme = reaction_scheme,
                               back=back,
                               showNotification=showNotification)

@sequencecontroller.route("/sequence/<int:sequence_id>/reagents", methods=["GET"])
def get_reagents(sequence_id):
    sequence = Sequence.query.filter(Sequence.SequenceID==sequence_id).first()
    reagents = sequence.reagents
    resp = [reagent.to_hash() for reagent in reagents]
    return Response(json.dumps(resp), headers={"Content-Type": "application/json"})


@sequencecontroller.route("/sequence/<int:sequence_id>/run_details", methods=["GET"])
def get_runs(sequence_id):
    sequences = StatusLog.query.filter(StatusLog.SequenceID==sequence_id).all()
    resp = json.dumps([sequence.to_hash() for sequence in sequences])
    return resp

@sequencecontroller.route("/sequence/<int:sequence_id>/revisions", methods=["GET"])
def revisions(sequence_id):
    sequences = Sequence.query.filter(Sequence.parentSequenceID==sequence_id).all()
    resp = json.dumps([sequence.to_hash() for sequence in sequences])
    return resp

@sequencecontroller.route("/sequence/most_new", methods=["GET"])
def get_newest_sequences():
    newest_sequences = Sequence.query.order_by(Sequence.CreationDate.desc()).limit(3).all()
    resp = [seq.to_hash() for seq in newest_sequences]
    return Response(json.dumps(resp), headers={"Content-Type": "application/json"})

@sequencecontroller.route("/sequence/most_popular", methods=["GET"])
def get_popular_sequences():
    most_downloaded = db.session.query(UniqueSequenceDownload.SequenceID, func.count(UniqueSequenceDownload.UserID)).group_by(UniqueSequenceDownload.SequenceID).order_by(func.count(UniqueSequenceDownload.UserID).desc()).limit(3).all()
    seq_data = {count[0]: {'numdownloads': count[1]} for count in most_downloaded}
    seqs = Sequence.query.filter(Sequence.SequenceID.in_(seq_data.keys())).all()
    resp = []
    for seq in seqs:
        seq_count = seq_data[seq.SequenceID]
        seq_count['obj'] = seq.to_hash()
        resp.append(seq_count)
    resp = sorted(resp, reverse=True, key=lambda seq: seq['numdownloads'])
    return Response(json.dumps(resp), headers={"Content-Type" : "application/json"})

@sequencecontroller.route("/sequence/<int:sequence_id>/export/", methods=["GET"])
def export(sequence_id):
    sequence = Sequence.query.filter_by(SequenceID=sequence_id).first()
    zipped_sequence = sequence.export()
    userid = session['userid']
    already_downloaded = UniqueSequenceDownload.query.filter(and_(UniqueSequenceDownload.UserID==userid,
                                                                  UniqueSequenceDownload.SequenceID==sequence_id)).first()
    if not already_downloaded:
        new_download = UniqueSequenceDownload(UserID=userid, SequenceID=sequence_id)
        new_download.save()
        #mimetype='application/zip',
    resp = Response(zipped_sequence[1], headers={'Content-Disposition':'attachment;filename=%s' % (zipped_sequence[0]) })
    return resp


@sequencecontroller.route("/sequence/import", methods=["GET"])
def go_import():
    return render_template("import.html")

@sequencecontroller.route("/sequence/<int:sequence_id>/check_following/", methods=["GET"])
def check_following(sequence_id):
    follower = Follower.query.filter(and_(Follower.ParentID == sequence_id,
                                     Follower.Type == 'Sequences',
                                     Follower.UserID == session['userid'])).first()
    return json.dumps(follower is not None)

@sequencecontroller.route("/sequence/<int:sequence_id>/follow/", methods=['POST'])
def follow(sequence_id):
    userid = session['userid']
    follower = Follower.query.filter(and_(Follower.ParentID == sequence_id,
                                          Follower.UserID == userid,
                                          Follower.Type == 'Sequences')).first()
    if not follower:
        follower = Follower(Type='Sequences', ParentID=sequence_id, UserID=userid)
        follower.save()

    return "OK"

@sequencecontroller.route("/sequence/<int:sequence_id>/account/", methods=["GET"])
def sequence_account(sequence_id):
    seq = Sequence.query.filter_by(SequenceID=sequence_id).first()
    seq_owner = seq.UserID
    account = Account.query.join(User.account).filter(User.UserID==seq_owner).first()
    resp = json.dumps(account.to_hash())
    return Response(resp, headers={"Content-Type": "application/json"})


@sequencecontroller.route("/sequence/<int:sequence_id>/unfollow/", methods=["DELETE"])
def unfollow(sequence_id):
    userid = session['userid']
    follower = Follower.query.filter(and_(Follower.ParentID == sequence_id, Follower.UserID == userid, Follower.Type=='Sequences')).first()
    if follower:
        db.session.delete(follower)
        db.session.commit()

    return "OK"

@sequencecontroller.route("/sequence/search/", methods=["GET"])
def search():
    txt = request.args['text']
    comments = Keyword.query.filter(and_(Keyword.Keyword.like('%' + txt + "%"), Keyword.Type == 'Sequence')).all()
    sequence_ids = [comment.ParentID for comment in comments]
    sequences = Sequence.query.filter(or_(Sequence.Name.like("%" + txt + "%"), Sequence.SequenceID.in_(sequence_ids))).all()
    resp = json.dumps([sequence.to_hash() for sequence in sequences])
    return Response(resp, headers={"content-type": "application/json"})

@sequencecontroller.route("/sequence/<int:sequence_id>/contact", methods=["POST"])
def contact(sequence_id):
    data = request.get_json()
    message = data['message']
    name = data['name']
    email = data['email']
    sequence = Sequence.query.filter_by(SequenceID=sequence_id).first()
    email_sender.contact_probe_owner(name, email, sequence, message)
    return "OK"


@sequencecontroller.route("/sequence/<int:sequence_id>/update/", methods=["POST"])
def update_sequence(sequence_id):
    try:
        sequence_data = request.json['sequence']
        sequence_data = base64.b64decode(sequence_data)
        update_sequence_file(sequence_id, sequence_data)
    except NoPermissionException:
        return Response("You do not have permission to edit this sequence", 403)
    except Exception as e:
        return Response("Your sequence file is corrupted", 403)
    return "OK"

def update_sequence_file(sequence_id, sequence_data):
    sequence = Sequence.query.filter_by(SequenceID=sequence_id).first()
    if sequence:
        session = db.session
        try:
            seq_components = Component.query.filter_by(SequenceID=sequence_id).all()
            for comp in seq_components:
                session.delete(comp)
            for reg in sequence.reagents:
                session.delete(reg)
            model_helpers.update_components(sequence_id,sequence_data)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    return sequence

class NoPermissionException(Exception):
    pass

@sequencecontroller.route("/sequence/create", methods=["POST"])
def edit_sequence():
    data = request.json
    try:
        if "SequenceID" in data:
            seq = Sequence.query.filter_by(SequenceID=data['SequenceID']).first()
            seq.can_save(g.user)
            if "CreationDate" in data:
                del data['CreationDate']
            seq.merge_fields(**data)
            is_new = False
        else:
            is_new = True
            seq = Sequence()
            seq.merge_fields(**data)
            seq.UserID = g.user.UserID
            seq.validate_required_fields()

        if seq.can_save(g.user):
            seq.save()

    except NoPermissionException:
        return Response({"error_details": "No Permissions Error"}, status=400, content_type="application/json")
    except Exception as e:
        db.session.rollback()
        msg = str(e)
        if e.__class__ == ValidationException().__class__:
            msg = e.errors()

        email_sender.auto_report_bug(msg, g.user.username)
        if request.headers.get("Accept") == "application/json":
            return Response(json.dumps({"error_details": msg}), status=400, headers={"Content-Type": "application/json"})
        return "not implemented.  Saving Failed %s" % msg

    uid = seq.SequenceID
    sequence_saved_trigger(is_new, seq)
    seq = Sequence.query.filter_by(SequenceID=uid).first()

    if request.headers.get("Accept") == "application/json":
        return Response(json.dumps(seq.to_hash()), headers={"Content-Type": "application/json"})

    return redirect("/")

def sequence_saved_trigger(is_new, seq):
    if is_new:
        if seq.molecule.Approved:
            message = "We make <a href='%s'>%s</a> %s" % (seq.details_url, seq.molecule.Name, "contact us for more information" if not seq.downloadable else "feel free to use it on your Elixys")
            comment = Comment(UserID=g.user.UserID, Type='Molecules',ParentID=seq.MoleculeID, Message=message, RenderType='html')
            comment.save()
        else:
            message = "%s is being approved by Sofie Biosciences, we will get back to you after it has been reviewed" % seq.molecule.Name
            comment = Comment(UserID=SOFIEBIO_USER, Type='Molecules',ParentID=seq.MoleculeID, Message=message, RenderType='text')
            comment.save()

@sequencecontroller.route('/sequence/<int:sequence_id>/reaction_scheme', methods=['DELETE'])
def delete_reaction_scheme(sequence_id):
    scheme = SequenceAttachment.query.filter(and_(SequenceAttachment.SequenceID==sequence_id,
                                                  SequenceAttachment.Type=='ReactionScheme')
                                             ).first()
    db.session.delete(scheme)
    db.session.commit()
    return "OK"

@sequencecontroller.route('/sequence/<int:sequence_id>/reaction_scheme', methods=['GET'])
def view_reaction_scheme(sequence_id):
    scheme = SequenceAttachment.query.filter(and_(SequenceAttachment.SequenceID==sequence_id,
                                                  SequenceAttachment.Type=='ReactionScheme')
                                             ).first()
    resp = Response(scheme.Attachment)
    resp.headers['Content-Disposition'] = "attachment; filename="+ '"' +scheme.FileName+'"'
    resp.headers['Content-Type'] = scheme.ContentType
    #resp = Response(scheme.Attachment, headers={'Content-Disposition':'attachment;filename=%s' % (scheme.FileName) })
    return resp

@sequencecontroller.route("/sequence/import", methods=["POST"])
def do_import():
    data = json.loads(request.form['SequenceMeta'])
    sequence_data = None
    if 'sequence' in request.files:
        sequence_data = request.files['sequence'].read()

    reaction_scheme = None
    if 'reactionScheme' in request.files:
        reaction_scheme = request.files['reactionScheme']

    try:
        if "SequenceID" in data:
            seq = Sequence.query.filter_by(SequenceID=data['SequenceID']).first()
            if seq.can_save(g.user):
                if sequence_data:
                    seq = update_sequence_file(data['SequenceID'], sequence_data)
                else:
                    seq = Sequence.query.filter(Sequence.SequenceID==data['SequenceID']).first()

                if "CreationDate" in data:
                    del data["CreationDate"]
                seq.merge_fields(**data)
                seq.validate_required_fields()
                seq.save()
                is_new = False
        else:
            if sequence_data:
                resp = model_helpers.do_import(sequence_data, session['userid'], data)
            else:
                seq = Sequence()
                seq.merge_fields(**data)
                seq.UserID = g.user.UserID
                seq.validate_required_fields()
                seq.save()
                resp = seq.SequenceID

            seq = Sequence.query.filter_by(SequenceID=resp).first()
            is_new = True

        print seq.SequenceID

        if(reaction_scheme):
            scheme = SequenceAttachment(SequenceID=seq.SequenceID,
                                        Attachment=reaction_scheme.read(),
                                        Type='ReactionScheme',
                                        FileName=reaction_scheme.filename,
                                        ContentType=reaction_scheme.content_type)
            scheme.save()

    except NoPermissionException:
        return Response({"error_details": "No Permissions Error"}, status=400, content_type="application/json")
    except Exception as e:
        db.session.rollback()
        msg = str(e)
        if e.__class__ == ValidationException().__class__:
            msg = e.errors()
        elif e.__class__ == SequenceImportException().__class__:
            msg = str(e)

        email_sender.auto_report_bug(msg, g.user.username)
        if request.headers.get("Accept") == "application/json":
            return Response(json.dumps({"error_details": msg}), status=400, headers={"Content-Type": "application/json"})
        return Response(msg, status=400)

    uid = seq.SequenceID
    print seq.SequenceID
    sequence_saved_trigger(is_new, seq)
    seq = Sequence.query.filter_by(SequenceID=uid).first()
    return Response(json.dumps(seq.to_hash()), headers={"Content-Type": "application/json"})
