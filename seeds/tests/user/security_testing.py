from chat_server import email_sender
from models.account import Account, db
from seeds.testing_utils import TestingUtils

#from email_sender import emails_skipped
import generate_db
import unittest
from copy import deepcopy
from models.role import Role

from models.user import User

class SecurityTesting(TestingUtils):

    def setUp(self):
        generate_db.drop_database()
        generate_db.generate_database()
        self.generate_roles()
        email_sender.send_emails(False)

        self.act = Account(name='The Sofie Account')
        self.act.save()

        self.other_act = Account(name='The Other guy')
        self.other_act.save()

        self.super_admin_usr = User(Email='elixys_field_service@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='fieldservice_username',
                                 password='test',
                                 AccountID=self.act.id,
                                 RoleID=self.super_admin.RoleID)

        self.admin_usr = User(Email='elixys_field_service@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='admin',
                                 password='test',
                                 AccountID=self.act.id,
                                 RoleID=self.admin.RoleID)

        self.std_user = User(Email='elixys_field_service@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='standard',
                                 password='test',
                                 AccountID=self.act.id,
                                 RoleID=self.chemist.RoleID)
        self.super_admin_usr.save()
        self.admin_usr.save()
        self.std_user.save()
        #Turn off for sending emails

        self.other_act_std_user = User(Email='elixys_field_service@gmail.com',
                                 FirstName='Field_First_Name',
                                 LastName='Service_Last_Name',
                                 username='otherGuy',
                                 password='test',
                                 AccountID=self.other_act.id,
                                 RoleID=self.chemist.RoleID)
        self.other_act_std_user.save()
        email_sender.send_emails(False)

    def tearDown(self):
        db.session.close()

    def test_admin_cannot_change_their_own_role(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.admin_usr.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.super_admin_usr.RoleID
        can_update = do_create(usr, self.admin_usr)
        self.assertEquals(False, can_update, 'We expect no one to be able to edit their own role')

    def test_super_admin_cannot_change_their_own_role(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.super_admin_usr.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.admin.RoleID
        running_user = User.query.filter_by(UserID=self.super_admin_usr.UserID).first()
        can_update = do_create(usr, running_user)
        self.assertEquals(False, can_update, 'We expect no one to be able to edit their own role')

    def test_standard_user_cannot_change_their_own_role(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.std_user.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.admin.RoleID
        can_update = do_create(usr, self.std_user)
        self.assertEquals(False, can_update, 'We expect no one to be able to edit their own role')

    def test_super_admin_can_edit_roles(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.other_act_std_user.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.admin.RoleID
        running_user = User.query.filter_by(UserID=self.super_admin_usr.UserID).first()
        can_update = do_create(usr, running_user)
        self.assertNotEquals(True, can_update, 'We expect super admins to be able to edit users roles')

    def test_admin_cannot_edit_user_role_to_super_admin(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.std_user.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.super_admin.RoleID
        running_user = User.query.filter_by(UserID=self.admin_usr.UserID).first()
        can_update = do_create(usr, running_user)
        self.assertEquals(False, can_update, 'We expect admins to not be able to give more permission than admin')

    def test_admin_can_edit_user_role_to_admin(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.std_user.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.admin.RoleID
        running_user = User.query.filter_by(UserID=self.admin_usr.UserID).first()
        can_update = do_create(usr, running_user)
        self.assertNotEquals(False, can_update, 'We expect admins to be able to change a user to be an admin so long as they belong to the same Account')

    def test_admin_cannot_edit_user_role_when_not_belonging_to_same_account(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.other_act_std_user.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['RoleID'] = self.admin.RoleID
        running_user = User.query.filter_by(UserID=self.admin_usr.UserID).first()
        can_update = do_create(usr, running_user)
        self.assertEquals(False, can_update, 'We expect admins to NOT be able to edit users belonging to a different account')

    def test_admin_cannot_change_user_to_belong_to_their_account(self):
        from controllers.user import do_create
        to_edit_usr = User.query.filter_by(UserID=self.other_act_std_user.UserID).first()
        usr = to_edit_usr.to_hash()
        usr['AccountID'] = self.admin_usr.AccountID
        running_user = User.query.filter_by(UserID=self.admin_usr.UserID).first()
        can_update = do_create(usr, running_user)
        self.assertEquals(False, can_update, 'We expect admins to NOT be able to edit users belonging to a different account')

    def test_other_users_cannot_edit_passwords_of_others(self):
            from controllers.user import do_create
            to_edit_usr = User.query.filter_by(UserID=self.other_act_std_user.UserID).first()
            original_pass = to_edit_usr.password
            usr = to_edit_usr.to_hash()

            usr['password'] = 'newPasswordHack'
            running_user = User.query.filter_by(UserID=self.super_admin_usr.UserID).first()
            can_update = do_create(usr, running_user)
            the_updated_usr = can_update
            self.assertNotEquals(False, can_update, 'We expect the save to happen still, but with no effect on the password')
            self.assertEquals(the_updated_usr.password, original_pass, 'We do not expect anyone to be able to edit your password besides you')

    def test_user_can_edit_their_password(self):
            from controllers.user import do_create
            to_edit_usr = User.query.filter_by(UserID=self.other_act_std_user.UserID).first()
            original_pass = to_edit_usr.password
            usr = to_edit_usr.to_hash()

            usr['password'] = 'newPasswordHack'
            running_user = User.query.filter_by(UserID=self.other_act_std_user.UserID).first()
            can_update = do_create(usr, running_user)
            the_updated_usr = can_update
            self.assertNotEquals(False, can_update, 'We expect users to be able to change their own passwords')
            self.assertNotEquals(the_updated_usr.password, original_pass, 'We do not expect anyone to be able to edit your password besides you')

    def test_admin_user_can_create_other_users_of_same_account(self):
            from controllers.user import do_create
            to_copy_usr = User.query.filter_by(UserID=self.admin_usr.UserID).first()
            usr = to_copy_usr.to_hash()
            del usr['UserID']
            usr['username'] = usr['username'] + 'd'

            can_update = do_create(usr, to_copy_usr)
            created_user = can_update
            self.assertNotEquals(False, can_update, 'We expect admin users to be able to create other users of the same type')
            self.assertNotEquals(created_user.UserID, None, 'We do not expect anyone to be able to edit your password besides you')

    def test_standard_user_cannot_create_other_users(self):
            from controllers.user import do_create
            to_copy_usr = User.query.filter_by(UserID=self.std_user.UserID).first()
            usr = to_copy_usr.to_hash()
            del usr['UserID']
            usr['username'] = usr['username'] + 'd'

            can_update = do_create(usr, to_copy_usr)
            self.assertEquals(False, can_update, 'We expect standard users to NOT be able to create a user')

if __name__ == "__main__":
    unittest.main()
