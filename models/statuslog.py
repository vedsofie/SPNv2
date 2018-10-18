import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
import json
from datetime import datetime
db = modules.database.get_db()
from sobject import SObject

class StatusLog(SObject, db.Model):
    """
    StatusLog Object
    """
    __tablename__ = 'StatusLog'
    StatusLogID = Column(Integer, primary_key=True)
    Timestamp = Column(DateTime, default=datetime.now)
    StatusString = Column(String(length=21845)) #max str len is 21845 for sqlalchemy (use Text type if larger)
    SequenceID = Column(Integer,ForeignKey('Sequences.SequenceID'))
    sequence = relationship('Sequence', backref='logs',
                            foreign_keys=[SequenceID])

    def __repr__(self):
        return '<StatusLog(%s,%s)>' % (self.StatusLogID, self.SequenceID)

    def as_dict(self):
        try:
            status_dict = json.loads(self.StatusString)
            return status_dict

        except:
            print "Error: No JSON object could be decoded from the StatusString"
            return None
