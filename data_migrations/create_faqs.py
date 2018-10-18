from chat_server import db
from models.forum import Forum
from models.user import User
from models.follower import Follower



faqs = Forum()
faqs.Subject = "FAQ"
faqs.Subtitle = "Frequently Asked Questions"
faqs.AccountID = 1
faqs.save()


users = User.query.all()
for user in users:
    follower = Follower(UserID=user.UserID, Type="Forums", ParentID=faqs.ForumID)
    db.session.add(follower)

db.session.commit()
