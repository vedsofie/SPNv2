import os
import requests
import json
import random
import httpagentparser
import io
import base64
import csv
from Crypto.Cipher import AES

from flask import Blueprint, render_template, request, redirect, session, url_for, flash, g, Response
from sqlalchemy import and_
from models.role import Role, db
from models.sobject import ValidationException
from models.user import User, SOFIEBIO_ACCOUNTID
from models.account import Account
from models.forum import Forum
from models.notification import Notification
from models.sequence import Sequence
from models.molecule import Molecule
from models.follower import Follower
from models.comment import Comment
import os
from back import back

SFDC_PATH_URL = os.environ.get('SFDC_URL')

import email_sender
from sqlalchemy.sql.expression import join, select, table, column, alias
import json
import base64
from copy import deepcopy
from datetime import datetime, timedelta
usercontroller = Blueprint("usercontroller", __name__, template_folder="../templates")

#new github API call
GIT_OWNER = "SofieBiosciences"
GIT_REPO = "Elixys"
PYELIXYS_BASE_DIR = "https://api.github.com/repos/%s/%s/" % (GIT_OWNER, GIT_REPO)
INSTALLER_BASE_DIR = "https://api.github.com/repos/%s/%s/" % ('SofieBiosciences', 'SofieDeploymentInstaller')
#GIT_OATH = os.environ["GIT_TOKEN"]
GIT_OATH = '4e71be023c265b4bfb14af91d8e562ae5d8cfcd7'
ENCRYPTION_KEY = '1234567890123456'


@usercontroller.route('/')
def welcome():
    #return redirect("/account")
    return "hello"


@usercontroller.route('/user/login')
def authenticate():
    password_reset = "Thank You.\nPlease check your email for the reset link" if request.args.get('passwordReset', False) else ""
    redirect_url = request.path
    redirect_url = "" if redirect_url == "/user/login" or redirect_url == "/user/logout" else redirect_url
    acts = Account.query.all()
    data = [act.to_hash() for act in acts]
    if redirect_url:
        redirect_url += '?'
        redirect_url += '&'.join(cross_product_join(request.args.keys(), request.args.values(), '='))
    return render_template("index.html", redirect_url=redirect_url, sequence_data=json.dumps(data), password_reset=json.dumps(password_reset))

@usercontroller.route('/user/terms/')
def get_user_terms():
    resp = json.dumps(g.user.to_hash())
    return render_template("user/templates/terms.html", runninguser=resp)

def cross_product_join(a1, a2, join_by):
    pdt = []
    for i in xrange(0, min(len(a1), len(a2))):
        pdt.append(str(a1[i])+ join_by + str(a2[i]))
    return pdt

