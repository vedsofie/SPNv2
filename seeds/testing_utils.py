from models.role import Role
from models.forum import Forum
from chat_server import db
import unittest

class TestingUtils(unittest.TestCase):
    def generate_roles(self):
        self.admin = Role(Type='admin')
        self.admin.save()
        self.super_admin = Role(Type='super-admin')
        self.super_admin.save()
        self.chemist = Role(Type='standard user')
        self.chemist.save()

    def generate_forums(self, accountid):
        forums = [Forum(Subject="General", Color="#7993F2"),
                  Forum(Subject="Wish List", Color="#F2C179"),
                  Forum(Subject='To Approve Molecules', Color="#7993F2")]
        for forum in forums:
            forum.AccountID = accountid
            db.session.add(forum)
        db.session.commit()
        return forums
