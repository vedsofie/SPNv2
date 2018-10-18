#NOET
import os
os.environ['SOFIE_ISSUE_EMAIL_USERS'] = 'justin.catterson@sofiebio.com'
os.environ['SOFIE_BUG_REPORT_EMAIL_ADDRESS'] = 'justin.catterson@sofiebio.com'

import modules.database
from chat_server import email_sender
from models.account import Account, db
from models.user import User
from models.forum import Forum
from models.follower import Follower
import time

class TestEmailGeneration():

    def setUp(self):
        #Turn off for sending emails
        email_sender.send_emails(False)
        self.act = Account(name='The Main Account')
        self.act.save()
        self.field_service_guy = User(Email='justin.catterson@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='fieldservice_username',
                                 password='test',
                                 AccountID=self.act.id)
        self.field_service_guy.save()

        self.inactive_user = User(Email='justin.catterson@gmail.com',
                                    FirstName='Field_First_Name',
                                    LastName='Service_Last_Name',
                                    username='inactive_guy',
                                    password='test',
                                    AccountID=self.act.id,
                                    Active=False)

        os.environ['SOFIE_AUTO_FOLLOWING_USERS'] = ','.join([self.field_service_guy.UserID, self.inactive_user.UserID])

        self.customer = User(Email='justin.catterson@gmail.com',
                        FirstName='Customer_First_Name',
                        LastName='Customer_Last_Name',
                        username='customer_username',
                        password='test',
                        AccountID=self.act.id)
        self.customer.save()

        email_sender.send_emails(False)

    def tearDown(self):
        db.session.delete(self.act)
        db.session.delete(self.field_service_guy)
        db.session.delete(self.customer)
        db.session.commit()

    def test_sfdc_down(self):
        original_sfdc_username = os.getenv("SFDC_USERNAME")
        os.environ['SFDC_USERNAME'] = 'bogus'
        print self.customer.AccountID
        forum = Forum(Type='Issue', UserID=self.customer.UserID, AccountID=self.customer.AccountID)
        forum.save()
        print 'Sleeping to ensure time for SFDC to respond or not'
        time.sleep(10)
        os.environ['SFDC_USERNAME'] = original_sfdc_username
        db.session.delete(forum)
        db.session.commit()

        # Assert SOFIE_ISSUE_EMAIL_USERS is emailed the error
        # Assert
        print 'ok'

    def test_sfdc_case_creation(self):
        forum = Forum(Type='Issue', UserID=self.customer.UserID, AccountID=self.customer.AccountID)
        forum.save()

        follow = Follower(Type="Forums",ParentID=forum.ForumID,UserID=self.customer.UserID)
        follow.save()

        print 'Sleeping to ensure time for SFDC to respond or not'
        time.sleep(20)
        db.session.delete(forum)
        db.session.commit()

        # Assert SOFIE_ISSUE_EMAIL_USERS is emailed the error
        # Assert Customer is emailed b/c they are a follower
        print 'ok'

if __name__ == '__main__':
    unittest.main()
