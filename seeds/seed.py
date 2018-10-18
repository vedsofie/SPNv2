import generate_db
import time
import os
import base64
#generate_db.drop_database()
generate_db.generate_database()
from chat_server import email_sender
email_sender.send_emails(False)
from models.account import Account, db
from models.forum import Forum
from models.role import Role
from models.molecule import Molecule
from models.sequence import Sequence
from models.follower import Follower
from models.sequenceattachment import SequenceAttachment
from models.labsystem import LabSystem
from models.uniquesequencedownload import UniqueSequenceDownload
from models.user import User
from models.comment import Comment
from data_migrations.generate_molecules_to_approve_following import create_approval_following

import models.model_helpers as model_helpers

user_count = 0
PAGINATION_SIZE = 20


def generate_accounts():
    accounts = []
    sofie = Account(name="Sofie Biosciences, Inc.", Latitude=33.98, Longitude=-118.39, LabName="Radiochemistry Division", description="We are biotech company which specializes in enabling PET imaging through the development of innovative instrumentation",\
                    City='Culver City', State='California', Address='6162 Bristol Parkway', ZipCode='90230')
    ucla = Account(name="UCLA", Latitude=34.07, Longitude=-118.44)
    stanford = Account(name='Stanford', Latitude=37.4282640,Longitude=-122.1688450)
    mgh = Account(name='MGH', Latitude=42.36, Longitude=-71.06)
    uc_davis = Account(name='UC Davis', Latitude=38.53, Longitude=-121.75)
    hopkins = Account(name='John Hopkins', Latitude=39.29, Longitude=-76.61)
    mskcc = Account(name='MSKCC', Latitude=40.76, Longitude=-73.95)
    thunder_bay = Account(name='Thunder Bay', Latitude=48.42, Longitude=-89.26)
    ucsf = Account(name='UCSF', Latitude=37.76, Longitude=-122.45)
    wash_u = Account(name='Wash Univ', Latitude=38.64, Longitude=-90.30)
    uni_tennessee = Account(name='Univ of Tennessee', Latitude=35.96, Longitude=-83.92)
    accounts.append(sofie)
    accounts.append(ucla)
    accounts.append(stanford)
    accounts.append(mgh)
    accounts.append(uc_davis)
    accounts.append(hopkins)
    accounts.append(mskcc)
    accounts.append(thunder_bay)
    accounts.append(ucsf)
    accounts.append(wash_u)
    accounts.append(uni_tennessee)
    for act in accounts:
        db.session.add(act)
    db.session.commit()

    """
    sofie_system = LabSystem(AccountID=sofie.id, Latitude=33.98, Longitude=-118.39)
    stanford_system = LabSystem(AccountID=stanford.id, Latitude=37.4282640,Longitude=-122.1688450)
    ucla1 = LabSystem(AccountID=ucla.id, Latitude=34.07, Longitude=-118.44)
    ucla2 = LabSystem(AccountID=ucla.id, Latitude=34.07, Longitude=-118.44)
    ucla3 = LabSystem(AccountID=ucla.id, Latitude=34.07, Longitude=-118.44)
    ahmanson = LabSystem(AccountID=ucla.id, Latitude=34.06, Longitude=-118.44)
    ucsf_system = LabSystem(AccountID=ucsf.id, Latitude=37.76, Longitude=-122.45)
    mgh_system = LabSystem(AccountID=mgh.id, Latitude=42.36, Longitude=-71.06)
    uc_davis_system = LabSystem(AccountID=uc_davis.id, Latitude=38.53, Longitude=-121.75)
    hopkins_system = LabSystem(AccountID=hopkins.id, Latitude=39.29, Longitude=-76.61)

    mskcc_system = LabSystem(AccountID=mskcc.id, Latitude=40.76, Longitude=-73.95)
    thunder_bay_system = LabSystem(AccountID=thunder_bay.id, Latitude=48.42, Longitude=-89.26)
    wash_u_system = LabSystem(AccountID=wash_u.id, Latitude=38.64, Longitude=-90.30)
    tennessee_system = LabSystem(AccountID=uni_tennessee.id, Latitude=35.96, Longitude=-83.92)
    db.session.add(sofie_system)
    db.session.add(stanford_system)
    db.session.add(ucla1)
    db.session.add(ucla2)
    db.session.add(ucla3)
    db.session.add(ahmanson)
    db.session.add(ucsf_system)
    db.session.add(mgh_system)
    db.session.add(uc_davis_system)
    db.session.add(hopkins_system)
    db.session.add(mskcc_system)
    db.session.add(thunder_bay_system)
    db.session.add(wash_u_system)
    db.session.add(tennessee_system)
    db.session.commit()
    """
    return accounts


