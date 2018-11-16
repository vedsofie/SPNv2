import os
import requests
import json
import random
import httpagentparser
import math
import datetime
from Crypto.Cipher import AES
from flask import Blueprint, render_template, request, Response, session, g, flash, redirect
from models.keyword import Keyword, db
from models.comment import Comment
from models.molecule import Molecule, ValidationException
from models.user import User
from models.sequence import Sequence
from models.follower import Follower
from back import back
import molecule_api.search
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_, or_, func
import urllib
SOFIEBIO_USER = int(os.getenv("SOFIEBIO_USERID", 0))
moleculecontroller = Blueprint('moleculecontroller', __name__, url_prefix="/probe",static_folder='static')

@moleculecontroller.route("/", methods=['GET'])
def index():
    specific_ids = request.args.get("MoleculeIDs", '')
    specific_ids = specific_ids.split(',')
    specific_ids = specific_ids if specific_ids[0] != '' else []
    page_number = request.args.get("page", 1, type=int)
    ids = []
    for specific_id in specific_ids:
        try:
            spec_id = int(specific_id)
            ids.append(specific_id)
        except Exception as e:
            pass
    sql_filter = Molecule.Approved == True
    if len(specific_ids) > 0:
        sql_filter = and_(sql_filter, Molecule.ID.in_(ids))

    #all_molecules = Molecule.query.order_by(Molecule.Name).filter(sql_filter).all()
    all_molecules = Molecule.query.order_by(Molecule.Name).filter(sql_filter).limit(9)
    all_molecules_count = Molecule.query.order_by(Molecule.Name).filter(sql_filter).count()
    number_of_pages = 0
    if all_molecules_count > 9:
        all_molecules = all_molecules.offset((page_number*9) - 9)
        number_of_pages = int(math.ceil(all_molecules_count / 9.0))

    sorted_molecules = []
    for molecule in all_molecules:
        x = molecule.to_hash()
        y = {"ID": x["ID"],"Formula": x["Formula"],"CID": x["CID"],"CAS": x["CAS"],"Name": x["Name"],"DisplayFormat": x["DisplayFormat"],"Description": x["Description"],"Isotope": x["Isotope"],"Approved": x["Approved"],"UserID": x["UserID"],"Sort": x["Name"].split(']')[1]}
        sorted_molecules.append(y)
    
    #sorted_molecules.sort(key=lambda x: x["Sort"].lower(), reverse=False)
    mole_dict = {}
    for molecule in sorted_molecules:
        if molecule['Isotope'] in mole_dict:
            mole_dict[molecule['Isotope']].append(molecule)
        else:
            mole_dict[molecule['Isotope']] = []
            mole_dict[molecule['Isotope']].append(molecule)

    molecules_list = []
    for key, value in mole_dict.iteritems():
        value.sort(key=lambda x: x["Sort"].lower(), reverse=False)
        molecules_list.extend(value)

    #molecules_list.reverse()
    #resp = json.dumps([molecule.to_hash() for molecule in all_molecules])
    resp = molecules_list
    userid = session["userid"]
    return render_template("molecule/molecules.html", molecules=resp, uid = userid, current_page_number = page_number, number_of_pages = number_of_pages,runninguser=json.dumps(g.user.to_hash()))




