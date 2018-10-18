import os
os.environ['SOFIE_ISSUE_EMAIL_USERS'] = 'justin.catterson@sofiebio.com'
os.environ['SOFIE_BUG_REPORT_EMAIL_ADDRESS'] = 'bug_email_address@sofiebio.com'
os.environ['SFDC_USERNAME'] = 'bogus'

import modules.database
from chat_server import email_sender
from models.account import Account, db
from models.user import User
from models.forum import Forum
from models.follower import Follower
from models.role import Role
from models.comment import Comment
import time
from email_sender import emails_skipped
import unittest
from sqlalchemy import or_, and_
from seeds.testing_utils import TestingUtils
import generate_db

class TestFieldServiceFlow(TestingUtils):

    def setUp(self):
        generate_db.drop_database()
        generate_db.generate_database()
        self.generate_roles()
        #Turn off for sending emails
        email_sender.send_emails(False)
        self.act = Account(name='The Sofie Account')
        self.act.save()
        self.field_service_guy = User(Email='elixys_field_service@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='fieldservice_username',
                                 password='test',
                                 AccountID=self.act.id,
                                 RoleID=self.super_admin.RoleID)
        self.field_service_guy.save()

        os.environ['SOFIE_AUTO_FOLLOWING_USERS'] = str(self.field_service_guy.UserID)

        self.customer_act = Account(name='The Customer')
        self.customer_act.save()

        self.customer = User(Email='justin.catterson@gmail.com',
                        FirstName='Customer_First_Name',
                        LastName='Customer_Last_Name',
                        username='customer_username',
                        password='test',
                        AccountID=self.customer_act.id,
                        RoleID=self.chemist.RoleID)
        self.customer.save()

        self.forum = Forum(Subject='To Approve Molecules')
        self.forum.save()

        follower = Follower(Type='Forums',ParentID=self.forum.ForumID,EmailSubscribed=True,UserID=self.field_service_guy.UserID)
        follower.save()

        del emails_skipped[:]


    def tearDown(self):
        pass
        """
        db.session.delete(self.act)
        db.session.delete(self.customer_act)
        db.session.delete(self.field_service_guy)
        db.session.delete(self.customer)
        db.session.delete(self.customer_team_member)'
        roles = [self.admin, self.super_admin, self.chemist]
        for role in self.roles:
            db.session.delete(role)
        db.session.commit()
        """


    def test_sfdc_down(self):
        from controllers.molecule import do_save
        img_file = open('seeds/molecule.jpeg', 'r')
        img = img_file.read()
        img_file.close()
        data = {'Name': 'molecule', 'Isotope': 'fd', "Image": img}
        do_save(user=self.customer, **data)

        #followers = Follower.query.filter(and_(Follower.UserID==self.field_service_guy.UserID)).all()
        comments = Comment.query.filter(and_(Comment.ParentID==self.forum.ForumID,
                                  Comment.Type=='Forums')).all()

        self.assertEqual(1, len(comments), "We expect the to approve molecules list to have one molecule to approve")


        """
        del emails_skipped[:]

        from controllers.issue import generate_issue, do_close_issue
        forum, follow = generate_issue(self.customer, 'Subject', 'Subtitle', 'The Message', 0, 0, None)
        followers = Follower.query.filter(and_(Follower.ParentID==forum.ForumID,
                                               Follower.Type=='Forums')).all()
        print 'Waiting for SFDC to respond from issue creation'
        time.sleep(5)
        self.assertEqual(2, len(emails_skipped), "We expect after to have sent 2 emails %s" % emails_skipped)
        self.assertEqual(emails_skipped[0]['recipients'][0], os.environ['SOFIE_BUG_REPORT_EMAIL_ADDRESS'], 'Since the username for SFDC is incorrect, we expect a notification to be emailed out')
        self.assertEqual(emails_skipped[1]['recipients'][0], os.environ['SOFIE_ISSUE_EMAIL_USERS'], 'Even when the SFDC integration is down, we expect all SOFIE_AUTO_FOLLOWING_USERS members to be notified. Actual %s' % emails_skipped[1]['recipients'])

        self.assertEqual(3, len(followers), "All SOFIE AUTO FOLLOWING USERS Plus all customer team members shall be following the case. %s" % followers)
        followerIds = {}
        for follower in followers:
            followerIds[follower.UserID] = follower

        self.assertIn(self.field_service_guy.UserID, followerIds, "We expect all members in SOFIE_AUTO_FOLLOWING_USERS to automatically follow the case")
        self.assertEqual(True, followerIds[self.field_service_guy.UserID].EmailSubscribed, "We expect SOFIE_AUTO_FOLLOWING_USERS to be subscribed to the emails")
        self.assertIn(self.customer.UserID, followerIds, "We expect the creator of the issue to automatically follow the case")
        self.assertEqual(True, followerIds[self.customer.UserID].EmailSubscribed, "We expect the creator of the issue to be subscribed to the emails")
        self.assertIn(self.customer_team_member.UserID, followerIds, "We expect all team-members of the case to automatically follow the case")
        self.assertEqual(False, followerIds[self.customer_team_member.UserID].EmailSubscribed, "We expect the team members to NOT be emailed automatically")

        do_close_issue(forum.ForumID, self.field_service_guy)
        print 'Waiting for SFDC to respond to updating of the issue'
        time.sleep(5)
        followers = Follower.query.filter(and_(Follower.ParentID==forum.ForumID,
                                               Follower.Type=='Forums')).all()
        self.assertEqual(2, len(followers), "We expect all SOFIE AUTO FOLLOWING USERS to unfollow, but the customers will remain following the case")

        followerIds = {}
        for follower in followers:
            followerIds[follower.UserID] = follower

        self.assertIn(self.customer_team_member.UserID, followerIds, "We expect all team-members to stay following the case")
        self.assertIn(self.customer.UserID, followerIds, "We expect all team-members to stay following the case")

        print 'ok'
        """


if __name__ == '__main__':
    unittest.main()
