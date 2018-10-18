#NOTE THESE TESTS ONLY PASS WHEN EXECUTED SEPERATELY
import os
os.environ['SOFIE_ISSUE_EMAIL_USERS'] = 'justin.catterson@sofiebio.com'
os.environ['SOFIE_BUG_REPORT_EMAIL_ADDRESS'] = 'bug_email_address@sofiebio.com'
original_sfdc_username = os.environ['SFDC_USERNAME']

import modules.database
from chat_server import email_sender
from models.account import Account, db
from models.user import User
from models.forum import Forum
from models.comment import Comment
from models.follower import Follower
from models.role import Role
import time
from email_sender import emails_skipped
import unittest
from sqlalchemy import or_, and_

import generate_db

class TestFieldServiceFlow(unittest.TestCase):

    def generate_roles(self):
        self.admin = Role(Type='admin')
        self.admin.save()
        self.super_admin = Role(Type='super-admin')
        self.super_admin.save()
        self.chemist = Role(Type='standard user')
        self.chemist.save()

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


        self.inactive_user = User(Email='justin.catterson@gmail.com',
                                    FirstName='Field_First_Name',
                                    LastName='Service_Last_Name',
                                    username='inactive_guy',
                                    password='test',
                                    AccountID=self.act.id)

        self.inactive_user.save()

        os.environ['SOFIE_AUTO_FOLLOWING_USERS'] = ','.join([str(self.field_service_guy.UserID),
                                                             str(self.inactive_user.UserID)])


        #os.environ['SOFIE_AUTO_FOLLOWING_USERS'] = str(self.field_service_guy.UserID)

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

        self.customer_team_member = User(Email='justin.catters33on@gmail.com',
                        FirstName='Customer_First_Name',
                        LastName='Customer_Last_Name',
                        username='customer_username2',
                        password='test',
                        AccountID=self.customer_act.id,
                        RoleID=self.chemist.RoleID)
        self.customer_team_member.save()

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
        del emails_skipped[:]
        self.inactive_user.Active = False
        self.inactive_user.save()
        os.environ['SFDC_USERNAME'] = 'bogus'
        from controllers.issue import generate_issue, do_close_issue
        forum, follow = generate_issue(self.customer, 'Subject', 'Subtitle', 'The Message', 0, 0, None,{'assistanceRequest': '',
                                                                                                        'instrument': '',
                                                                                                        'elixysVersion': ''})
        followers = Follower.query.filter(and_(Follower.ParentID==forum.ForumID,
                                               Follower.Type=='Forums')).all()
        print 'Waiting for SFDC to respond from issue creation'
        time.sleep(10)
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
        self.assertEqual(3, len(followers), "We expect all followers to remain after closing")

        followerIds = {}
        for follower in followers:
            followerIds[follower.UserID] = follower

        self.assertIn(self.customer_team_member.UserID, followerIds, "We expect all team-members to stay following the case")
        self.assertIn(self.customer.UserID, followerIds, "We expect all team-members to stay following the case")

        print 'ok'

    def test_sfdc_up(self):
        del emails_skipped[:]
        os.environ['SFDC_USERNAME'] = original_sfdc_username
        from controllers.issue import generate_issue, do_close_issue
        forum, follow = generate_issue(self.customer, 'Subject', 'Subtitle', 'The Message', 0, 0, None,{'assistanceRequest': '',
                                                                                                        'instrument': '',
                                                                                                        'elixysVersion': ''})
        followers = Follower.query.filter(and_(Follower.ParentID==forum.ForumID,
                                               Follower.Type=='Forums')).all()
        print 'Waiting for SFDC to respond from issue creation'
        time.sleep(10)

        self.assertEqual(2, len(emails_skipped), "We expect after to have sent 2 emails %s" % emails_skipped)

        self.assertEqual(emails_skipped[0]['recipients'][0], self.customer.Email, 'When a case number has been generated, we expect the customer to be notified')
        self.assertEqual(emails_skipped[1]['recipients'][0], os.environ['SOFIE_ISSUE_EMAIL_USERS'], 'Even when the SFDC integration is down, we expect SOFIE_ISSUE_EMAIL_USERS to be notified. Actual %s' % emails_skipped[1]['recipients'])

        self.assertEqual(4, len(followers), "All SOFIE AUTO FOLLOWING USERS Plus all customer team members shall be following the case. %s" % followers)
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
        followers = Follower.query.filter(and_(Follower.ParentID==forum.ForumID,
                                               Follower.Type=='Forums')).all()
        self.assertEqual(4, len(followers), "We expect all followers to remain after closing")

        followerIds = {}
        for follower in followers:
            followerIds[follower.UserID] = follower

        self.assertIn(self.customer_team_member.UserID, followerIds, "We expect all team-members to stay following the case")
        self.assertIn(self.customer.UserID, followerIds, "We expect all team-members to stay following the case")

        del emails_skipped[:]

        self.inactive_user.Active = False
        self.inactive_user.save()


        customer_comment = Comment(Message='Testing - Comment from your customer...', UserID=self.customer.UserID, ParentID=forum.ForumID, Type='Forums')
        customer_comment.save()

        time.sleep(10)
        print emails_skipped

        len(emails_skipped[0]['recipients'])
        self.assertEquals(len(emails_skipped[0]['recipients']), 1, "We only expect active users to be emailed")
        self.assertEquals(emails_skipped[0]['recipients'][0], self.field_service_guy.Email, "We only expect active users to be emailed")

        print 'ok'

    def test_double_tapped_team_members_users(self):
        del emails_skipped[:]
        os.environ['SFDC_USERNAME'] = 'bogus'
        from controllers.issue import generate_issue, do_close_issue
        forum, follow = generate_issue(self.inactive_user, 'Subject', 'Subtitle', 'The Message', 0, 0, None,{'assistanceRequest': '',
                                                                                                        'instrument': '',
                                                                                                        'elixysVersion': ''})

        followers = Follower.query.filter(and_(Follower.ParentID==forum.ForumID,
                                             Follower.Type=='Forums'
                    )).all()
        self.assertEqual(2, len(followers), 'We only expect the two users to be following the issue, no users need to be double following.  Expected %s, Actual %s' % (2, len(followers)))



if __name__ == '__main__':
    unittest.main()
