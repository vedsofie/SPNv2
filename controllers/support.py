import os
import requests
import json
import random
import httpagentparser
import io
import base64
import csv
from Crypto.Cipher import AES
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
from controllers.user import getUserFollowingIssue
import models.model_helpers as model_helpers
import base64,zipfile,io,os
import modules
from sqlalchemy import or_, and_
import email_sender

#new github API call
GIT_OWNER = "SofieBiosciences"
GIT_REPO = "Elixys"
PYELIXYS_BASE_DIR = "https://api.github.com/repos/%s/%s/" % (GIT_OWNER, GIT_REPO)
INSTALLER_BASE_DIR = "https://api.github.com/repos/%s/%s/" % ('SofieBiosciences', 'SofieDeploymentInstaller')
#GIT_OATH = os.environ["GIT_TOKEN"]
GIT_OATH = '4e71be023c265b4bfb14af91d8e562ae5d8cfcd7'
ENCRYPTION_KEY = '1234567890123456'

db = modules.database.get_db()

def SOFIE_AUTO_FOLLOWING_USER_IDS():
    return os.getenv("SOFIE_AUTO_FOLLOWING_USERS", "").split(",")

supportcontroller = Blueprint("supportcontroller", __name__, url_prefix="/support")

@supportcontroller.route("/",methods=["GET"])
def report_issue_forum():
    url = PYELIXYS_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    resp = response.json()
    releases = json.dumps(as_assets(resp))

    url = INSTALLER_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    print response
    resp = response.json()
    installers = json.dumps(as_assets(resp))
    userid = session["userid"]
    return render_template('/support/support_dashboard.html', releases=releases, uid = userid, installers=installers, runninguser=json.dumps(g.user.to_hash()))

@supportcontroller.route("/documentation",methods=["GET"])
def documentation():
    userid = session["userid"]
    return render_template("/support/documentation.html", uid = userid, runninguser=json.dumps(g.user.to_hash()))

@supportcontroller.route("/faq",methods=["GET"])
def faq():
    userid = session["userid"]
    return render_template("/support/faq.html", uid = userid, runninguser=json.dumps(g.user.to_hash()))


@supportcontroller.route("/software",methods=["GET"])
def software():
    userid = session["userid"]
    url = PYELIXYS_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    resp = response.json()
    releases = as_assets(resp)
    new_release = releases[0]
    releases.pop(0)
    old_release = []
    for release in range(2):
        old_release.append(releases[release])

    return render_template("/support/software.html", new_release=new_release, old_release=old_release, uid = userid, runninguser=json.dumps(g.user.to_hash()))

@supportcontroller.route("/field_support",methods=["GET"])
def field_support():
    userid = session["userid"]
    openCase, closedCase = getUserFollowingIssue()
    return render_template("/support/field_support.html", openCase=openCase, closedCase=closedCase, uid = userid, runninguser=json.dumps(g.user.to_hash()))

def as_assets(resp):
    spn_domain = os.environ['SOFIE_PROBE_DOMAIN']
    assets = []

    for release in resp:
        if not release['prerelease'] or spn_domain != 'sofienetwork.com':
            rel = {}
            tag_name = release['tag_name']
            rel['name'] = tag_name
            rel["versions"] = []
            rel['assets_url'] = release['assets_url']
            dateSplit = release['published_at'].split('T')[0].split('-')
            rel['published_at'] = dateSplit[1] + "/" + dateSplit[2] + "/" + dateSplit[0]
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