def generate_users(account_id, count, roleid):
    users = []
    global user_count
    for i in xrange(count):
        x = i + user_count
        usr = generate_user(account_id, "user%i" % x, roleid)
        users.append(usr)
        user_count += 1
    return users


def generate_user(account_id, username,roleid):
    usr = User(username=username,password='test',RoleID=roleid,title='Users Title',AccountID=account_id,Email="test@test.com",LastName="LastName", FirstName="FirstName")
    usr.save()
    uid = usr.UserID
    #uid = User.create(username, account_id, "test", "test", title="Users Title", email="test@test.com", first_name="FirstName", last_name="LastName")
    return uid


def generate_zipped_sequence(userid, moleculeId):
    data = open(os.path.join("seeds", "sequence_data", "D-FAC.zip"), 'rb')
    data = data.read()
    return model_helpers.do_import(data, userid, {"MoleculeID": moleculeId, "MadeOnElixys": True, "PurificationMethod": "HPLC"})


def generate_sequence(userid, moleculeid):
    data = open(os.path.join("seeds", "sequence_data", "D-FAC-2014-12-03.sequence"), 'r')
    data = data.read()
    return model_helpers.do_import(data, userid, {"MadeOnElixys": True, "MoleculeID": moleculeid, "PurificationMethod": "HPLC"})

def generate_private_sequence(userid, moleculeid, madeOnElixys=True):
    seq = Sequence(UserID=userid, MoleculeID=moleculeid, Name="Private Sequence", MadeOnElixys=madeOnElixys)
    seq.save()

def generate_comment(userid, sequence_id, message='This is a test comment'):
    com = Comment()
    com.Message = message
    com.UserID = userid
    com.ParentID = sequence_id
    com.Type = 'Sequences'
    com.save()

def generate_forums(accountid):
    forums = [Forum(Subject="General", Color="#7993F2"),
              Forum(Subject="Wish List", Color="#F2C179")]
    for forum in forums:
        forum.AccountID = accountid
        db.session.add(forum)
    db.session.commit()

def generate_issues():
    from controllers.issue import generate_issue
    user = User.query.first()
    generate_issue(user, 'subject', 'subtitle', 'message', 0, 0, None, sfdc_data={'assistanceRequest': '',
                                                                                                        'instrument': '',
                                                                                                        'elixysVersion': ''})

def generate_roles():
    admin = Role(Type='admin')
    admin.save()
    super_admin = Role(Type='super-admin')
    super_admin.save()
    chemist = Role(Type='standard user')
    chemist.save()
    return (chemist, admin, super_admin)


def generate_unique_downloads():
    sequences = Sequence.query.limit(3)
    user = User.query.first()
    for seq in sequences:
        unique = UniqueSequenceDownload(SequenceID=seq.SequenceID,UserID=user.UserID)
        unique.save()

