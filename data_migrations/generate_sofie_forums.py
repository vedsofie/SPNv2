from chat_server import db
from models.forum import Forum
from models.user import User
from models.follower import Follower


def generate_forums(account_id):
    forums = [Forum(Subject="General", Color="#7993F2"),
              Forum(Subject="Wish List", Color="#F2C179"),
              Forum(Subject='To Approve Molecules', Color='#CF79f2')]

    for forum in forums:
        forum.AccountID = account_id
        db.session.add(forum)
    db.session.commit()

def generate_followers():
    users = User.query.all()
    for user in users:
        general = Follower(UserID=user.UserID, Type="Forums", ParentID=1)
        wish_list = Follower(UserID=user.UserID, Type="Forums", ParentID=2)
        db.session.add(general)
        db.session.add(wish_list)
    db.session.commit()


generate_forums(1)
generate_followers()

