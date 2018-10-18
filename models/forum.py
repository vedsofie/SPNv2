import modules.database
import modules.sfdc as sfdc
import os
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_
from sqlalchemy.orm import relationship, backref
import threading
db = modules.database.get_db()
from sobject import SObject
import base64
import datetime
import email_sender
SOFIEBIO_USERID = int(os.getenv("SOFIEBIO_USERID"))

class Forum(SObject, db.Model):
    __tablename__ = "Forums"
    ForumID = db.Column(Integer, primary_key=True)
    Subject = db.Column(db.String(3000))
    Subtitle = db.Column(db.String(3000))
    Type = db.Column(db.String(30))
    AccountID = db.Column(Integer, ForeignKey("Account.id"))
    UserID = db.Column(Integer, ForeignKey("user.UserID"))
    Color = Column(db.String(8))
    ReadOnly = Column(db.Boolean)
    account = relationship('Account', backref=backref('forums', cascade="delete"),
                        foreign_keys=[AccountID])
    user = relationship('User', backref='users', foreign_keys=[UserID])
    SFDC_ID = db.Column(db.String(30))
    CreationDate = db.Column(DateTime, default=datetime.datetime.now)
    ClosedDate = db.Column(DateTime, default=None)
    CaseNumber = db.Column(db.String(50))

    def __init__(self, **kwargs):
        super(Forum, self).__init__(**kwargs)

    @property
    def random_color_fields(self):
        return set(["Color"])

    @property
    def Name(self):
        return self.Subject

    def save(self, sfdc_data=None):
        is_new = self.ForumID is None
        super(Forum, self).save()
        if self.is_issue and is_new:
            self.create_salesforce_case(sfdc_data)

    @property
    def is_issue(self):
        return self.Type == 'Issue'

    @property
    def sfdc_lookups(self):
        return {"SFDC_ID": {"sObjectType": "Case", "QueryFields": "CaseNumber", "FilterField": "CaseNumber"}}

    def create_salesforce_case(self, sfdc_data):
        def create(forum_id, sfdc_data):
            if sfdc_data is None:
                print 'no sfdc data'
                return
            assistance_request = str(sfdc_data['assistanceRequest'])
            support_request = str(sfdc_data['instrument'])
            elixys_version = str(sfdc_data['elixysVersion'])

            original_subject = self.Subject
            forum = Forum.query.filter(Forum.ForumID == forum_id).first()

            try:
                sf = sfdc.get_instance()
                user = forum.user
                account_id = user.account.SFDC_ID
                contact_id = user.SFDC_ID
                case_details = {'Description': self.Subtitle,
                                "Subject": self.Subject,
                                "Origin": "Web",
                                "SuppliedEmail": user.Email,
                                "AccountID": account_id,
                                "ContactID": contact_id,
                                "Support_Request__c": support_request,
                                "Assistance_Request__c": assistance_request,
                                "Elixys_Version__c": elixys_version}
                response = sf.Case.create(case_details)
                sf_case_id = response['id']
                forum.SFDC_ID = sf_case_id

                sf_case = sf.Case.get(sf_case_id)
                case_number = sf_case['CaseNumber']
                forum.CaseNumber = case_number

                forum.save()

                from comment import Comment
                from sequenceattachment import SequenceAttachment

                comment_attachments = Comment.query.filter(and_(Comment.ParentID==forum.ForumID,
                                                                Comment.Type=='Forums')).all()
                for comment_attached in comment_attachments:
                    if comment_attached.RenderType != 'text' and comment_attached.RenderType is not None and comment_attached.RenderType != '':
                        attachment = SequenceAttachment.query.filter(and_(SequenceAttachment.Type=='comments',
                                                                          SequenceAttachment.ParentID==comment_attached.CommentID)).first()
                        if attachment:
                            attachment.create_case_attachment(sf_case_id)

                comment = Comment(Type='Forums',\
                                  ParentID=forum.ForumID,\
                                  UserID=SOFIEBIO_USERID,\
                                  RenderType='text',\
                                  Message='Thank-you %s, case #%s has been assigned to you. \n You will be contacted within 48 business hours by an ELIXYS support team-member' % (user.Name, case_number))
                comment.save()



            except Exception as e:
                err = str(e) + "\n Please reset your SFDC credentials"
                email_sender.auto_report_bug(err)
            finally:
                email_sender.report_issue(forum, original_subject)

        create_thread = threading.Thread(target=create, args=(self.ForumID,sfdc_data))
        create_thread.start()

    def close_salesforce_case(self):
        def create(forum_id):
            forum = Forum.query.filter(Forum.ForumID == forum_id).first()
            try:
                sf = sfdc.get_instance()
                response = sf.Case.update(str(forum.SFDC_ID), {'Status': 'closed'})
                case = sf.Case.get(str(forum.SFDC_ID))
                forum.ClosedDate = case['ClosedDate']
                forum.save()
                print response
            except Exception as e:
                print "what??"
                err = str(e) + "\n Please reset your SFDC credentials"
                email_sender.auto_report_bug(err)

        create_thread = threading.Thread(target=create, args=(self.ForumID,))
        create_thread.start()