@moleculecontroller.route("/my_probes", methods=['GET'])
def my_probes():
    specific_ids = request.args.get("MoleculeIDs", '')
    specific_ids = specific_ids.split(',')
    specific_ids = specific_ids if specific_ids[0] != '' else []
    userid = session["userid"]
    page_number = request.args.get("page", 1, type=int)  #this is used for pagination, dont delete
    ids = []
    for specific_id in specific_ids:
        try:
            spec_id = int(specific_id)
            ids.append(specific_id)
        except Exception as e:
            pass
    sql_filter = Molecule.Approved == True
    if len(specific_ids) > 0:
        sql_filter = and_(sql_filter, Molecule.ID.in_(ids))
    molecules_list = []
    #all_molecules = Molecule.query.order_by(Molecule.Name).filter(sql_filter).all()
    all_molecules = Molecule.query.filter_by(UserID=userid).order_by(Molecule.Name).limit(9)
    my_molecules_count = Molecule.query.filter_by(UserID=userid).count()
    number_of_pages = 0
    if my_molecules_count > 9:
        all_molecules = all_molecules.offset((page_number*9) - 9)
        #all_molecules_count = Molecule.query.order_by(Molecule.Name).filter(sql_filter).count()
        number_of_pages = int(math.ceil(my_molecules_count / 9.0))


    sorted_molecules = []
    for molecule in all_molecules:
        x = molecule.to_hash()
        y = {"ID": x["ID"],"Formula": x["Formula"],"CID": x["CID"],"CAS": x["CAS"],"Name": x["Name"],"DisplayFormat": x["DisplayFormat"],"Description": x["Description"],"Isotope": x["Isotope"],"Approved": x["Approved"],"UserID": x["UserID"],"Sort": x["Name"].split(']')[1]}
        sorted_molecules.append(y)
    
    #sorted_molecules.sort(key=lambda x: x["Sort"].lower(), reverse=False)
    mole_dict = {}
    for molecule in sorted_molecules:
        if molecule['Isotope'] in mole_dict:
            mole_dict[molecule['Isotope']].append(molecule)
        else:
            mole_dict[molecule['Isotope']] = []
            mole_dict[molecule['Isotope']].append(molecule)

    
    for key, value in mole_dict.iteritems():
        value.sort(key=lambda x: x["Sort"].lower(), reverse=False)
        molecules_list.extend(value)
            #molecules_list.reverse()
    #resp = json.dumps([molecule.to_hash() for molecule in all_molecules])
    resp = molecules_list

    return render_template("molecule/my_probes.html", molecules=resp, uid = userid, current_page_number = page_number, number_of_pages = number_of_pages,runninguser=json.dumps(g.user.to_hash()))

@moleculecontroller.route("/<int:cid>/auto_fill/", methods=["GET"])
def autofill(cid):
    mole = Molecule(CID=cid)
    mole.autofill(get_image=False)
    keywords = mole.get_keywords()
    keyword_resp = [keyword.to_hash() for keyword in keywords]
    resp = {"molecule": mole.to_hash(), "keywords": keyword_resp}
    return Response(json.dumps(resp), content_type="application/json")

@moleculecontroller.route("/new/", methods=['GET'])
def new():
    mole = Molecule()
    resp = json.dumps(mole.to_hash())
    return render_template("molecule/edit.html", molecule=resp, runninguser=json.dumps(g.user.to_hash()))

@moleculecontroller.route("/<int:molecule_id>/edit/", methods=['GET'])
def edit(molecule_id):
    userid = session["userid"]
    molecule = Molecule.query.filter_by(ID=molecule_id).first()
    return render_template("molecule/edit.html", molecule=molecule, uid = userid,runninguser=json.dumps(g.user.to_hash()))

@moleculecontroller.route("/<int:molecule_id>/", methods=['GET'])
@back.anchor
def get_details(molecule_id):
    edit_page = request.args.get('edit', False)
    userid = session["userid"]
    molecule = Molecule.query.filter_by(ID=molecule_id).first()
    # Get sequences for this molecule
    sequences = Sequence.query.filter_by(MoleculeID=molecule_id).all()
    all_seq_resp = [seq.to_hash() for seq in sequences if seq.downloadable]
    private_sequences = [seq.to_hash() for seq in sequences if not seq.MadeOnElixys or not seq.downloadable]
    public_sequences = [seq.to_hash() for seq in sequences if seq.MadeOnElixys and seq.downloadable]
    #fetching synonyms for probe
    keywords = Keyword.query.filter_by( ParentID=molecule_id, Type="Molecules").all()
    keywords_hash = [keyword.to_hash() for keyword in keywords ]
    # Get account of the user who uploaded a sequence (this is used to get logo of that )


    # get comments for this probe
    all_comments = []
    comments = Comment.query.filter(and_(Comment.ParentID == molecule_id,Comment.Type == 'Molecules')).order_by(Comment.CreationDate.desc()).all()
    for comment in comments:
        users_name = User.query.filter_by(UserID=comment.UserID).first()
        comments_aggr = comment.to_hash()
        comments_aggr['CreationDate'] = datetime.datetime.fromtimestamp(int(comments_aggr['CreationDate'] / 1000)).strftime('%m / %d / %Y')
        comments_aggr['username'] = users_name.username
        all_comments.append(comments_aggr)
    # Check if logged in user is following this probe
    follower = Follower.query.filter(and_(Follower.ParentID == molecule_id, Follower.UserID == userid, Follower.Type == 'Molecules')).first()

    usr = g.user.to_hash()
    
    if molecule and (molecule.Approved or g.user.role.Type == 'super-admin'):
        resp = molecule.to_hash()
        if "Accept" in request.headers and request.headers['Accept'] == "application/json":
            return Response(resp, headers={"Content-Type": "application/json"})

        if edit_page and molecule.can_save(g.user):
            return render_template("molecule/edit.html", molecule=resp, uid = userid,runninguser=json.dumps(usr))

        return render_template("molecule/detail.html", molecule=resp, public_sequences=public_sequences, private_sequences=private_sequences, follower = follower,comments = all_comments, keywords = keywords_hash,uid = userid,runninguser=json.dumps(usr))
    

    else:
        if(molecule):
            message = urllib.quote("%s is being reviewed by Sofie Biosciences,\n" % molecule.Name +
                                   "if you are following this probe, you will be notified when it has been approved.\n" +
                                   "Thank you for your patience")
        else:
            message = urllib.quote("The Probe Does not exist")
        return redirect('/user/dashboard?notificationMessage=%s' % message)