@usercontroller.route('/dashboard')
@back.anchor
def dashboard():
    back.set_back_url("/user/dashboard")
    runningUserAccount = Account.query.filter_by(id=g.user.AccountID).first()
    running_user = g.user.to_hash()
    running_user['RoleType'] = g.user.role.Type
    newest_sequences = Sequence.query.order_by(Sequence.CreationDate.desc()).limit(6).all()
    notification = request.args.get("notificationMessage", "")
    do_password_reset = True if 'password_reset' in request.args else False
    tab_to_load = None
    if 'issue' in request.args:
        tab_to_load = {"tab": "FieldService", "following": request.args['issue']}
    elif 'forum_id' in request.args:
        follower = Follower.query.filter(and_(Follower.UserID==g.user.UserID,
                                              Follower.ParentID==request.args['forum_id'],
                                              Follower.Type=='Forums')).first()
        if follower:
            tab_to_load = {"tab": "FieldService", "following": follower.FollowerID}
    elif 'tab' in request.args and 'following' in request.args:
        tab_to_load = {"tab": request.args['tab'], "following": request.args['following']}

    #it determines what page we need to go when the page is refreshed or something
    support = request.args.get('support')
    issue = request.args.get('issue')
    probes = request.args.get('myprobes')
    sequences = request.args.get('mysequences')
    if g.user.role.Type == 'super-admin' :
        is_super_admin = True
    else:
        is_super_admin = False
    url = PYELIXYS_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    resp = response.json()
    releases = json.dumps(as_assets(resp))
    userid = session["userid"]
    url = INSTALLER_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    resp = response.json()
    installers = json.dumps(as_assets(resp))
    if (support == "true") or issue != None: 
        #if support
        isSupport = True
        return render_template("dashboard.html",
                               runninguser=running_user,
                               runningUserAccount=json.dumps(runningUserAccount.to_hash()),
                               onLoadTab=json.dumps(tab_to_load),
                               reset_password=json.dumps(do_password_reset),
                               notification=json.dumps(notification),
                               support=json.dumps(isSupport), 
                               releases=releases, 
                               installers=installers,
                               probes=False,
                               sequences=False,
                               uid = userid,
                               new_seq = newest_sequences,
                               is_admin = is_admin
                               )
    else:                
        #if main dash board
        isSupport = False
        isProbes = False
        isSequences = False
        if probes == 'true':
            isProbes = True
        elif sequences == 'true':
            isSequences = True

        return render_template("dashboard.html",
                               runninguser=running_user,
                               runningUserAccount=json.dumps(runningUserAccount.to_hash()),
                               onLoadTab=json.dumps(tab_to_load),
                               reset_password=json.dumps(do_password_reset),
                               notification=json.dumps(notification),
                               support=json.dumps(isSupport),
                               releases=releases, 
                               installers=installers,
                               probes=isProbes,
                               sequences=isSequences,
                               uid = userid,
                               new_seq = newest_sequences,
                               is_super_admin = is_super_admin
                               )

@usercontroller.route('/user/<int:user_id>/role/')
def get_role(user_id):
    usr = User.query.filter_by(UserID=user_id).first()
    return usr.role.Type

#custom function to check for None type and return empty strings
def xstr(s):
    return '' if s is None else s

