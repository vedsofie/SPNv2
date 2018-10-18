import modules.database
from models.sequence import Sequence
from models.user import User
from sobject import SObject, ValidationException
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, or_
from sqlalchemy.orm import relationship, backref, validates
import base64
from sqlalchemy.ext.hybrid import hybrid_property
db = modules.database.get_db()

class Account(SObject, db.Model):
    __tablename__ = "Account"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description  = db.Column( db.String(500) )
    _image = db.Column("image", db.Binary())
    primary_contact_id = db.Column(db.Integer, ForeignKey('user.UserID'))
    primary_contact = relationship('User', foreign_keys=[primary_contact_id])
    City = db.Column(db.String(100))
    State = db.Column(db.String(100))
    ZipCode = db.Column(db.String(20))
    Address = db.Column(db.String(100))
    Latitude = db.Column(db.Float())
    Longitude = db.Column(db.Float())
    LabName = db.Column(db.String(100))
    PrincipalInvestigatorID = db.Column(db.Integer, ForeignKey('user.UserID'))
    principal_investigator = relationship("User", foreign_keys=[PrincipalInvestigatorID])
    SFDC_ID = db.Column(db.String(30))
    Pharma = Column(db.Boolean)

    @property
    def Name(self):
        return self.name

    @property
    def sequences(self):
        sequences = Sequence.query.join(User.sequences).filter(User.AccountID==self.id).all()
        return sequences

    @property
    def exclude_columns(self):
        return ['account_number']

    @property
    def sfdc_lookups(self):
        return {"SFDC_ID": {"sObjectType": "Account"}}

    @hybrid_property
    def image(self):
        return self._image

    @image.setter
    def set_image(self, val):
        self._image = base64.b64decode(val) if str(val) != "image" else None

    def basic_query(self, search_text):
        records = self.query.filter(Account.name.like("%" + search_text + "%")).all()
        resp = [{
          "name": rec.name,
          "id": rec.id,
          "url": "/account/%i" % rec.id
        } for rec in records]
        return resp

    def can_save(self, usr):
        if usr and usr.role:
            type = str(usr.role.Type)
            if type == 'super-admin':
                return True
            elif type == 'admin' and usr.AccountID == self.id and self.id is not None:
                return True
            else:
                return False
        else:
            return False

    @validates("name")
    def validate_name(self, key, name):
        assert name is not None, "Organization name is required"
        assert name != "", "Organization name is required"
        return name

    def validate_required_fields(self):
        validations = {"name": self.validate_name}
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

