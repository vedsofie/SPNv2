import modules.database
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_
from sqlalchemy.orm import relationship, backref
db = modules.database.get_db()
from sobject import SObject


class Role(SObject, db.Model):
    __tablename__ = "Roles"
    RoleID = db.Column(Integer, primary_key=True)
    Type = db.Column(db.String(160))

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)

    @property
    def Name(self):
        return self.Type

    def basic_query(self, search_text):
        records = self.query.filter(Role.Type.like("%" + search_text + "%")).all()
        resp = [{
          "name": rec.Type,
          "id": rec.RoleID
        } for rec in records]
        return resp

