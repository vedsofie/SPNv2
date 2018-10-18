import modules.database
import modules.sfdc as sfdc
import threading
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
import json
from sqlalchemy import and_, or_
from keyword import Keyword
import re
from datetime import datetime
db = modules.database.get_db()
from sobject import SObject
import email_sender

class Comment(SObject, db.Model):
    __tablename__ = 'Comments'
    MAX_COMMENT_LENGTH = 3000
    CommentID = db.Column(db.Integer, primary_key=True)
    Message = db.Column(db.String(MAX_COMMENT_LENGTH))
    CreationDate = db.Column(DateTime, default=datetime.now)
    UserID = db.Column(Integer, ForeignKey('user.UserID'))
    ParentID = Column(Integer)
    Type = db.Column(db.String(150))
    user = relationship('User', backref=backref('comments', cascade="delete"),
                        foreign_keys=[UserID])
    RenderType = db.Column(db.String(40))

    def save(self):
        is_new = self.CommentID is None
        super(Comment, self).save()
        from follower import Follower
        if self.Type == 'Comments':
            already_follows = Follower.query.filter(and_(Follower.Type=='Comments',
                                                         Follower.ParentID==self.ParentID,
                                                         Follower.UserID==self.UserID)).first()
            if not already_follows:
                follower = Follower(Type='Comments', ParentID=self.ParentID, UserID=self.UserID)
                follower.save()

        if is_new and self.Type == 'Forums':
            from forum import Forum
            forum = Forum.query.filter(and_(Forum.ForumID==self.ParentID,
                                            Forum.SFDC_ID is not None)).first()
            if forum:
                self.create_case_comment(forum.SFDC_ID)

        if is_new:
            self.notify_followers()

    def notify_followers(self, notify_self=False):
        from follower import Follower
        from notification import Notification
        from forum import Forum
        followings = Follower.query.filter(and_(Follower.Type==self.Type,
                                                Follower.ParentID==self.ParentID)).all()

        if len(followings) > 0:
            if self.Type != 'Comments':
                for following in followings:
                    if following.UserID != self.UserID:
                        note = Notification(UserID=following.UserID,
                                            Type="Comments",
                                            ParentID=self.CommentID,
                                            FollowerID=following.FollowerID)
                        db.session.add(note)
                db.session.commit()

                if self.Type == 'Forums':
                    forum = Forum.query.filter(Forum.ForumID==self.ParentID).first()
                    followers_to_email = [follower for follower in followings if follower.EmailSubscribed is True and \
                                                                                 follower.user.Active is True]
                    user = self.user

                    if forum and forum.Type == 'Issue' and forum.SFDC_ID is not None and forum.SFDC_ID != '':
                        subject = '%s has responded to %s' % (user.Name, forum.Subject)
                        email_sender.send_email_to_issue_followers(self,
                                                                   subject,
                                                                   followers_to_email,
                                                                   user.Email,
                                                                   exclude=[self.UserID])
                    elif forum and forum.Subject == 'To Approve Molecules':
                        email_sender.send_email_to_issue_followers(self,
                                                                   'Please Approve the Molecule',
                                                                   followers_to_email,
                                                                   user.Email)
            else:
                pass

    def notify_self(self):
        from notification import Notification
        from follower import Follower
        follower = Follower.query.filter(and_(Follower.Type==self.Type,
                                              Follower.ParentID==self.ParentID,
                                              Follower.UserID==self.UserID)).first()
        if follower:
            note = Notification(UserID=self.UserID, Type="Comments", ParentID=self.CommentID, FollowerID=follower.FollowerID)
            note.save()

    def basic_query(self, search_text):
        records = self.query.filter(Comment.Message.like("%" + search_text + "%")).all()
        resp = [{"name": rec.Message,
                 "id": rec.CommentID,
                 "url": "/comment/%i" % rec.CommentID}
                for rec in records]
        return resp

    @property
    def polymorphic_lookups(self):
        return {"Type": ["ParentID", ("Sequences", "Molecules", "Comments", "Forums")]}

    def get_render_types(self):
        return ['text', 'html', 'link', 'attachment']

    def create_case_comment(self, sfdc_case_id):
        def create(sfdc_case_id, comment_id):
            comment = Comment.query.filter(Comment.CommentID==comment_id).first()
            sf = sfdc.get_instance()
            if comment.RenderType == '' or comment.RenderType is None or comment.RenderType == 'text' and sfdc_case_id:
                sf.CaseComment.create({'CommentBody': comment.Message, 'ParentId': sfdc_case_id})

        if sfdc_case_id and sfdc_case_id != '':
            create_thread = threading.Thread(target=create, args=(sfdc_case_id, self.CommentID,))
            create_thread.start()

    @staticmethod
    def make_comments(user_id, comment_type, parent_id, message):
        num_comments = len(message) / Comment.MAX_COMMENT_LENGTH
        remainder = len(message) % Comment.MAX_COMMENT_LENGTH
        end_point = 0

        for i in xrange(num_comments):
            start_point = i*Comment.MAX_COMMENT_LENGTH
            end_point = start_point + Comment.MAX_COMMENT_LENGTH
            sub_message = message[start_point:end_point]
            comment = Comment(UserID=user_id, Type=comment_type, ParentID=parent_id, Message=sub_message)
            comment.save()

        if remainder:
            sub_message = message[end_point:len(message)]
            comment = Comment(UserID=user_id, Type=comment_type, ParentID=parent_id, Message=sub_message)
            comment.save()

