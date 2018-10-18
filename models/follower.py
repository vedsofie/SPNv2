import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_
from sqlalchemy.orm import relationship, backref
db = modules.database.get_db()
from sobject import SObject


class Follower(SObject, db.Model):
    __tablename__ = "Followers"
    FollowerID = db.Column(Integer, primary_key=True)
    ParentID = db.Column(Integer)
    Type = db.Column(db.String(160))
    EmailSubscribed = db.Column(db.Boolean(), default=True)
    UserID = db.Column(Integer, ForeignKey("user.UserID"))
    user = relationship('User', backref=backref('following', cascade="delete"),
                        foreign_keys=[UserID])

    def __init__(self, **kwargs):
        super(Follower, self).__init__(**kwargs)

    @property
    def polymorphic_lookups(self):
        return {"Type": ["ParentID", ("Sequences", "Molecules", "Comments", "Forums")]}