@moleculecontroller.route("/<int:molecule_id>/check_following/", methods=['GET'])
def is_following(molecule_id):
    follower = Follower.query.filter(and_(Follower.ParentID == molecule_id,
                                     Follower.Type == 'Molecules',
                                     Follower.UserID == session['userid'])).first()
    return Response(json.dumps(follower is not None), headers={"Content-Type": 'application/json'})

@moleculecontroller.route("/<int:molecule_id>/", methods=['DELETE'])
def delete_molecule(molecule_id):
    molecule = Molecule.query.filter_by(ID=molecule_id).first()
    molecule.Approved = False
    molecule.save()
    return "OK"

@moleculecontroller.route("/<int:molecule_id>/unfollow/", methods=['DELETE'])
def unfollow(molecule_id):
    userid = session['userid']
    follower = Follower.query.filter(and_(Follower.ParentID == molecule_id,
                                          Follower.UserID == userid,
                                          Follower.Type == 'Molecules')).first()
    if follower:
        db.session.delete(follower)
        db.session.commit()

    return "OK"

@moleculecontroller.route("/<int:molecule_id>/follow/", methods=['POST'])
def follow(molecule_id):
    userid = session['userid']
    follower = Follower.query.filter(and_(Follower.ParentID == molecule_id,
                                          Follower.UserID == userid,
                                          Follower.Type == 'Molecules')).first()
    if not follower:
        follower = Follower(Type='Molecules', ParentID=molecule_id, UserID=userid)
        follower.save()

    return "OK"

@moleculecontroller.route("/undefined/image/")
def get_default_image():
    default_image = open("seeds/FAraG.png", "rb")
    return default_image.read()

@moleculecontroller.route("/<int:molecule_id>/image/")
def get_image(molecule_id):
    mole = Molecule.query.filter_by(ID=molecule_id).first()
    if mole.Image:
        img = mole.Image
    else:
        return get_default_image()
    """
    if mole.image_url != "":
        req = requests.get(mole.image_url)
        img = req.content
    else:
    """
    img = mole.Image
    return Response(img)#, headers={'content-type': 'image/png'})

@moleculecontroller.route("/<int:molecule_id>/keywords", methods=['GET'])
def get_molecules_keywords(molecule_id):
    keywords = Keyword.query.filter_by( ParentID=molecule_id, Type="Molecules").all()
    resp = json.dumps([keyword.to_hash() for keyword in keywords])
    return Response(resp, headers={'content-type': 'application/json'})

@moleculecontroller.route("/<int:molecule_id>/private_accounts/", methods=['GET'])
def get_private_account_sequences(molecule_id):
    sequences = Sequence.query.filter(Sequence.MoleculeID==molecule_id).all()
    private_sequences = [seq for seq in sequences if not seq.MadeOnElixys or not seq.downloadable]
    private_sequence_ownerids = set([seq.UserID for seq in private_sequences])
    users = User.query.filter(User.UserID.in_(private_sequence_ownerids))
    acts = {}
    for user in users:
        if user.AccountID not in acts:
            acts[user.AccountID] = user.account
    accounts = [acts[account].to_hash() for account in acts]
    resp = json.dumps(accounts)
    return Response(resp, headers={'content-type': 'application/json'})

@moleculecontroller.route("/<int:molecule_id>/sequences", methods=['GET'])
def get_molecules_sequences(molecule_id):
    sequences = Sequence.query.filter_by(MoleculeID=molecule_id).all()
    resp = json.dumps([sequence.to_hash() for sequence in sequences])
    return Response(resp, headers={'content-type': 'application/json'})

