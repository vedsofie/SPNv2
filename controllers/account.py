from flask import Blueprint, request, make_response, render_template, session, redirect, url_for, g, Response, flash
from models.user import User, db, SOFIEBIO_ACCOUNTID
from models.account import Account
from models.labsystem import LabSystem
from models.sequence import Sequence
from models.role import Role
from models.molecule import Molecule
from models.sobject import ValidationException
import email_sender
import json
import math
from back import back
from werkzeug import secure_filename
import urllib

accountcontroller = Blueprint("accountcontroller", __name__, template_folder="../templates")

@accountcontroller.route("/account/create", methods=["POST"])
def create():
    data = request.json
    try:
        if "id" in data and data['id']:
            act = Account.query.filter_by(id=data['id']).first()
            act.merge_fields(**data)
        else:
            act = Account()
            act.merge_fields(**data)
            act.validate_required_fields()

        if act.can_save(g.user):
            act.save()
            if request.headers.get("Accept", "") != "application/json":
                return redirect("/user/new?account_id=%s" % act.id)
        else:
            return make_response("You do not have the appropriate role type to create this record", 403)
    except Exception as e:
        db.session.rollback()
        msg = str(e)
        if e.__class__ == ValidationException().__class__:
            msg = e.errors()
        if request.headers.get("Accept") == "application/json":
            return Response(json.dumps({"account": act.to_hash(), "error_details": msg}), status=400, headers={"Content-Type": "application/json"})
        flash(msg)
        return render_template("account/new.html", account=act.to_hash())

    uid = act.id
    act = Account.query.filter_by(id=uid).first()

    if request.headers.get("Accept") == "application/json":
        return Response(json.dumps(act.to_hash()), headers={"Content-Type": "application/json"})

    return redirect("/")

@accountcontroller.route("/account/<account_ids>/contact", methods=["POST"])
def contact_accounts(account_ids):
    data = request.get_json()
    message = data['message']
    name = data['name']
    email = data['email']
    accounts = account_ids.split(',')
    sofiebio = Account.query.filter(Account.id==SOFIEBIO_ACCOUNTID).first()
    matching_accounts = Account.query.filter(Account.id.in_(accounts)).all()
    acts = ['%s (%i)' % (account.name, account.id) for account in matching_accounts]
    message += '\nAttempting to contact:\n' + '\n'.join(acts)
    guest_user = User(FirstName=name, LastName=" ", Email=email)

    email_sender.contact_account(guest_user, sofiebio, message)
    return "OK"


@accountcontroller.route("/account/<int:account_id>/contact", methods=["POST"])
def contact(account_id):
    data = request.get_json()
    message = data['message']
    name = data['name']
    email = data['email']
    contacting_account = Account.query.filter_by(id=account_id).first()
    if g.user:
        account = contacting_account
    else:
        account = Account.query.filter_by(id=SOFIEBIO_ACCOUNTID).first()
        message += "\nContacting Account %s ID: %i" % (account.name,account.id)
    guest_user = User(FirstName=name, LastName=" ", Email=email)

    email_sender.contact_account(guest_user, account, message)
    return "OK"

@accountcontroller.route("/account/<int:account_id>/update_old", methods=["POST", "PUT"])
def update(account_id):
    try:
        account_name = None
        short_description = None
        description = None
        image = None
        primary_contact = None

        if request.method == "POST":
            data = request.form
        elif request.method == "PUT":
            data = request.get_json()

        account_name = data.get('name', None)
        short_description = data.get('short_description', None)
        description = data.get('description', None)
        if 'logo' in request.files:
            image = request.files['logo'].read()

        primary_contact = data.get('primary_contact', None)

        act = Account.query.filter_by(id=account_id).first()
        act.name = account_name if account_name else act.name
        act.short_description = short_description if short_description else act.short_description
        act.description = description if description else act.description
        act.image = image if image else act.image
        if primary_contact:
            act.primary_contact_id = primary_contact
        act.save()
        resp = act.to_hash()
        if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
            return json.dumps(resp)
        return redirect(url_for('.get_account', account_id=act.id))
    except Exception as e:
        return make_response( str(e), 400)


