import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_
from sqlalchemy.orm import relationship, backref
db = modules.database.get_db()
from sobject import SObject


class Notification(SObject, db.Model):
    __tablename__ = "Notifications"
    NotificationID = db.Column(Integer, primary_key=True)
    ParentID = db.Column(Integer)
    FollowerID = db.Column(Integer, ForeignKey("Followers.FollowerID"))
    Type = db.Column(db.String(160))
    UserID = db.Column(Integer, ForeignKey("user.UserID"))
    user = relationship('User', backref=backref('notifications', cascade="delete"),
                        foreign_keys=[UserID])
    follower = relationship('Follower', backref=backref('notifications', cascade="delete"),
                            foreign_keys=[FollowerID])

    def __init__(self, **kwargs):
        super(Notification, self).__init__(**kwargs)

    @property
    def polymorphic_lookups(self):
        return {"Type": ["ParentID", ["Comments"]]}
