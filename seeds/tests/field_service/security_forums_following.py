from chat_server import email_sender
from models.account import Account, db
from seeds.testing_utils import TestingUtils
import os
#from email_sender import emails_skipped
import generate_db
import unittest
from sqlalchemy import or_, and_
from copy import deepcopy
from models.role import Role
from models.forum import Forum
from models.follower import Follower
from models.user import User
from email_sender import emails_skipped

class SecurityForumsTesting(TestingUtils):

    def setUp(self):
        generate_db.drop_database()
        generate_db.generate_database()
        self.generate_roles()
        email_sender.send_emails(False)

        os.environ['SFDC_USERNAME'] = 'bogus'
        self.sofie_act = Account(name='The Sofie Account')
        self.sofie_act.save()

        basic_forums = self.generate_forums(self.sofie_act.id)
        self.all_basic_forums = {forum.ForumID: forum for forum in basic_forums}

        self.sofie_member = User(Email='justin.catterson@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='fieldservice_username',
                                 password='test',
                                 RoleID=self.super_admin.RoleID,
                                 AccountID=self.sofie_act.id)
        self.sofie_member.save()

        self.case_act = Account(name='Case Creation Account')
        self.case_act.save()

        self.case_creator = User(Email='justin.catterson@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='case_creator',
                                 password='test',
                                 RoleID=self.admin.RoleID,
                                 AccountID=self.case_act.id)
        self.case_creator.save()

        self.case_team_member = User(Email='justin.catterson@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='case_team_member',
                                 password='test',
                                 RoleID=self.admin.RoleID,
                                 AccountID=self.case_act.id)
        self.case_team_member.save()

        self.other_act = Account(name='Unrelated Account')
        self.other_act.save()

        del emails_skipped[:]

    def tearDown(self):
        db.session.close()


    def test_new_user_of_different_account_only_follow_sofie_sequences(self):
        from controllers.issue import generate_issue
        from controllers.user import do_create as do_create_user
        self.case_creator = User.query.filter_by(UserID=self.case_creator.UserID).first()
        forum, following = generate_issue(self.case_creator, 'Subject', 'Subtitle', 'message', 0, 0, None, sfdc_data=None)
        new_usr = User(Email='justin.catterson@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='other_guy',
                                 password='test',
                                 RoleID=self.admin.RoleID,
                                 AccountID=self.other_act.id)
        new_usr = do_create_user(new_usr.to_hash(), self.sofie_member)
        all_followings = Follower.query.filter_by(UserID=new_usr.UserID).all()

        self.assertEquals(len(self.all_basic_forums)-1, len(all_followings), "The user should not follow the newly created issue, as the issue does not belong to their organization")
        for new_usr_following in  all_followings:
            self.assertEquals(True, new_usr_following.ParentID in self.all_basic_forums, "The user should not follow the newly created issue, as the issue does not belong to their organization")

    def test_new_user_of_same_account_do_follow_the_issue_sequence(self):
        from controllers.issue import generate_issue
        from controllers.user import do_create as do_create_user
        self.case_creator = User.query.filter_by(UserID=self.case_creator.UserID).first()
        forum, following = generate_issue(self.case_creator, 'Subject', 'Subtitle', 'message', 0, 0, None, sfdc_data=None)
        new_usr = User(Email='justin.catterson@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='other_guy',
                                 password='test',
                                 RoleID=self.admin.RoleID,
                                 AccountID=self.case_act.id)
        new_usr = do_create_user(new_usr.to_hash(), self.sofie_member)
        all_followings = Follower.query.filter_by(UserID=new_usr.UserID).all()
        self.assertEquals(len(self.all_basic_forums), len(all_followings), "The user should follow the newly created issue, as the issue DOES belong to their organization")
        issue_following = Follower.query.filter(and_(Follower.UserID==new_usr.UserID,
                                                     Follower.ParentID==forum.ForumID,
                                                     Follower.Type=='Issue')).all()
        self.assertEquals(1, len(issue_following), 'We expect the newly created user to follow the forum')

if __name__ == "__main__":
    unittest.main()
