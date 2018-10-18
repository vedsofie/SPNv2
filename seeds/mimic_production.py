import generate_db
from chat_server import email_sender
email_sender.send_emails(False)
from models.account import Account, db
from models.forum import Forum
from models.role import Role
from models.molecule import Molecule
from models.sequence import Sequence
from models.follower import Follower
from models.keyword import Keyword
from models.sequenceattachment import SequenceAttachment
from models.labsystem import LabSystem
from models.uniquesequencedownload import UniqueSequenceDownload
from models.user import User
from models.comment import Comment
import requests
import os
authorization = os.getenv("SPN_AUTH")
os.environ['SFDC_USERNAME'] = 'lksdasdlkjsdfa'

def generate_user(account_id, username,roleid):
    usr = User(username=username,password='test',RoleID=roleid,title='Users Title',AccountID=account_id,Email="test@test.com",LastName="LastName", FirstName="FirstName")
    usr.save()
    uid = usr.UserID
    #uid = User.create(username, account_id, "test", "test", title="Users Title", email="test@test.com", first_name="FirstName", last_name="LastName")
    return uid

def generate_roles():
    admin = Role(Type='admin')
    admin.save()
    super_admin = Role(Type='super-admin')
    super_admin.save()
    chemist = Role(Type='standard user')
    chemist.save()
    return (chemist, admin, super_admin)

def create_accounts():
    account_ids = {}
    accounts = requests.get('http://www.sofienetwork.com/account/',
                            headers={'Accept': 'json',\
                                     'Authorization': authorization})
    accounts = accounts.json()

    for account in accounts:
        try:
            account_json = account
            account_id = account_json['id']
            del account_json['sequence_count']
            del account_json['id']
            del account_json['PrincipalInvestigatorID']
            del account_json['primary_contact_id']
            account = Account(**account_json)

            res = requests.get('http://www.sofienetwork.com/account/%i/logo/' % account_id, headers={'Authorization': authorization})
            account._image = res.content
            account.save()
            print account.id
            account_ids[account_id] = account.id
        except Exception as e:
            print str(e)
            db.session.rollback()
    return account_ids

def create_users(account_ids):
    user_ids = {}
    for account_id in account_ids:
        res = requests.get('http://www.sofienetwork.com/account/%i/users' % account_id,\
                           headers={'Accept': 'application/json',\
                                    'Authorization': authorization})
        users = res.json()

        for user in users:
            try:
                spn_id = user['UserID']
                del user['RoleType']
                del user['UserID']
                usr = User(**user)
                usr.password = 'test'
                usr.AccountID = account_ids[account_id]
                res = requests.get('http://www.sofienetwork.com/user/%i/avatar' % spn_id, headers={'Authorization': authorization})
                usr._avatar = res.content
                usr.save()
                print 'Creating User %s' % usr.UserID
                user_ids[spn_id] = usr.UserID
            except Exception as e:
                print str(e)
                print 'user insertion error'
                db.session.rollback()
    return user_ids

def create_molecules(user_ids):
    molecule_sofie_id = {}

    for x in xrange(1, 30):
        res = requests.get('http://www.sofienetwork.com/probe/%i/' % x, \
                           headers={'Accept': 'application/json', 'Authorization': authorization})
        try:
            molecule_json = res.json()
            spn_id = molecule_json["ID"]
            del molecule_json['ID']
            user_id = molecule_json['UserID']
            molecule_json['UserID'] = user_ids[user_id] if user_id in user_ids else None
            molecule = Molecule(**molecule_json)
            res = requests.get('http://www.sofienetwork.com/probe/%i/image/' % x, headers={'Authorization': authorization})
            molecule._Image = res.content
            molecule.save()
            print molecule.ID
            molecule_sofie_id[spn_id] = molecule.ID

            res = requests.get('http://www.sofienetwork.com/keyword/Molecules/%i/' % x, headers={'Authorization': authorization})
            keywords = res.json()
            for keyword in keywords:
                del keyword['CreationDate']
                del keyword['KeywordID']
                key = Keyword(**keyword)
                key.ParentID = molecule.ID
                key.save()
        except Exception as e:
            print str(e)
            print 'molecule insertion error'
            db.session.rollback()
    return molecule_sofie_id