@usercontroller.route('/user/following/')
def follow():
    userid = session['userid']
    followings = Follower.query.filter_by(UserID=userid).all()
    sequence_ids = []
    molecule_ids = []
    account_ids = []
    forum_ids = []

    mapping = {"Sequences": sequence_ids, "Molecules": molecule_ids, "Forums": forum_ids}
    for following in followings:
        if following.Type in mapping:
            mapping[following.Type].append(following.ParentID)
        else:
            pass
    sequence_followings = {seq.SequenceID : seq for seq in Sequence.query.filter(Sequence.SequenceID.in_(sequence_ids)).all()} if len(sequence_ids) > 0 else {}
    owner_ids = [seq.UserID for seq in sequence_followings.values()]
    molecule_followings = {mol.ID: mol for mol in Molecule.query.filter(Molecule.ID.in_(molecule_ids)).all()} if len(molecule_ids) > 0 else {}
    forum_followings = {forum.ForumID : forum for forum in Forum.query.filter(Forum.ForumID.in_(forum_ids))} if len(forum_ids) > 0 else {}

    user_table = table('user', column('UserID'), column('AccountID'))
    account_table = table('Account', column('name'), column('id'))
    statement = user_table.join(account_table, user_table.c.AccountID==account_table.c.id)
    x = db.session.query(statement).filter(user_table.c.AccountID==account_table.c.id).all()
    account_name_by_userid = {res[0] : {"AccountName": res[2], "AccountID": res[1]} for res in x}
    forum_table = table('Forums', column('ForumID'), column('AccountID'), column('Color'), column('Subject'), column("Subtitle"), column("Type"), column("SFDC_ID"), column("UserID"), column("ReadOnly"), column("CreationDate"), column("CaseNumber"), column("ClosedDate"))
    account_table = table('Account', column('name'), column('id'))
    statement = forum_table.join(account_table, account_table.c.id==forum_table.c.AccountID)

    form_account_table = db.session.query(statement).filter(account_table.c.id==forum_table.c.AccountID).all()

    account_name_by_forumids = {form_account[0] : {"Subtitle": xstr(form_account[4]).encode('utf-8'), "Color": xstr(form_account[2]).encode('utf-8'), "Subject": xstr(form_account[3]).encode('utf-8'), "AccountID": form_account[1], "Type": form_account[5], "SFDC_ID": form_account[6], "UserID": form_account[7], "ReadOnly": form_account[8], "CreatedDate": form_account[9], "CaseNumber": form_account[10], "ClosedDate": form_account[11]} for form_account in form_account_table}
    responds = []

    for following in followings:
        resp = following.to_hash()
        if ["Sequences", "Molecules", "Forums"].__contains__(following.Type):
            if following.Type == "Sequences" and following.ParentID in sequence_followings:
                seq = sequence_followings[following.ParentID]
                resp["Title"] = seq.Name
                resp['Color'] = seq.molecule.Color
                resp['RedirectURL'] = '/sequence/%s/' % seq.SequenceID
                resp['ImageURL'] = "/probe/%s/image/" % seq.MoleculeID
                resp["OwnerID"] = seq.SequenceID
                resp['OwnerName'] = account_name_by_userid[seq.UserID]['AccountName']
                resp["SubTitle"] = seq.Comment if seq.Comment else ''
                account_id = account_name_by_userid[seq.UserID]['AccountID']
                resp['AccountID'] = account_id
                resp["OwnerAvatarURL"] = "/account/%s/logo/" % account_id
                resp['CanUnfollow'] = True
                resp['SubType'] = None
                responds.append(resp)
            elif following.Type == "Molecules" and following.ParentID in molecule_followings:
                molecule = molecule_followings[following.ParentID]
                resp["Title"] = molecule.DisplayFormat
                resp["Color"] = molecule.Color
                resp['RedirectURL'] = '/probe/%s/' % molecule.ID
                resp['ImageURL'] = "/probe/%s/image/" % molecule.ID
                resp["SubTitle"] = molecule.Description if molecule.Description else ""
                resp["OwnerID"] = molecule.ID
                resp["OwnerAvatarURL"] = "/account/undefined/logo/"
                resp['OwnerName'] = 'Sofie Biosciences, Inc.'
                resp['CanUnfollow'] = True
                resp['SubType'] = None
                responds.append(resp)
            elif following.Type == "Forums" and following.ParentID in forum_ids:
                if following.ParentID in account_name_by_forumids:
                    resp = {}
                    resp['Type'] = 'Forums'
                    resp['Title'] = account_name_by_forumids[following.ParentID]['Subject']
                    resp["OwnerID"] = following.ParentID
                    subtitle = account_name_by_forumids[following.ParentID]['Subtitle']
                    resp['SubTitle'] = subtitle if subtitle is not None and subtitle != "" and subtitle != 'None' else resp['Title']
                    resp['Color'] = account_name_by_forumids[following.ParentID]['Color']
                    account_id =  account_name_by_forumids[following.ParentID]['AccountID']
                    resp['AccountID'] = account_id
                    resp["OwnerAvatarURL"] = "/account/%s/logo/" % account_id
                    resp['OwnerName'] = 'Sofie Biosciences, Inc.'
                    resp['SubType'] = None

                    is_case = SOFIEBIO_ACCOUNTID != account_id
                    can_unfollow = account_name_by_forumids[following.ParentID]['Type'] == 'Issue'
                    resp['CanUnfollow'] = can_unfollow
                    resp["ReadOnly"] = account_name_by_forumids[following.ParentID]['ReadOnly']
                    if can_unfollow:
                        resp['CaseNumber'] = account_name_by_forumids[following.ParentID]['CaseNumber']
                        created_date = account_name_by_forumids[following.ParentID]['CreatedDate']
                        if created_date and not isinstance(created_date, unicode):
                            resp['CreatedDate'] = created_date.isoformat()
                        else:
                            resp['CreatedDate'] = created_date

                        closed_date = account_name_by_forumids[following.ParentID]['ClosedDate']
                        if closed_date and not isinstance(closed_date, unicode):
                            resp['ClosedDate'] = closed_date.isoformat()
                        else:
                            resp['ClosedDate'] = closed_date

                        act = Account.query.filter(Account.id==account_id).first()
                        resp['OwnerName'] = act.Name if act else ''
                        resp["CanClose"] = g.user.AccountID == SOFIEBIO_ACCOUNTID
                        resp['SubType'] = 'FieldService'
                        resp["OwnerAvatarURL"] = '/user/%s/avatar' % account_name_by_forumids[following.ParentID]['UserID']
                        resp['UnfollowDetails'] = {'ForumID': following.ParentID,
                                                   'unfollowTitle': "Unfollow",
                                                   "FollowingID": following.FollowerID,
                                                   "SubTitle": subtitle}
                        resp['EmailSubscribed'] = following.EmailSubscribed
                        if g.user.role.Type == 'super-admin':
                            resp['RedirectURL'] = '%s%s' % (SFDC_PATH_URL, account_name_by_forumids[following.ParentID]['SFDC_ID'])

                    resp['ImageURL'] = "/account/%s/logo/" % account_id
                    responds.append(resp)
            resp['FollowingID'] = following.FollowerID
            resp['hasNotifications'] = len(following.notifications) > 0

    return Response(json.dumps(responds), headers={"Content-Type": "application/json"})

