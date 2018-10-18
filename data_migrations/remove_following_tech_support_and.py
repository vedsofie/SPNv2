from chat_server import db
from models.follower import Follower
from models.forum import Forum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_


forums_to_del = Forum.query.filter(Forum.Subject.in_(['Tech Support',
                                     'Hardware Configurations'])).all()
for forum_to_del in forums_to_del:
    followings_to_del = Follower.query.filter(and_(Follower.ParentID==forum_to_del.ForumID,
                                                    Follower.Type=='Forums')).all()
    for old_following in followings_to_del:
        db.session.delete(old_following)
    db.session.delete(forum_to_del)
db.session.commit()