def seed_data():
    molecule = Molecule(CID=3232583, DisplayFormat="<p>[<sup>18</sup>F]-<sub>D</sub>-FEAU</p>", \
                        Description="FEAU is an nucleoside analog and a highly specific substrate for herpes simplex " \
                                    "virus 1 thymidine kinase (HSV1-tk). FEAU is phosphorylated by HSV1-tk " \
                                    "and subsequently retained intracellularly; hence it can annotate HSV1-tk " \
                                    "expression in vivo. The gene encoding HSV1-tk is a commonly used reporter gene " \
                                    "in cell-based therapy studies.",
                        Name="<p>[<sup>18</sup>F]-<sub>D</sub>-FEAU</p>")
    molecule.save()

    molecule1 = Molecule(CID=3232584, DisplayFormat="<p>[<sup>18</sup>F]-<sub>D</sub>-FEAU</p>", \
                        Description="FEAU is an nucleoside analog and a highly specific substrate for herpes simplex " \
                                    "virus 1 thymidine kinase (HSV1-tk). FEAU is phosphorylated by HSV1-tk " \
                                    "and subsequently retained intracellularly; hence it can annotate HSV1-tk " \
                                    "expression in vivo. The gene encoding HSV1-tk is a commonly used reporter gene " \
                                    "in cell-based therapy studies.",
                        Name="FEAU")
    molecule1.save()

    molecule2 = Molecule(CID=3232585, DisplayFormat="<p>[<sup>18</sup>F]-<sub>D</sub>-FEAU</p>", \
                        Description="FEAU is an nucleoside analog and a highly specific substrate for herpes simplex " \
                                    "virus 1 thymidine kinase (HSV1-tk). FEAU is phosphorylated by HSV1-tk " \
                                    "and subsequently retained intracellularly; hence it can annotate HSV1-tk " \
                                    "expression in vivo. The gene encoding HSV1-tk is a commonly used reporter gene " \
                                    "in cell-based therapy studies.",
                        Name="FEAU")
    molecule2.save()

    molecule3 = Molecule(CID=3232586, DisplayFormat="<p>[<sup>18</sup>F]-<sub>D</sub>-FEAU</p>", \
                        Description="FEAU is an nucleoside analog and a highly specific substrate for herpes simplex " \
                                    "virus 1 thymidine kinase (HSV1-tk). FEAU is phosphorylated by HSV1-tk " \
                                    "and subsequently retained intracellularly; hence it can annotate HSV1-tk " \
                                    "expression in vivo. The gene encoding HSV1-tk is a commonly used reporter gene " \
                                    "in cell-based therapy studies.",
                        Name="FEAU")
    molecule3.save()

    molecule.save_synonyms_from_pubchem()
    accounts = generate_accounts()
    main_account = accounts[0]
    generate_forums(main_account.id)
    alternative_account = accounts[1]
    chemist, admin, super_admin = generate_roles()
    main_user = generate_user(main_account.id, "test", super_admin.RoleID)
    create_approval_following()
    main_account_users = generate_users(main_account.id, 5, chemist.RoleID)
    alternative_account_users = generate_users(alternative_account.id, 5, chemist.RoleID)
    competitor_user = alternative_account_users[0]
    sequence_id = generate_zipped_sequence(main_user, molecule.ID)

    data = open(os.path.join("seeds", "molecule.jpeg"), 'r')
    data = data.read()
    reaction_scheme = SequenceAttachment(SequenceID=sequence_id, FileName='molecules.jpg', Type="ReactionScheme", Attachment=data)
    reaction_scheme.save()
    competitor_sequence = generate_zipped_sequence(competitor_user, molecule.ID)
    follow = Follower(UserID=main_user, Type="Sequences", ParentID=competitor_sequence)
    follow.save()

    follow = Follower(UserID=main_user, Type="Molecules", ParentID=molecule.ID)
    follow.save()

    generate_comment(main_user, sequence_id)
    generate_comment(competitor_user, sequence_id, "My #sequence produces a better yield")

    generate_private_sequence(main_user, molecule.ID)
    generate_private_sequence(main_user, molecule.ID, False)

    for x in xrange(PAGINATION_SIZE+2):
        sequence_id = generate_sequence(main_user, molecule.ID)
        sequence = Sequence.query.filter_by(SequenceID=sequence_id).first()
        sequence.StartingActivity = 21.33
        sequence.Yield = 12.55
        sequence.SpecificActivity = 20.3
        sequence.NumberOfSteps = 20
        sequence.SynthesisTime = 400
        sequence.save()
        generate_comment(main_user, competitor_sequence, "Testing Pagination size %i" % x)

    image_comment = Comment(ParentID=1,Type='Sequences',RenderType='image',Message='',UserID=main_user)
    image_comment.save()

    data = open(os.path.join("seeds", "molecule.jpeg"), 'r')
    data = data.read()

    image = SequenceAttachment(ParentID=image_comment.CommentID,Type='comments',Attachment=data)
    image.save()

    generate_unique_downloads()

    generate_issues()

    time.sleep(15)
    generate_issues()


if __name__ == "__main__":
    seed_data()