def get_comment(parentID):
    comments_data = Comment.query.all()
    comments = []
    for comment in comments_data:
        temp = comment.to_hash()
        if temp['ParentID'] == parentID:
            comments.append(comment.to_hash())
    comments = sorted(comments, key=lambda x: x["CreationDate"], reverse=False)
    return comments

@usercontroller.route('/user/followingIssue/')
def getUserFollowingIssue():
    userid = session['userid']
    followings = Follower.query.filter_by(UserID=userid).all()

    sequence_ids = []
    molecule_ids = []
    account_ids = []
    forum_ids = []

    mapping = {"Sequences": sequence_ids, "Molecules": molecule_ids, "Forums": forum_ids}
    for following in followings:
        if following.Type in mapping:
            mapping[following.Type].append(following.ParentID)
        else:
            pass
    sequence_followings = {seq.SequenceID : seq for seq in Sequence.query.filter(Sequence.SequenceID.in_(sequence_ids)).all()} if len(sequence_ids) > 0 else {}
    owner_ids = [seq.UserID for seq in sequence_followings.values()]
    molecule_followings = {mol.ID: mol for mol in Molecule.query.filter(Molecule.ID.in_(molecule_ids)).all()} if len(molecule_ids) > 0 else {}
    forum_followings = {forum.ForumID : forum for forum in Forum.query.filter(Forum.ForumID.in_(forum_ids))} if len(forum_ids) > 0 else {}

    user_table = table('user', column('UserID'), column('AccountID'))
    account_table = table('Account', column('name'), column('id'))
    statement = user_table.join(account_table, user_table.c.AccountID==account_table.c.id)
    x = db.session.query(statement).filter(user_table.c.AccountID==account_table.c.id).all()
    account_name_by_userid = {res[0] : {"AccountName": res[2], "AccountID": res[1]} for res in x}
    forum_table = table('Forums', column('ForumID'), column('AccountID'), column('Color'), column('Subject'), column("Subtitle"), column("Type"), column("SFDC_ID"), column("UserID"), column("ReadOnly"), column("CreationDate"), column("CaseNumber"), column("ClosedDate"))
    account_table = table('Account', column('name'), column('id'))
    statement = forum_table.join(account_table, account_table.c.id==forum_table.c.AccountID)

    form_account_table = db.session.query(statement).filter(account_table.c.id==forum_table.c.AccountID).all()

    account_name_by_forumids = {form_account[0] : {"Subtitle": xstr(form_account[4]).encode('utf-8'), "Color": xstr(form_account[2]).encode('utf-8'), "Subject": xstr(form_account[3]).encode('utf-8'), "AccountID": form_account[1], "Type": form_account[5], "SFDC_ID": form_account[6], "UserID": form_account[7], "ReadOnly": form_account[8], "CreatedDate": form_account[9], "CaseNumber": form_account[10], "ClosedDate": form_account[11]} for form_account in form_account_table}
    openCase = []
    closeCase = []

    for following in followings:
        resp = following.to_hash()
        if ["Forums"].__contains__(following.Type):
            if following.Type == "Forums" and following.ParentID in forum_ids:
                if following.ParentID in account_name_by_forumids:
                    resp = {}
                    resp['Type'] = 'Forums'
                    resp['ForumID'] = following.ParentID
                    resp['Title'] = account_name_by_forumids[following.ParentID]['Subject']
                    resp["OwnerID"] = following.ParentID
                    subtitle = account_name_by_forumids[following.ParentID]['Subtitle']
                    resp['SubTitle'] = subtitle if subtitle is not None and subtitle != "" and subtitle != 'None' else resp['Title']
                    resp['Color'] = account_name_by_forumids[following.ParentID]['Color']
                    account_id =  account_name_by_forumids[following.ParentID]['AccountID']
                    resp['AccountID'] = account_id
                    resp["OwnerAvatarURL"] = "/account/%s/logo/" % account_id
                    resp['OwnerName'] = 'Sofie Biosciences, Inc.'
                    resp['SubType'] = None

                    is_case = SOFIEBIO_ACCOUNTID != account_id
                    can_unfollow = account_name_by_forumids[following.ParentID]['Type'] == 'Issue'
                    resp['CanUnfollow'] = can_unfollow
                    resp["ReadOnly"] = account_name_by_forumids[following.ParentID]['ReadOnly']
                    if can_unfollow:
                        resp['CaseNumber'] = account_name_by_forumids[following.ParentID]['CaseNumber']
                        created_date = account_name_by_forumids[following.ParentID]['CreatedDate']
                        if created_date and not isinstance(created_date, unicode):
                            resp['CreatedDate'] = created_date.isoformat()
                        else:
                            resp['CreatedDate'] = created_date

                        closed_date = account_name_by_forumids[following.ParentID]['ClosedDate']
                        if closed_date and not isinstance(closed_date, unicode):
                            resp['ClosedDate'] = closed_date.isoformat()
                        else:
                            resp['ClosedDate'] = closed_date

                        act = Account.query.filter(Account.id==account_id).first()
                        resp['OwnerName'] = act.Name if act else ''
                        resp["CanClose"] = g.user.AccountID == SOFIEBIO_ACCOUNTID
                        resp['SubType'] = 'FieldService'
                        resp["OwnerAvatarURL"] = '/user/%s/avatar' % account_name_by_forumids[following.ParentID]['UserID']
                        resp['UnfollowDetails'] = {'ForumID': following.ParentID,
                                                   'unfollowTitle': "Unfollow",
                                                   "FollowingID": following.FollowerID,
                                                   "SubTitle": subtitle}
                        resp['EmailSubscribed'] = following.EmailSubscribed
                        if g.user.role.Type == 'super-admin':
                    
                            resp['RedirectURL'] = '%s%s' % (SFDC_PATH_URL, account_name_by_forumids[following.ParentID]['SFDC_ID'])
                        comment_list = get_comment(resp['UnfollowDetails']['ForumID'])
                        for comment in comment_list:
                            comment['username'] = User.query.filter_by(UserID = comment['UserID']).first().username
                        resp['numComments'] = len(comment_list)
                        resp["comments"] = comment_list
                        resp['AccountName'] = Account.query.filter_by(id = account_id).first().name
                    resp['ImageURL'] = "/account/%s/logo/" % account_id
                    if resp['SubType'] == 'FieldService' and resp['ClosedDate'] == None:
                        openCase.append(resp)
                    elif resp['SubType'] == 'FieldService' and resp['ClosedDate'] != None:
                        closeCase.append(resp)
            resp['FollowingID'] = following.FollowerID
            resp['hasNotifications'] = len(following.notifications) > 0

    openCase = sorted(openCase, key=lambda x: x["CreatedDate"], reverse=False)
    closeCase = sorted(closeCase, key=lambda x: x["ClosedDate"], reverse=True)

    return openCase, closeCase

