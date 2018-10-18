import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
import json
from keyword import Keyword
import re
from datetime import datetime
db = modules.database.get_db()
from sobject import SObject

class UniqueSequenceDownload(SObject, db.Model):
    __tablename__ = 'UniqueSequenceDownloads'
    UniqueSequenceDownloadID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(Integer, ForeignKey('user.UserID'))
    SequenceID = db.Column(Integer, ForeignKey('Sequences.SequenceID'))
    sequence = relationship('Sequence', backref=backref('downloads',cascade="delete"),
            foreign_keys=[SequenceID])

    def __init__(self, **kwargs):
        super(UniqueSequenceDownload, self).__init__(**kwargs)