@accountcontroller.route('/account/new/')
def new():
    account = Account()
    return render_template("/account/edit.html", account=json.dumps(account.to_hash()),
                                                 runninguser=json.dumps(g.user.to_hash()))
    """
    if account.can_save(g.user.UserID):
        return render_template("/account/edit.html", account=account.to_hash())
    else:
        return render_template('/')#make_response("You do not have the appropriate role type to create this record", 403)
    """
    #return render_template("account/edit.html", account=json.dumps(account.to_hash()))

"""
@accountcontroller.route('/account/new/')
def edit(account_id):
    account = Account.query.filter_by(id=account_id).first()
    if account.can_save(g.user.UserID):
        return render_template("account/edit.html", account=account.to_hash())
    return make_response("You do not have the appropriate role type to create this record", 403)
"""

@accountcontroller.route("/account/<int:account_id>/", methods=["GET"])
@back.anchor
def get_account(account_id):
    account = Account.query.filter_by(id=account_id).first()
    resp = account

    account_users = []
    for user in account.users:
        if user.Active == True:
            account_users.append(user)

    sequences = account.sequences
    private_sequences = [seq.to_hash() for seq in sequences if not seq.MadeOnElixys or not seq.downloadable]
    public_sequences = [seq.to_hash() for seq in sequences if seq.MadeOnElixys and seq.downloadable]          
    return render_template("account/detail.html", back=back, account=resp, public_sequences=public_sequences, private_sequences=private_sequences, account_users = account_users,runninguser=g.user.to_hash())
    
    # if account is not None:
    #     resp = json.dumps(account.to_hash())
    #     edit_page = request.args.get('edit', False)
    #     if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
    #         return Response(resp, headers={'Content-Type': "application/json"})
    #     if edit_page and account.can_save(g.user):
    #         return render_template("account/edit.html", account=resp, runninguser=json.dumps(g.user.to_hash()))
    #     return render_template("account/detail.html", back=back, account=resp, runninguser=json.dumps(g.user.to_hash()))
    # message = urllib.quote("The organization does not exist")
    # return redirect('/user/dashboard?notificationMessage=%s' % message)

# ================== Edit the details of a particular account ==============
@accountcontroller.route("/account/<int:account_id>/edit/", methods=["GET"])
@back.anchor
def edit_account(account_id):
    account = Account.query.filter_by(id=account_id).first()
    resp = account.to_hash()
    return render_template("/account/edit.html", back=back, account=resp,runninguser=g.user.to_hash())

@accountcontroller.route("/account/<int:account_id>/update/", methods=["POST"])
@back.anchor
def update_account(account_id):
    account = Account.query.filter_by(id=account_id).first()
    data = request.form
    if account.can_save(g.user):
        account.name = data['name']
        account.LabName = data['LabName']
        account.description = data['description']
        account.City = data['City']
        account.State = data['State']
        account.ZipCode = data['ZipCode']
        account.Address = data['Address']
        account.Latitude = data['Latitude']
        account.Longitude = data['Longitude']
        if account.save():
            return redirect(url_for('.get_account', account_id=account_id))
        else:
            error = "There was an error saving the changes to database"
            return redirect(url_for('.edit_account', account_id=account_id), error)

    # resp = account.to_hash()
    # return render_template("/account/edit.html", back=back, account=resp,runninguser=g.user.to_hash())

@accountcontroller.route("/account/undefined/logo/", methods=["GET"])
def get_default_logo():
    default_image = open("static/img/default-user.png", "rb")
    return default_image.read()

@accountcontroller.route("/account/<int:account_id>/logo/", methods=["GET"])
def get_account_logo(account_id):
    account = Account.query.filter_by(id=account_id).first()
    if account.image is not None:
        return account.image
    return get_default_logo()

@accountcontroller.route("/account/sequences", methods=["GET"])
def my_account_sequences():
    user = User.query.filter_by(UserID=session['userid']).first()
    account = user.account
    sequences = []
    if account is not None:
        sequences = account.sequences
    resp = json.dumps( [sequence.to_hash() for sequence in sequences] )
    return resp

@accountcontroller.route("/account/<int:account_id>/sequence_count", methods=["GET"])
def sequence_count(account_id):
    account = Account.query.filter_by(id=account_id).first()
    sequences = []
    if account is not None:
        sequences = account.sequences
    return str(len(sequences))


