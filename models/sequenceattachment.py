import modules.database
import modules.sfdc as sfdc
import base64
from sqlalchemy import Column, Integer, String, Float, Text,DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
import datetime
import threading
db = modules.database.get_db()
from sobject import SObject

class SequenceAttachment(SObject, db.Model):
    SequenceAttachmentID = Column(Integer,primary_key=True)
    SequenceID = Column(Integer,ForeignKey('Sequences.SequenceID'))
    Attachment = Column(LargeBinary)
    CreationDate = Column(DateTime, default=datetime.datetime.now)
    FileName = Column(String(256))
    ContentType = Column(Text)
    Author = Column(String(256))
    Detail = Column(String(length=2048))
    ParentID = Column(Integer)
    Type = db.Column(db.String(150))
    sequence = relationship('Sequence', backref=backref('attachments',cascade="delete"),
            foreign_keys=[SequenceID])

    @property
    def exclude_columns(self):
        return ['Attachment']

    def create_case_attachment(self, sfdc_case_id):
        def create(sfdc_case_id, attachment_id):
            attachment = SequenceAttachment.query.filter_by(SequenceAttachmentID=attachment_id).first()
            sf = sfdc.get_instance()
            if sfdc_case_id and attachment.Attachment:
                sf.Attachment.create({"ParentID": sfdc_case_id,
                                      "Name": attachment.FileName,
                                      "Body": base64.b64encode(attachment.Attachment)})

        create_thread = threading.Thread(target=create, args=(sfdc_case_id, self.SequenceAttachmentID))
        create_thread.start()