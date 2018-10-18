import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
import datetime
db = modules.database.get_db()
from sobject import SObject

class LabSystem(SObject, db.Model):
    LabSystemID = Column(Integer,primary_key=True)
    Type = Column(String(100))
    AccountID = Column(Integer,ForeignKey('Account.id'), nullable=False)
    Detail = Column(String(length=2048))
    #ControlBox Version, Synth Version, Pyelixys Version
    City = Column(String(200))
    State = Column(String(100))
    Zip = Column(String(30))
    Address = Column(String(300))
    Latitude = Column(db.Float)
    Longitude = Column(db.Float)

    account = relationship('Account', backref=backref('systems',cascade="delete"),
            foreign_keys=[AccountID])
