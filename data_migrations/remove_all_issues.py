from chat_server import db
from sqlalchemy import or_, and_
from models.follower import Follower
from models.forum import Forum

forums_to_delete = Forum.query.filter(Forum.Type=='Issue').all()
forum_ids = [f.ForumID for f in forums_to_delete]
followers_to_delete = Follower.query.filter(and_(Follower.ParentID.in_(forum_ids),
                                                 Follower.Type == 'Forums')).all()

for follower in followers_to_delete:
    db.session.delete(follower)
db.session.commit()

for forum in forums_to_delete:
    db.session.delete(forum)
db.session.commit()