@accountcontroller.route("/account/<int:account_id>/sequences", methods=["GET"])
def sequences(account_id):
    account = Account.query.filter_by(id=account_id).first()
    sequences = []
    if account is not None:
        sequences = account.sequences
    resp = json.dumps( [sequence.to_hash() for sequence in sequences] )

    if "Accept" in request.headers and request.headers['Accept'] == 'application/json':
        return resp
    return render_template("sequence/sequences.html", sequences=resp)

@accountcontroller.route("/account/<int:account_id>/probes", methods=["GET"])
def unique_probes_for(account_id):
    account = Account.query.filter_by(id=account_id).first()
    molecule_ids = []
    if account is not None:
        molecule_ids = set([sequence.MoleculeID for sequence in account.sequences])

    molecules = Molecule.query.filter(Molecule.ID.in_(molecule_ids)).all()
    resp = []
    for molecule in molecules:
        if molecule.Approved:
            x = molecule.to_hash()
            x.update({"AccountID": account_id, "AccountName": account.name})
            resp.append(x)
    resp = json.dumps(resp)

    return Response(resp, content_type='application/json')

@accountcontroller.route("/account/probes/")
def all_probes_for_account():
    resp = []
    accounts = Account.query.all()

    for account in accounts:
        molecule_ids = []
        molecule_ids = set([sequence.MoleculeID for sequence in account.sequences])
        molecules = Molecule.query.filter(Molecule.ID.in_(molecule_ids)).all()
        for molecule in molecules:
            if molecule.Approved:
                x = molecule.to_hash()
                y = {"Name": x["Name"],"searchName": getName(x["Name"]), "AccountID": account.id, "AccountName": account.name, "number" : 0, "url": '/probe/'+str(molecule.ID)+'/image/'}
                resp.append(y)

    resp = json.dumps(resp)
    return Response(resp, content_type='application/json')

def getName(name) :
    return name.split("]")[1].rstrip()


@accountcontroller.route("/account/<int:account_id>/user_count", methods=["GET"])
def user_count(account_id):
    account = Account.query.filter_by(id=account_id).first()
    users = []
    if account is not None:
        users = account.users
    return str(len(users))

@accountcontroller.route("/account/<int:account_id>/users", methods=["GET"])
def users(account_id):
    account = Account.query.filter_by(id=account_id).first()
    users = []
    if account is not None:
        users = account.users
    resp = json.dumps( [user.to_hash() for user in users] )
    if "Accept" in request.headers and request.headers['Accept'] == 'application/json':
        return resp
    return render_template("user/users.html", users=resp)


@accountcontroller.route("/account/", methods=["GET"])
@back.anchor
def show():
    page_number = request.args.get("page", 1, type=int)
    all_accounts = Account.query.order_by(Account.name).all()
    all_accounts_count = Account.query.order_by(Account.name).count()
    number_of_pages = int(math.ceil(all_accounts_count / 9.0))
    response = []
    for act in all_accounts:
        x = act.to_hash()
        x.update({"sequence_count": len(act.sequences)})
        response.append(x)
    response.sort(key=lambda account: account["sequence_count"], reverse=True)
    lower_limit = page_number*9 - 9
    upper_limit = page_number*9
    response = response[lower_limit : upper_limit]



    # #pagination
    # all_accounts = Account.query.order_by(Account.name).limit(9)
    
    # number_of_pages = 0
    # if all_accounts_count > 9:
    #     all_accounts = all_accounts.offset((page_number*9) - 9)
    #     number_of_pages = int(math.ceil(all_accounts_count / 9.0))



    return render_template("account/accounts.html", accounts=response, current_page_number = page_number, number_of_pages = number_of_pages,runninguser=g.user.to_hash())

@accountcontroller.route('/account/<int:account_id>/user/available_roles/')
def get_available_roles(account_id):
    running_users_role = g.user.role.Type
    roles = Role.query.all()
    to_exclude = set()
    if running_users_role != 'super-admin' or account_id != SOFIEBIO_ACCOUNTID:
        to_exclude.add('super-admin')
    if running_users_role == 'chemist':
        to_exclude.add('admin')
    resp = [role.to_hash() for role in roles if role.Type not in to_exclude]

    return Response(json.dumps(resp), content_type='application/json')
