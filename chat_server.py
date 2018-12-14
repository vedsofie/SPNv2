import os
from flask import Flask, redirect, url_for, session, request, g, Response, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.triangle import Triangle
import modules.database
import json
import email_sender
import traceback
from flask_sslify import SSLify
class MyFlask(Flask):
    def get_send_file_max_age(self, name):
        return 0
app = MyFlask(__name__)
sslify = SSLify(app)
Triangle( app )
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.secret_key = os.environ['SESSION_KEY']
db = modules.database.generate_db(app)
from models.user import User
from models.account import Account
from models.sequence import Sequence
from models.labsystem import  LabSystem
from models.molecule import Molecule
from flask.ext.assets import Environment, Bundle

import controllers
import re

@app.before_request
def do_authenticate():
    """
    if request.url.startswith('http://') and not request.url.startswith("http://localhost:8080/"):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    """
    g.user = None
    userid = session["userid"] if "userid" in session else None
    username = request.headers.get("USERNAME", None)
    password = request.headers.get("PASSWORD", None)

    if username:
        running_user = User.authenticate(username, password)
        g.user = running_user
    if userid:
        running_user = User.query.filter_by(UserID=userid).first()
        g.user = running_user
        session['userid'] = running_user.UserID
    elif request and request.authorization and 'username' in request.authorization and 'password' in request.authorization:
        auth = request.authorization
        if auth:
            try:
                running_user = User.authenticate(auth['username'], auth['password'])
                g.user = running_user
            except:
                return Response(json.dumps({"message": "Invalid username or password"}), content_type="application/json", status=404)

    if g.user:
        user_edit_url = '/user/' + str(g.user.UserID) + '/edit/'
        if g.user.TermsAndConditions is None and request.path != user_edit_url \
           and not request.path.startswith('/static') \
           and request.path != '/user/logout/' \
           and request.path != '/user/privacy_policy/' \
           and request.path != '/user/%s/avatar' % g.user.UserID \
           and request.path != url_for('usercontroller.login') \
           and request.path != url_for('usercontroller.agreeToTerms'):
            return redirect(user_edit_url)
        if g.user.role is None or str(g.user.role.Type) != 'super-admin':
            if request.path.startswith('/admin'):
                return controllers.user.dashboard()

    else: # only allow public pages to be excluded from the redirect
        if request.path == url_for('usercontroller.login') or \
            request.path == url_for('usercontroller.reset_password') or \
            re.match('[/]user[/]password_reset[/][A-Za-z0-9]*', request.path) is not None or\
            request.path == url_for('moleculecontroller.find') or \
            request.path == url_for('account_sequences') or \
            re.match('[/]account[/][0-9,]*[/]contact', request.path) is not None or\
            request.path.startswith("/static") or \
            request.path.startswith("/login") or \
            request.path.startswith("/forgot_password") or \
            request.path.startswith("/find_a_probe") or \
            request.path == url_for("account_sequences") or \
            request.path == url_for("featured_sequences") or \
            request.path == url_for("usercontroller.running_user") or \
            re.match('[/]account[/][0-9,]*[/]probes', request.path) is not None or \
            re.match('[/]probe[/][0-9,]*[/]image', request.path) is not None or \
            request.path.startswith("/github/latests_exe") or \
            request.path.startswith("/github/latests_installer_exe") or \
            request.path.startswith('/probe/hint/') or \
            request.path == url_for('mapcontroller.getMapSearch') or \
            request.path == url_for('accountcontroller.all_probes_for_account') :
                return
        else:
            return controllers.user.authenticate()

@app.route('/account_location_molecules', methods=["POST"])
def account_sequences():
    x = request.json

    if 'MoleculeIDs' in x:
        moleculeids = x['MoleculeIDs']
        sequences = Sequence.query.filter(Sequence.MoleculeID.in_(moleculeids)).all()
        users = set()
        acts = set()
        [users.add(seq.UserID) for seq in sequences]
        users = User.query.filter(User.UserID.in_(users)).all()
        [acts.add(usr.AccountID) for usr in users]
        labsystems = Account.query.filter(Account.id.in_(acts))
        resp = [system.to_hash() for system in labsystems]
        return Response(json.dumps(resp), content_type='application/json')
    return Response("No", 403)


# Links for public facing pages out here
@app.route('/featured_sequences')
def featured_sequences():
  seqs = Sequence.query.all()
  resp = [seq.to_hash() for seq in seqs]
  return Response(json.dumps(resp), content_type="application/json")

@app.route('/')
def welcome():
    return redirect(url_for("usercontroller.dashboard"))

@app.route('/login')
def login():
    return render_template("user/login.html")

@app.route('/find_a_probe')
def find_a_probe():
    accounts = Account.query.all()
    data = [act.to_hash() for act in accounts]
    probe_data = []

    for account in accounts:
        molecule_ids = []
        molecule_ids = set([sequence.MoleculeID for sequence in account.sequences])
        molecules = Molecule.query.filter(Molecule.ID.in_(molecule_ids)).all()
        for molecule in molecules:
            if molecule.Approved:
                x = molecule.to_hash()
                y = {"Name": x["Name"],"searchName": getName(x["Name"]), "AccountID": account.id, "AccountName": account.name, "number" : 0, "url": '/probe/'+str(molecule.ID)+'/image/'}
                probe_data.append(y)

    #sort the probe list for displaying
    probe_data = sorted(probe_data, key=lambda k: k['searchName']) 
    probe_data = json.dumps(probe_data)

    return render_template("find_a_probe.html", sequence_data=json.dumps(data), probe_data = probe_data)
    
