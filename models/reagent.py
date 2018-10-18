import modules.database
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
db = modules.database.get_db()
from sobject import SObject


class Reagent(SObject, db.Model):
    """
    Reagent Object
    """
    ReagentID = Column(Integer, primary_key=True)
    ComponentID = Column(Integer, ForeignKey('Components.ComponentID'))
    Position = Column(String(length=2))
    Name = Column(String(length=64))
    Description = Column(String(length=255))
    component = relationship('Component',
            primaryjoin="Component.ComponentID==Reagent.ComponentID",
            backref=backref('reagents', cascade="delete"),
            uselist=False)


    @staticmethod
    def generate(json):
        reg = Reagent()
        if 'position' in json:
            reg.Position = json['position']
        if 'reagentid' in json:
            reg.ReagentID = json['reagentid']
        if 'name' in json:
            reg.Name = json['name']
        if 'description' in json:
            reg.Description = json['description']
        return reg

    def as_dict(self):
        """
        Function shall convert the
        reagent's properties as a
        python dictionary and return the
        dictionary.
        Function expects no parameters.
        Function returns a dictionary object.
        """
        reagent_dict = {}
        #reagent_dict['type'] = 'reagent'
        reagent_dict['reagentid'] = self.ReagentID
        #reagent_dict['componentid'] = self.ComponentID
        reagent_dict['position'] = self.Position
        reagent_dict['name'] = self.Name
        #reagent_dict['namevalidation'] = 'type=string; required=true'
        reagent_dict['description'] = self.Description
        #reagent_dict['descriptionvalidation'] = 'type=string'
        return reagent_dict