@moleculecontroller.route("/<int:molecule_id>/do_i_make_this/", methods=['GET'])
def do_i_make_this(molecule_id):
    act_sequences = g.user.account.sequences
    for seq in act_sequences:
        if seq.MoleculeID == molecule_id:
            return Response(json.dumps(True), headers={"Content-Type": "application/json"})
    return Response(json.dumps(False), headers={"Content-Type": "application/json"})

@moleculecontroller.route("/<int:molecule_id>/sequence_count", methods=['GET'])
def get_sequence_count(molecule_id):
    sequences = Sequence.query.filter_by(MoleculeID=molecule_id).all()
    resp = json.dumps(len(sequences))
    return Response(resp, headers={'content-type': 'application/json'})

@moleculecontroller.route("/search", methods=['GET'])
def search_by_name():
    chem_name = request.args['chemical_name']
    matches = molecule_api.search.find_matches(chem_name)
    chems = {}
    resp = []

    for match in matches["PropertyTable"]["Properties"]:
        key = str(match['CID'])
        chems[key] = match
        chems[key]['seq_count'] = 0

    our_mols = Molecule.query.filter(Molecule.CID.in_(chems.keys())).all()
    our_molecules = {str(mole.CID): mole for mole in our_mols}
    our_mole_ids = [mole.ID for mole in our_mols]
    seq_count = db.session.query(Sequence.MoleculeID, func.count(Sequence.SequenceID)).group_by(Sequence.MoleculeID).filter(Molecule.ID.in_(our_mole_ids)).all()
    seq_by_mole_count = {counter[0]: counter[1] for counter in seq_count}

    for key in our_molecules:
        mol = our_molecules[str(key)]
        chem = chems[str(key)]
        chem['Description'] = mol.Description
        chem['Name'] = mol.Name
        chem['ID'] = mol.ID
        chem['seq_count'] = seq_by_mole_count[mol.ID] if mol.ID in seq_by_mole_count else 0
        resp.append(chem)

    unknown_cids = set(chems.keys()).difference(our_molecules.keys())
    if(len(unknown_cids) > 0):
        res = molecule_api.search.get_common_names(list(unknown_cids))
        res = res['InformationList']['Information']
        for chem in res:
            key = str(chem['CID'])
            res_chem = chems[key]
            res_chem['Name'] = chem['Title']
            chem['seq_count'] = 0
            resp.append(res_chem)

    if len(matches) == 0:
        Keyword.add_search_word(chem_name, search_type="molecule")
    return Response(json.dumps(resp), headers={'content-type': 'application/json'})

@moleculecontroller.route("/hint/<keyword>", methods=['GET'])
def search_hints(keyword):
    include_keywords = request.args.get("includeKeywords", True)
    include_keywords = False if include_keywords == 'false' else True
    keyword = keyword.lower()
    #if len(keyword) >= 3:
    keyword_filters = and_(func.lower(Keyword.Keyword).like("%" + keyword + "%"),
                           Keyword.Type=='Molecules')
    if not include_keywords:
        keyword_filters = and_(keyword_filters, Keyword.Category=='Synonym')

    molecule_id_to_keywords = {}
    for key in Keyword.query.filter(keyword_filters).all():
        if key.ParentID not in molecule_id_to_keywords:
            molecule_id_to_keywords[key.ParentID] = []
        molecule_id_to_keywords[key.ParentID].append(key.DisplayFormat)

    running_user_id = g.user.UserID if g.user else None

    molecules = Molecule.query.filter(and_(or_(Molecule.Approved==True,Molecule.UserID==running_user_id),
                                           or_(Molecule.ID.in_(molecule_id_to_keywords.keys()),
                                               func.lower(Molecule.Name).like('%' + keyword + '%')
                                           )
                                     )).all()
    resp = []
    for molecule in molecules:
        resp.append({
            "master_name": molecule.Name,
            "formatted_master_name": molecule.DisplayFormat,
            "keywords": molecule_id_to_keywords.get(molecule.ID, []),
            "molecule_id": molecule.ID,
            "url":'/probe/'+str(molecule.ID)+'/image/',
            "searchName": getName(molecule.Name)
        })
    return Response(json.dumps(resp), content_type="application/json")

def getName(name) :
    return name.split("]")[1].rstrip()

@moleculecontroller.route("/<int:molecule_id>/sObject/Name", methods=['GET'])
def get_molecule_name(molecule_id):
    res = Molecule.query.filter_by(ID=molecule_id).first()
    return Response(res.Name)

