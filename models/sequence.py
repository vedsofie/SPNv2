import modules.database
from user import User
from sequenceattachment import SequenceAttachment
from follower import Follower
from sobject import SObject, ValidationException, NoPermissionException
import datetime
from models.component import Component
from models.molecule import Molecule
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_
from sqlalchemy.orm import relationship, backref, validates
import zipfile, os, StringIO,json
from sqlalchemy.ext.hybrid import hybrid_property
db = modules.database.get_db()

class Sequence(SObject, db.Model):
    __tablename__ = "Sequences"
    SequenceID = db.Column(Integer, primary_key=True)
    Name = db.Column(String(length=64))
    Color = Column(db.String(8))
    Comment = db.Column(String(length=255))
    Type = db.Column(String(length=20))
    parentSequenceID = db.Column(Integer)
    parentSequenceName = db.Column(String(length=64))
    CreationDate = db.Column(DateTime, default=datetime.datetime.now)
    UserID = db.Column(Integer, ForeignKey('user.UserID'))
    Valid = db.Column(Boolean, default=False)
    Dirty = db.Column(Boolean, default=False)
    MadeOnElixys = db.Column(Boolean, default=False)
    MoleculeID = db.Column(Integer, ForeignKey('Molecules.ID'))
    molecule = relationship('Molecule', backref=backref('sequences'),
            foreign_keys=[MoleculeID])
    owner = relationship('User', backref=backref('sequences'),
            foreign_keys=[UserID])
    SynthesisTime = db.Column(Integer)
    NumberOfSteps = db.Column(Integer)#Number of Cassettes
    PurificationMethod = db.Column(db.String(30))
    SpecificActivity = db.Column(db.Float)
    StartingActivity = db.Column(db.Float)
    NumberOfRuns = db.Column(Integer)
    StartingActivityStandardDeviation = db.Column(db.Float)
    SpecificActivityStandardDeviation = db.Column(db.Float)
    YieldStandardDeviation = db.Column(db.Float)
    SynthesisTimeStandardDeviation = db.Column(db.Float)
    _TermsAndConditions = db.Column("TermsAndConditions", DateTime)
    Yield = db.Column(db.Float)
    SynthesisModule = db.Column(db.String(35))

    def __init__(self, **kwargs):
        super(Sequence, self).__init__(**kwargs)

    @hybrid_property
    def TermsAndConditions(self):
        if self._TermsAndConditions:
            return self._TermsAndConditions.strftime('%s') * 1000
        return None

    @TermsAndConditions.setter
    def set_terms_and_conditions(self, val):
        if val == self.TermsAndConditions:
            pass
        elif val and val != self.TermsAndConditions:
            dt = datetime.datetime.fromtimestamp(val)
            self._TermsAndConditions = dt
        else:
            self._TermsAndConditions = None

    @property
    def reagents(self):
        reagents = []
        for component in self.components:
            reagents.extend(component.reagents)
        return reagents

    def export(self):
        seq = {"sequence": self.as_dict()}
        seq["components"] = [component.as_dict() for component in self.components]

        seq_name = self.Name
        seq_creation_date = self.CreationDate.date()
        seq_json_file_name = "%s-%s.sequence" % (seq_name, seq_creation_date)

        zip_io = StringIO.StringIO()
        zip_io.write(json.dumps(seq))
        return (seq_json_file_name, zip_io.getvalue())

    @staticmethod
    def generate(sequence_json):
        new_sequence = Sequence()
        #update new sequence with comment / name
        if 'type' in sequence_json:
           new_sequence.Type = sequence_json['type']
        if 'name' in sequence_json['details']:
           new_sequence.Name = sequence_json['details']['name']
        if 'comment' in sequence_json['details']:
           new_sequence.Comment = sequence_json['details']['comment']

        if 'valid' in sequence_json['details']:
           new_sequence.Valid = sequence_json['details']['valid']

        #link new sequence to user
        if 'userid' in sequence_json:
           new_sequence.UserID = sequence_json['userid']

        if 'parent_network_sequenceid' in sequence_json:
            new_sequence.parentSequenceID = sequence_json['parent_network_sequenceid']

        return new_sequence

    def delete_sequence_file(self):
        components_to_delete = Component.query.filter_by(SequenceID=self.SequenceID).all()
        for component in components_to_delete:
            db.session.delete(component)
        for reagent in self.reagents:
            db.session.delete(reagent)
        db.session.commit()

    def delete(self):
        self.delete_sequence_file()
        for attachment in self.attachments:
            db.session.delete(attachment)
        for download in self.downloads:
            db.session.delete(download)
        db.session.delete(self)
        db.session.commit()

    @property
    def exclude_columns(self):
        return ['Color']

    @property
    def following(self):
        following = User.query.join(Follower).filter(and_(Follower.Type == 'Sequence',
                                                       Follower.ParentID == self.SequenceID)).all()
        return following

    @staticmethod
    def do_import(json_sequence, data):
        if "SequenceID" in data:
            seq = Sequence.query.filter_by(SequenceID=data['SequenceID']).first()
        else:
            seq = Sequence.generate(json_sequence['sequence'])
        seq.merge_fields(**data)
        seq.validate_required_fields()
        seq.save()
        return seq

    def save(self):
        is_new = self.SequenceID is None
        super(Sequence, self).save()
        if is_new:
            follower = Follower(ParentID=self.SequenceID,Type='Sequences',UserID=self.UserID)
            follower.save()

    def basic_query(self, search_text):
        records = self.query.filter(Sequence.Name.like("%" + search_text + "%")).all()
        resp = [{"name": rec.Name,
                 "id": rec.SequenceID,
                 "url": rec.details_url}
                for rec in records]
        return resp

    @property
    def details_url(self):
        return "/sequence/%s" % self.SequenceID

    def to_hash(self):
        res = super(Sequence, self).to_hash()

        res['TermsAndConditions'] = self.TermsAndConditions
        #res['Color'] = self.molecule.Color if self.molecule else None
        res['hasReactionScheme'] = self.has_reaction_scheme
        res['IsDownloadable'] = self.downloadable
        seq_user = User.query.filter_by(UserID=self.UserID).first()
        res['SequenceUserFN'] = seq_user.FirstName
        res['SequenceUserLN'] = seq_user.LastName
        res['AccountID'] = seq_user.AccountID
        res['AccountName'] = seq_user.account.name
        mol = Molecule.query.filter_by(ID = self.MoleculeID).first()
        res['MoleculeName'] = mol.DisplayFormat
        return res

    @property
    def has_reaction_scheme(self):
        return self.reaction_scheme is not None

    @property
    def reaction_scheme(self):
        reaction = SequenceAttachment.query.filter(and_(SequenceAttachment.SequenceID==self.SequenceID,
                                                        SequenceAttachment.Type=='ReactionScheme')).first()
        return reaction

    @property
    def downloadable(self):
        return len(self.components) > 0

    @property
    def random_color_fields(self):
        return set(["Color"])

    @validates("Name")
    def validate_name(self, key, name):
        assert name is not None, "Sequence name is required"
        assert name != "", "Sequence name is required"
        return name

    @validates("PurificationMethod")
    def validate_purification_method(self, key, method):
        assert method is not None, "Purification Method is required"
        assert method != "", "Purification Method is required"
        return method

    @validates("SynthesisModule")
    def validate_synthesis_module(self, key, value):
        self.MadeOnElixys = value == 'SOFIE ELIXYS'
        return value

    @validates("MoleculeID")
    def validate_moleculeid(self, key, molecule_id):
        assert molecule_id is not None, "Molecule ID is required"
        from molecule import Molecule
        mole = Molecule.query.filter_by(ID=molecule_id).first()
        assert mole is not None, "Invalid MoleculeID %s" % molecule_id
        return molecule_id

    def can_save(self, user):
        user_role = user.role.Type
        if(self.SequenceID is None or user_role == 'super-admin' or self.UserID == user.UserID or \
          (self.owner.AccountID == user.AccountID and user_role == 'admin')):
            return True

        raise NoPermissionException()


    def validate_required_fields(self):
        validations = {"Name": self.validate_name,
                       "MoleculeID": self.validate_moleculeid,
                       "PurificationMethod": self.validate_purification_method}
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

    def as_dict(self):
        """
        Function shall return the
        Sequences class attributes as a
        Python dictionary object.
        Funciton expects no parameters
        Function returns a Sequence as a
        dictionary object.
        """
        comp_dict = {}
        comp_dict['type'] = self.Type if self.Type else "logged"
        comp_dict['userid'] = 1#self.UserID.  Needs to be the only user that exists in Elixys
        comp_dict['sequenceid'] = self.SequenceID
        comp_dict['parentsequenceid'] = self.parentSequenceID #used for archiving and logging
        comp_dict['parentsequencename'] = self.parentSequenceName #used for archiving and logging

        comp_dict['date'] = self.CreationDate.strftime('%m/%d/%Y')
        comp_dict['time'] = self.CreationDate.strftime('%H:%M.%S')
        comp_dict['details'] = {}
        comp_dict['details']['name'] = self.Name
        comp_dict['details']['comment'] = self.Comment
        comp_dict['details']['valid'] = self.Valid
        comp_dict["hasinstructions"] = len(self.attachments) > 0
        #removed 6/7/2014 by joshua.thompson@sofiebio.com
        #comp_dict['components'] = [comp.as_dict() for comp in self.components]

        comp_dict['checklistid'] = 'none'

        comp_dict['dirty'] = self.Dirty
        return comp_dict
