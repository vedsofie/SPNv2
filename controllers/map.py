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
import os
from back import back
SFDC_PATH_URL = os.environ.get('SFDC_URL')

import email_sender
from sqlalchemy.sql.expression import join, select, table, column, alias
import json
import base64
from copy import deepcopy
from datetime import datetime, timedelta

mapcontroller = Blueprint("mapcontroller", __name__, template_folder="../templates", url_prefix="/map")

@mapcontroller.route('/search/')
def getMapSearch():
	print db
	print "getmapsearch"
	return render_template("map.html")