# ====== create a new user =========
@usercontroller.route('/user/new/')
def new():
    redirect_url = request.args["redirect_url"] if "redirect_url" in request.args else None
    redirect_url = "" if redirect_url == "/user/login" or redirect_url == "/user/logout" or redirect_url == "/user/new" else redirect_url
    user = User()
    if "account_id" in request.args:
        user.AccountID = int(request.args['account_id'])
        account = Account.query.filter_by(id = user.AccountID).first()

    if not user.can_save(g.user.to_hash()):
        return Response("You do not have the appropriate role type to update this record", 403)
    return render_template("user/new.html", redirect_url=redirect_url, user=user.to_hash(), account=account, runninguser=g.user.to_hash())

@usercontroller.route('/user/<int:user_id>/edit/')
def edit(user_id):
    redirect_url = request.args["redirect_url"] if "redirect_url" in request.args else None
    redirect_url = "" if redirect_url == "/user/login" or redirect_url == "/user/logout" or redirect_url == "/user/new" else redirect_url
    user = User.query.filter_by(UserID=user_id).first()

    terms_need_signing = user.TermsAndConditions is None
    if not user.can_save(g.user.to_hash()):
        return Response("You do not have the appropriate role type to update this record", 403)
    return render_template("user/edit.html", \
                           redirect_url=redirect_url, \
                           user=json.dumps(user.to_hash()), \
                           runninguser=json.dumps(g.user.to_hash()),\
                           terms_required=terms_need_signing)