def getName(name) :
    return name.split("]")[1].rstrip()

@app.route('/forgot_password')
def forgot_password():
    return render_template("user/forgot_password.html")

@app.errorhandler(500)
def server_error(err):
    try:
        tb = traceback.format_exc()
        err = tb + '\n' + str(err)
    except:
        pass

    print 'Error %s' % err
    if g.user:
        email_sender.auto_report_bug(err, g.user.username)
        return render_template('unexpected_error.html', runninguser=json.dumps(g.user.to_hash()))
    else:
        email_sender.auto_report_bug(tb + '\n' + str(err), 'Portal Guest')
        return redirect('/user/login')

with app.app_context():
    from controllers.user import usercontroller
    from controllers.account import accountcontroller
    from controllers.sequence import sequencecontroller
    from controllers.comment import commentcontroller
    from controllers.molecule import moleculecontroller
    from controllers.admin import admincontroller
    from controllers.notification import notificationcontroller
    from controllers.keyword import keywordcontroller
    from github.githubapi import github
    from controllers.issue import issuecontroller
    from controllers.products import productscontroller
    from controllers.map import mapcontroller
    from controllers.support import supportcontroller



    app.register_blueprint(usercontroller)
    app.register_blueprint(accountcontroller)
    app.register_blueprint(sequencecontroller)
    app.register_blueprint(commentcontroller)
    app.register_blueprint(moleculecontroller)
    app.register_blueprint(admincontroller)
    app.register_blueprint(notificationcontroller)
    app.register_blueprint(keywordcontroller)
    app.register_blueprint(issuecontroller)
    app.register_blueprint(github)
    app.register_blueprint(productscontroller)
    app.register_blueprint(mapcontroller)
    app.register_blueprint(supportcontroller)

    assets = Environment(app)
#     js = Bundle(
# 'js/libs/jquery.min.js',
# 'js/libs/bootstrap.min.js',
# 'js/libs/bootstrap-datetimepicker-4.17.37/build/js/moment-with-locales.min.js',
# 'js/libs/knockout-debug.js',

# 'js/libs/bootstrap-datetimepicker-4.17.37/build/js/bootstrap-datetimepicker.min.js',
# 'js/libs/simplePagination.js-master/jquery.simplePagination.js',
# 'js/libs/validate.min.js',
# 'js/admin/column.js',
# 'js/admin/record.js',
# 'js/admin/table.js',

# 'js/visual_components/popupbox.js',
# 'js/commentsCtrl.js',

# 'js/account/account.js',
# 'js/account/account_detail.js',
# 'js/account/account_detail_popup.js',
# 'js/account/contact_us_about.js',
# 'js/account/components.js',


# 'js/sequence/sequence.js',
# 'js/sequence/sequence_edit_detail.js',
# 'js/sequence/sequence_detail_popup.js',
# 'js/sequence/search.js',
# 'js/sequence/components.js',

# 'js/user/user.js',
# 'js/user/user_edit_detail.js',
# 'js/user/user_detail_popup.js',
# 'js/user/components.js',


# 'js/posts.js',
# 'js/contact_us.js',
# 'js/notifications.js',



# 'js/keyword/keyword.js',
# 'js/keyword/keyword_list_popup_ctrl.js',
# 'js/keyword/keyword_list_read_only_popup_ctrl.js',
# 'js/keyword/components.js',

# 'js/molecule/molecule.js',
# 'js/molecule/molecule_detail.js',
# 'js/molecule/molecule_edit_detail.js',
# 'js/molecule/molecule_detail_popup.js',
# 'js/molecule/search.js',
# 'js/molecule/components.js',



# 'js/golden-colors/golden-colors-amd.min.js',
# 'js/golden-colors/golden-colors.min.js',
# 'js/libs/lodash.js',


# #'js/knockout-js-infinite-scroll/knockout-js-infinite-scroll.js',



# #'js/libs/infinite_scroll.js',
# 'js/libs/notify.js',
# 'js/visual_components/navigation_bar.js',

# 'js/visual_components/datetime_picker.js',
# 'js/visual_components/color_selector.js',
# 'js/visual_components/sobject_field.js',
# 'js/visual_components/timerinput.js',
# 'js/visual_components/numericinput.js',
# 'js/visual_components/lookup.js',
# 'js/visual_components/polymorphic_lookup.js',
# 'js/visual_components/sfdc_lookup.js',
# 'js/visual_components/binary_field.js',
# 'js/visual_components/report_issue.js',
# 'js/visual_components/picklist.js',
# 'js/cropper/cropper.js',
# 'js/news_tab_component.js',
# 'js/dashboard.js',
#             output='gen/application.js')

# assets.register('js_all', js)


if __name__ == "__main__":
    import sys
    import getopt
    opts, args = getopt.getopt(sys.argv[1:], "m:", ["help", "grammar="])

    for opt, arg in opts:
        if opt == '-m' and arg == 'no':
            email_sender.send_emails(False)
    app.run(host='0.0.0.0', port=8080, debug=True)
