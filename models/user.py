import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, or_, and_
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
import base64
import os
from datetime import datetime
import email_sender
from flask.ext.bcrypt import Bcrypt
db = modules.database.get_db()
flask_bcrypt = Bcrypt()
from sobject import SObject, ValidationException
SOFIEBIO_USER = int(os.getenv("SOFIEBIO_USERID", 0))
SOFIEBIO_ACCOUNTID = int(os.getenv("SOFIEBIO_ACCOUNTID", 1))

class User(SObject, db.Model):
    __tablename__ = "user"
    UserID = db.Column(Integer, primary_key=True)
    AccountID = db.Column(Integer, ForeignKey('Account.id'))
    RoleID = db.Column(Integer, ForeignKey('Roles.RoleID'))
    username = db.Column(db.String(80), nullable=False, unique=True)
    account = relationship('Account', backref='users',
          foreign_keys=[AccountID])
    _avatar = db.Column("avatar", db.Binary())
    _password = db.Column("password", db.String(100), nullable=False)
    title = db.Column(db.String(100))
    Email = db.Column(db.String(150), nullable=False)
    FirstName = db.Column(db.String(100), nullable=False)
    LastName = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(20))
    ResetCode = db.Column(db.String(100), unique=True)
    ResetDate = db.Column(DateTime)
    SFDC_ID = db.Column(db.String(30))
    Active = db.Column(db.Boolean(), default=True)
    role = relationship('Role', backref='users', foreign_keys=[RoleID])
    TermsAndConditions = db.Column(DateTime)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def create_reset_url(self, send_email=True, do_save=True, reset_expires=True):
        self.ResetCode = uuid.uuid4().hex
        if reset_expires:
            self.ResetDate = datetime.now()
        else:
            self.ResetDate = None
        if do_save:
            self.save()
        if send_email:
            reset_url = "user/password_reset/%s" % self.ResetCode
            email_sender.forgot_your_email(self, reset_url)

    def generate_password(self):
        self.password = uuid.uuid4().hex
        self.create_reset_url(send_email=False, do_save=False, reset_expires=False)

    def re_welcome_email(self):
        self.generate_password()
        self.save()
        email_sender.welcome_user(self)

    @staticmethod
    def authenticate(username, password):
        users = User.query.filter(User.username==username,
                                  User.Active==True)
        if len(users.all()) > 0 and flask_bcrypt.check_password_hash(users.first().password, password ):
          return users.first()
        raise Exception("Username or Password is incorrect")

    def as_dict(self):
        user_dict = {'type': 'user'}
        user_dict['userid'] = self.UserID
        user_dict['username'] = self.username if self.username else ""
        user_dict['accountid'] = self.AccountID
        user_dict['title'] = self.title if self.title else ""
        user_dict['firstname'] = self.FirstName if self.FirstName else ""
        user_dict['lastname'] = self.LastName if self.LastName else ""
        user_dict['email'] = self.Email if self.Email else ""
        user_dict['phone'] = self.Phone if self.Phone else ""
        return user_dict

    @property
    def Name(self):
        return "%s %s" % (self.FirstName, self.LastName)

    @property
    def can_order_products(self):
        account = self.account
        return account and account.SFDC_ID != '' and account.SFDC_ID != None

    @property
    def exclude_columns(self):
        return ['avatar', 'password', 'ResetCode', 'ResetDate', 'TermsAndConditions']

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def set_password(self, val):
        encrypted = flask_bcrypt.generate_password_hash(val)
        self._password = encrypted
        self.ResetCode = None

    @hybrid_property
    def avatar(self):
        return self._avatar

    @avatar.setter
    def set_avatar(self, val):
        self._avatar = base64.b64decode(val) if str(val) != "image" else None

    @property
    def sfdc_lookups(self):
        return {"SFDC_ID": {"sObjectType": "Contact"}}

    def save(self):
        is_new = self.UserID is None
        super(User, self).save()

        primary_usr_not_set = self.account.primary_contact is None
        pi_not_set = self.account.PrincipalInvestigatorID is None
        if primary_usr_not_set or pi_not_set:
            if primary_usr_not_set:
                self.account.primary_contact_id = self.UserID
                self.account.save()
            if pi_not_set:
                self.account.PrincipalInvestigatorID = self.UserID
                self.account.save()

        if is_new:
            email_sender.welcome_user(self)
            self.follow_forums()

    def follow_forums(self):
        from forum import Forum
        from follower import Follower
        exclude_following_list = ['To Approve Molecules']
        forums = Forum.query.filter(or_(and_(Forum.Subject.notin_(exclude_following_list),Forum.AccountID==SOFIEBIO_ACCOUNTID),
                                        and_(Forum.Type=='Issue', Forum.AccountID==self.AccountID)
                                    )).all()
        for forum in forums:
            follower = Follower(UserID=self.UserID, Type=forum.Type, ParentID=forum.ForumID)
            db.session.add(follower)
        db.session.commit()

    def basic_query(self, search_text):
        users = self.query.filter(or_(
                                    User.FirstName.like("%" + search_text + "%"),
                                    User.LastName.like("%" + search_text + "%"))).all()
        resp = [{
          "name": usr.username,
          "id": usr.UserID,
          "url": "/user/%i" % usr.UserID
        } for usr in users]
        return resp

    def can_save(self, running_user):
        usr = running_user
        is_new = self.UserID is None
        if usr and usr['RoleID']:
            from role import Role
            role_type = Role.query.filter_by(RoleID=usr['RoleID']).first().Name
            if not is_new:
                existing_usr = User.query.filter_by(UserID=self.UserID).first()

                if usr['RoleID'] != self.RoleID and usr['UserID'] == self.UserID:
                    return False # cannot edit
            if role_type == "super-admin":
                return True

            new_role_type = Role.query.filter_by(RoleID=self.RoleID).first()
            if new_role_type is None:
                new_role_type = 'standard user'
            else:
                new_role_type = new_role_type.Name
            if role_type == 'admin' and self.AccountID == usr['AccountID'] and (new_role_type == 'admin' or new_role_type == 'standard user'):
                return True
            elif self.UserID == usr['UserID']:
                return True
            else:
                return False
        else:
            return False

    def to_hash(self):
        res = super(User, self).to_hash()
        res['can_order_products'] = self.can_order_products
        res['RoleType'] = self.role.Type if self.role else ""
        return res

    @validates('username')
    def validate_username(self, key, username):
        assert username != "", "Username must be populated"
        assert username is not None, "Username cannot be null"
        existing_usr = User.query.filter_by(username=username).first()
        assert not existing_usr or existing_usr.UserID == self.UserID, "Username \"%s\" has already been taken" % username
        return username

    @validates('Email')
    def validate_email(self, key, address):
        assert address is not None, "Email address cannot be null"
        assert address != "", "Email address cannot be empty"
        return address

    @validates('FirstName')
    def validate_firstname(self, key, firstname):
        assert firstname is not None, "Firstname cannot be null"
        assert firstname != "", "Firstname cannot be empty"
        return firstname

    @validates('LastName')
    def validate_lastname(self, key, lastname):
        assert lastname is not None, "LastName cannot be null"
        assert lastname != "", "LastName cannot be empty"
        return lastname

    @validates('RoleID')
    def validate_role(self, key, roleid):
        assert roleid is not None, "RoleID cannot be null"
        return roleid

    def validate_required_fields(self):
        validations = {"LastName": self.validate_lastname,
                       "FirstName": self.validate_firstname,
                       "Email": self.validate_email,
                       "username": self.validate_username,
                       "RoleID": self.validate_role}
        exceptions = []
        for col in validations:
            function = validations[col]
            val = getattr(self, col, None)
            try:
                function(col, val)
            except AssertionError as e:
                exceptions.append({"field": col, "message": str(e)})
        if len(exceptions) > 0:
            raise ValidationException(exceptions)