@usercontroller.route("/user/<int:user_id>/account")
def users_account(user_id):
    user = User.query.filter_by(UserID=user_id).first()
    resp = json.dumps(user.account.to_hash())
    if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
        return resp
    else:
        return render_template('/account/detail.html', account=resp)

@usercontroller.route("/user/account/")
def my_account():
    user = User.query.filter_by(UserID=session['userid']).first()
    resp = json.dumps(user.account.to_hash())
    if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
        return resp
    else:
        return render_template('/account/new.html', account=resp)

@usercontroller.route("/user/me")
def running_user():
    if 'userid' in session:
        user = User.query.filter_by(UserID=session['userid']).first()
        role = user.role.Type if user.role else ""
        usr_dict = user.to_hash()
        usr_dict['Role'] = role
        resp = json.dumps(usr_dict)
        if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
            return Response(resp, headers={'content-type': 'application/json'})
        else:
            return render_template('/user/detail.html', user=resp)
    else:
        return ''

@usercontroller.route("/user/privacy_policy/")
def privacy_policy():
    return render_template('/user/privacy-policy.html', runninguser=json.dumps(g.user.to_hash()))

@usercontroller.route("/user/password_reset/<reset_url>", methods=["GET"])
def reset_for_user(reset_url):
    user_reset_path = User.query.filter_by(ResetCode=reset_url).first()
    if user_reset_path and (user_reset_path.ResetDate is None or user_reset_path.ResetDate + timedelta(hours=3) >= datetime.now()):
        session['userid'] = user_reset_path.UserID
        #user_reset_path.ResetCode = None
        #user_reset_path.save()
        return redirect('/user/%i/edit/' % user_reset_path.UserID)
    else:
        return redirect(url_for(".login"))

@usercontroller.route("/user/forgot_password", methods=["POST"])
def reset_password():
    data = request.form
    username = data['username']
    user_who_forgot = User.query.filter_by(username=username).first()
    if user_who_forgot:
        user_who_forgot.create_reset_url()
    return redirect("/user/login?passwordReset=True")

@usercontroller.route("/user/", methods=["GET"])
def get_users():
    users = User.query.all()
    resp = json.dumps([user.to_hash() for user in users])
    return render_template("user/users.html", users=resp)

@usercontroller.route('/user/logout/')
def logout():
    session.clear()
    return redirect( url_for('.login') )

@usercontroller.route('/user/sequences')
def my_sequences():
    sequences = Sequence.query.filter(Sequence.UserID==session['userid']).all()
    resp = json.dumps( [sequence.to_hash() for sequence in sequences] )
    return resp

@usercontroller.route("/user/undefined/avatar", methods=['GET'])
def get_default_logo():
    return get_user_logo(None)

@usercontroller.route("/user/null/avatar", methods=['GET'])
def get_autobot_avatar():
    return get_user_logo(None)

