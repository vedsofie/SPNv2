from chat_server import db
from models.follower import Follower

for follower in Follower.query.all():
    follower.EmailSubscribed = True
    db.session.add(follower)

db.session.commit()