@moleculecontroller.route("/list/", methods=['GET', 'POST'])
def find():
    chem_name = request.json.get('keyword', None)
    molecule_id = request.json.get('molecule_id', None)
    action_type = request.json.get('actionType', 'ajax')
    molecule_id_matches = []

    if molecule_id is None:
        molecule_matches = search_hints(chem_name)
        resp = json.loads(molecule_matches.data) if molecule_matches.data != '' else {}
        for match in resp:
            molecule_id_matches.append(match['molecule_id'])
    else:
        molecule_id_matches.append(molecule_id)

    resp = Molecule.query.filter(Molecule.ID.in_(molecule_id_matches)).all()
    resp = [mole.to_hash() for mole in resp]

    if action_type == "redirect":
        if len(molecule_id_matches) == 1:
            resp = {"redirect_to": "/probe/%i/" % molecule_id_matches[0]}
            return Response(json.dumps(resp), content_type="application/json")
        else:
            molecule_id_matches = [str(molecule_id) for molecule_id in molecule_id_matches]
            resp = {"redirect_to": "/probe/?MoleculeIDs=%s" % (",".join(molecule_id_matches))}
            return Response(json.dumps(resp), content_type="application/json")

    return Response(json.dumps(resp), headers={'content-type': 'application/json'})

@moleculecontroller.route("/create", methods=["POST"])
def create():
    data = request.json
    try:
        mole = do_save(g.user, **data)
        if request.headers.get("Accept") == "application/json":
            return Response(json.dumps(mole.to_hash()), headers={"Content-Type": "application/json"})
        return redirect("/")
    except Exception as e:
        db.session.rollback()
        msg = str(e)
        if e.__class__ == ValidationException().__class__:
            msg = e.errors()

        if request.headers.get("Accept") == "application/json":
            return Response(json.dumps({"molecule": Molecule.to_hash(), "error_details": msg}), status=400, headers={"Content-Type": "application/json"})
        flash(msg)
        return render_template("molecule/new.html", molecule=Molecule().to_hash())

    """
    id = data.get("ID", None)
    was_approved = None
    if not id or can_approve:# Only super-admins can edit a molecule for now
        try:
            if id:
                mole = Molecule.query.filter_by(ID=data['ID']).first()
                already_approved = mole.Approved
                mole.merge_fields(**data)
                was_approved = mole.Approved and not already_approved
                mole.validate_required_fields()
            else:
                mole = Molecule()
                mole.merge_fields(**data)
                mole.UserID = g.user.UserID
                mole.Approved = can_approve and data['Approved']
                mole.validate_required_fields()
            mole.save()
        except Exception as e:
            db.session.rollback()
            msg = str(e)
            if e.__class__ == ValidationException().__class__:
                msg = e.errors()

            if request.headers.get("Accept") == "application/json":
                return Response(json.dumps({"molecule": mole.to_hash(), "error_details": msg}), status=400, headers={"Content-Type": "application/json"})
            flash(msg)
            return render_template("molecule/new.html", molecule=mole.to_hash())

        uid = mole.ID

        if was_approved:
            message = "%s was approved" % mole.Name
            comment = Comment(UserID=g.user.UserID, Type='Molecules',ParentID=mole.ID, Message=message, RenderType='text')
            comment.save()
        mole = Molecule.query.filter_by(ID=uid).first()

        if request.headers.get("Accept") == "application/json":
            return Response(json.dumps(mole.to_hash()), headers={"Content-Type": "application/json"})

        return redirect("/")
    else:
        return Response("You do not have permission to create molecules", 403)
    """

def do_save(user, **kwargs):
    can_approve = user.role.Type == 'super-admin'
    id = kwargs.get("ID", None)
    was_approved = None
    uid = None
    if not id or can_approve:# Only super-admins can edit a molecule for now
        if id:
            mole = Molecule.query.filter_by(ID=kwargs['ID']).first()
            already_approved = mole.Approved
            mole.merge_fields(**kwargs)
            was_approved = mole.Approved and not already_approved
            mole.validate_required_fields()
        else:
            mole = Molecule()
            mole.merge_fields(**kwargs)
            mole.UserID = user.UserID
            mole.Approved = can_approve and kwargs['Approved']
            mole.validate_required_fields()
        mole.save()

        uid = mole.ID

    if was_approved:
        message = "%s was approved" % mole.Name
        comment = Comment(UserID=user.UserID, Type='Molecules',ParentID=mole.ID, Message=message, RenderType='text')
        comment.save()

    if uid:
        mole = Molecule.query.filter_by(ID=uid).first()
        return mole
    return None