@usercontroller.route("/user/<int:user_id>/avatar", methods=["GET"])
def get_user_logo(user_id):
    if user_id:
        user = User.query.filter_by(UserID=user_id).first()
        if user.avatar is not None:
            return user.avatar
    default_image = open("static/img/default-user.png", "rb")
    return default_image.read()

@usercontroller.route('/user/<int:user_id>/')
def get_user(user_id):
    user = User.query.filter(User.UserID==user_id).first()
    resp = json.dumps(user.to_hash())
    if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
        return resp
    else:
        return render_template('/user/detail.html', user=resp)

@usercontroller.route('/user/<int:user_id>/sequences')
def sequences(user_id):
    sequences = Sequence.query.filter(Sequence.UserID==user_id).all()
    resp = json.dumps( [sequence.to_hash() for sequence in sequences] )
    return resp

@usercontroller.route('/user/login', methods=["POST"])
def login():
    is_api = request.headers['Accept'] == "application/json"
    redirect_url = request.args["redirect_url"] if "redirect_url" in request.args else None
    if is_api:
        data = request.json
    else:
        data = request.form
    username = str( data['username'] )
    password = str( data['password'] )
    usr = login(username, password)

    if is_api:
        if usr:
            return json.dumps("ok")
        else:
            res = Response('Failed to Authenticate', status=401)
            return res
    return redirect( url_for('.welcome') ) if not redirect_url else redirect(redirect_url)

def login(username, password):
    try:
        usr = User.authenticate( username, password )
        session['userid'] = usr.UserID
        session['username'] = usr.username
        return usr
    except Exception as e:
        flash( str(e) )

@usercontroller.route('/user/agreeToTerms/', methods=["GET"])
def agreeToTerms():
    usr = g.user
    usr.TermsAndConditions = datetime.now()
    usr.save()
    return "OK"

@usercontroller.route('/user/create/', methods=["POST"])
def create():
    data = request.form
    usr = User()
    data = data.to_dict()
    for key, value in data.iteritems():
        if value:
            setattr(usr, key, value)
    usr.generate_password()
    
    if usr.save():
        flash('User created successfully')
        return redirect(url_for('accountcontroller.get_account', account_id=usr.AccountID))
    else:
        return redirect(url_for('.new', account_id = usr.AccountID))

def do_create(data, running_user):
    if "ResetDate" in data:
        del data['ResetDate']

    if 'password' in data and running_user.UserID != data['UserID']:
        del data['password']

    running_user_role = running_user.role.Name
    running_user = running_user.to_hash()

    if "UserID" in data and data['UserID']:
        usr = User.query.filter_by(UserID=data['UserID']).first()
        if 'AccountID' in data and running_user_role != 'super-admin':
            del data['AccountID']
        usr.merge_fields(**data)
    else:
        usr = User()
        if 'AccountID' in data and running_user_role != 'super-admin':
            data['AccountID'] = running_user['AccountID']
        usr.merge_fields(**data)
        usr.generate_password()
        usr.validate_required_fields()

    if usr.can_save(running_user):
        usr.save()
    else:
        return False

    uid = usr.UserID
    user = User.query.filter_by(UserID=uid).first()
    return user

def as_assets(resp):
    spn_domain = os.environ['SOFIE_PROBE_DOMAIN']
    assets = []

    for release in resp:
        if not release['prerelease']:
            rel = {}
            tag_name = release['tag_name']
            rel['name'] = tag_name
            rel["versions"] = []
            rel['assets_url'] = release['assets_url']
            rel['published_at'] = release['published_at'].split('T')[0]
            rel['body'] = release['body']
            index = 0
            while index < len(release['assets']):
                if 'linux_pyelixys_' in release['assets'][index]['name']:
                    rel['size'] = round(release['assets'][index]['size'] * 0.000001, 2)
                index += 1
            assets_url = rel['assets_url']
            for asset in release['assets']:
                asset_name = asset['name']
                op_os = asset_name.split('_')
                rel["versions"].append({'name': asset_name, 'url': asset['url'], 'os': op_os[0]})
            assets.append(rel)
    return assets
def git_headers():
    token = GIT_OATH
    return {
        "Authorization": "token %s " % token
    }

