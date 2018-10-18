import modules.database
import models.user
import datetime,json
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sqlalchemy.orm import relationship, backref
db = modules.database.get_db()
from sobject import SObject
from reagent import Reagent

class Component(SObject, db.Model):
  """
  Component of a Unit operation
  """
  __tablename__ = "Components"
  ComponentID = Column(Integer, primary_key=True)
  SequenceID = Column(Integer, ForeignKey('Sequences.SequenceID'))
  Order = Column(Integer)
  Type = Column(String(length=20))
  Note = Column(String(length=64))
  Details = Column(String(length=2048))
  sequence = relationship('Sequence', backref=backref('components', cascade="delete"),
          foreign_keys=[SequenceID])

  @staticmethod
  def generate(component_json):
    component = Component()
    for key in component_json:
      value = component_json[key]
      if key == "sequence_id":
          component.SequenceID = value
      elif key == 'order':
          component.Order = value
      elif key == "componenttype":
          component.Type = value
      elif key == "note":
          component.Note = value
      elif key == "details":
          component.Details = json.dumps(value)
    return component

  @property
  def Name(self):
    return self.Type + " " + str(self.ComponentID)

  @property
  def details(self):
      return json.loads(self.Details)

  def to_hash(self):
    columns = [c.name for c in self.__table__.columns]
    dict = self.__dict__
    hash = {}
    for key in columns:
      if key in dict:
        value = dict[key]
        if isinstance(value, datetime.datetime):
          hash[key] = value.__str__()
        elif key == "Details":
          hash[key] = json.loads(value)
        else:
          hash[key] = value

    hash["reagents"] = []

    for reagent in self.reagents:
        hash["reagents"].append( reagent.to_hash() )
    return hash

  @staticmethod
  def do_import(sequence_import,sequence_id=None):
    components = sequence_import['components']
    comps = []
    for component in components:
      comp = Component.generate(component)
      comps.append(comp)
      if sequence_id:
          comp.SequenceID = sequence_id

      db.session.add(comp)

    db.session.commit()

    for index in xrange(len(comps)):
        if "reagents" in components[index]:
            for reagent in components[index]["reagents"]:
                reagent = Reagent.generate(reagent)
                reagent.ReagentID = None
                reagent.ComponentID = comps[index].ComponentID
                db.session.add(reagent)

    return comps

  def basic_query(self, search_text):
      records = self.query.filter(Component.Type.like("%" + search_text + "%")).all()
      resp = [{"name": rec.Type,
               "id": rec.ComponentID,
               "url": "/component/%i" % rec.ComponentID}
              for rec in records]
      return resp

  def as_dict(self):
        """
        Function shall return the
        Components class attributes as a
        Python dictionary object.
        Funciton expects no parameters
        Function returns a Component as a
        dictionary object.
        """
        comp_dict = {}
        comp_dict['componentid'] = self.ComponentID
        comp_dict['order'] = self.Order
        comp_dict['sequenceid'] = self.SequenceID
        comp_dict['type'] = 'component'
        comp_dict['validationerror'] = False
        comp_dict['componenttype'] = self.Type
        comp_dict['note'] = self.Note
        comp_dict['reagents'] = [r.as_dict() for r in self.reagents]
        if self.Type == "CASSETTE":
            current_details = self.details
            if "spe0" not in current_details:
                current_details['spe0'] = ""
            if "spe1" not in current_details:
                current_details["spe1"] = ""
            self.Details = json.dumps(current_details)
        elif self.Type == "TRANSFER":
            current_details = self.details
            if "hplc" in current_details and "starttransferimmediatly" not in current_details["hplc"]:
                if "mode" in current_details["hplc"] and current_details["hplc"]["mode"] == "automatic":
                    current_details["hplc"]["starttransferimmediatly"] = True
                else:
                    current_details["hplc"]["starttransferimmediatly"] = False
            self.Details = json.dumps(current_details)

        comp_dict['details'] = self.details


        return comp_dict