def create_sequences(account_ids, user_ids, molecule_ids):
    sequence_ids = {}
    for account_id in account_ids:
        res = requests.get('http://www.sofienetwork.com/account/%i/sequences' % account_id,\
                           headers={'Accept': 'application/json',\
                                    'Authorization': authorization})
        sequences_json = res.json()
        for sequence_json in sequences_json:
            molecule_id = sequence_json['MoleculeID']
            user_id = sequence_json['UserID']
            if molecule_id in molecule_ids:
                sequence_json['MoleculeID'] = molecule_ids[molecule_id]
                seq_id = sequence_json['SequenceID']
                del sequence_json['SequenceID']
                del sequence_json['CreationDate']
                del sequence_json['TermsAndConditions']
                try:
                    sequence = Sequence()
                    sequence_json['UserID'] = user_ids[sequence_json['UserID']]
                    sequence_json['MoleculeID'] = molecule_ids[sequence_json['MoleculeID']]
                    sequence.merge_fields(**sequence_json)
                    sequence.save()
                    sequence_ids[seq_id] = sequence.SequenceID
                except Exception as e:
                    print 'sequence insertion error'
                    print str(e)
                    db.session.rollback()
    return sequence_ids

"""
def generate_forums(accountid):
    forums = [Forum(Subject="General", Color="#7993F2", AccountID=accountid),
              Forum(Subject="Wish List", Color="#F2C179", AccountID=accountid),
              Forum(Subject='To Approve Molecules', Color="#F2C179", AccountID=accountid)]
    for forum in forums:
        forum.AccountID = accountid
        db.session.add(forum)
    db.session.commit()
"""
def generate_forums(user_ids, account_ids):
    res = requests.get('http://www.sofienetwork.com/admin/Forums/records',
                       headers={'Accept': 'application/json',
                                'Authorization': authorization})

    forums = res.json()
    follower_ids = {}

    for forum in forums:
        forum_id = forum['ForumID']
        del forum['ForumID']

        f = Forum(**forum)
        if f.UserID in user_ids:
            f.UserID = user_ids[f.UserID]
        else:
            f.UserID = None

        if f.AccountID in account_ids:
            f.AccountID = account_ids[f.AccountID]
        else:
            f.AccountID = None
        f.save()
        follower_ids[forum_id] = f.ForumID
    return follower_ids


def generate_followings(user_ids, following_types_to_key):
    res = requests.get('http://www.sofienetwork.com/admin/Followers/records',
                       headers={'Accept': 'application/json',
                                'Authorization': authorization})
    followings = res.json()
    for follower in followings:
        follower_id = follower['FollowerID']
        del follower['FollowerID']
        f = Follower(**follower)
        if f.UserID in user_ids:
            f.UserID = user_ids[f.UserID]
        else:
            f.UserID = None

        if f.Type in following_types_to_key:
            keys = following_types_to_key[f.Type]
            if f.ParentID in keys:
                f.ParentID = keys[f.ParentID]
            else:
                f.ParentID = None
        else:
            f.ParentID = None
        f.save()

import pdb
def routine():
    generate_db.generate_database()
    generate_roles()

    account_ids = create_accounts()
    user_ids = create_users(account_ids)
    molecule_ids = create_molecules(user_ids)
    sequence_ids = create_sequences(account_ids, user_ids, molecule_ids)
    forum_ids = generate_forums(user_ids, account_ids)
    generate_followings(user_ids, {'Forums': forum_ids, 'Molecules': molecule_ids, 'Sequences': sequence_ids, 'Comments': {}})

if __name__ == '__main__':
    routine()

