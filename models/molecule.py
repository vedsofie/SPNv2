import modules.database
import datetime
from follower import Follower
import requests
db = modules.database.get_db()
from sqlalchemy import Column, and_, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event
from sobject import SObject, ValidationException
import requests
from sqlalchemy.orm import relationship, backref, validates
import base64
import json
import modules.ml_stripper as ml_stripper
from sqlalchemy.ext.hybrid import hybrid_property
import os

TO_APPROVE_ID = os.getenv("APPROVAL_PROCESS_LIST", None)

class Molecule(SObject, db.Model):
    __tablename__ = "Molecules"
    ID = Column(Integer, primary_key=True)
    Formula = Column(db.String(300))
    CID = Column(Integer, unique=True)
    CAS = Column(db.String(300), unique=True)
    Name = Column(db.String(300))
    DisplayFormat = db.Column(db.String(300))
    Description = db.Column(db.String(length=1080))
    _Image = Column("Image", db.Binary())
    Color = Column(db.String(8))
    Isotope = Column(db.String(length=100))
    Approved = Column(db.Boolean, default=True)
    UserID = db.Column(Integer, ForeignKey('user.UserID'))

    def __init__(self, **kwargs):
        super(Molecule, self).__init__(**kwargs)

    def find_name(self):
        name = ""
        if self.CID:
            url = "http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/description/JSON" % str(self.CID)
            resp = requests.get(url);
            resp = resp.json()['InformationList']['Information']
            if len(resp) > 0:
                name = resp[0]['Title']
        return name

    def save(self):
        is_new = self.ID is None
        super(Molecule, self).save()
        if not self.Approved and TO_APPROVE_ID:
            from comment import Comment
            from forum import Forum
            forum = Forum.query.filter_by(Subject='To Approve Molecules').first()
            msg = "Please review <a href='%s'>%s</a>" % (self.details_url, self.Name)
            comm = Comment(Message=msg, UserID=self.UserID, ParentID=forum.ForumID, Type="Forums", RenderType="html")
            comm.save()

        if is_new:
            follower = Follower(ParentID=self.ID,Type='Molecules',UserID=self.UserID)
            follower.save()


    def autofill(self, get_image=True):
        if not self.Image and get_image:
            self.get_image_from_pubchem()
        if not self.Name:
            self.Name = self.find_name()
        if not self.Description:
            self.Description = self.find_description()
        if not self.Formula:
            self.Formula = self.find_formula()

    @property
    def host_url(self):
        return os.getenv("SOFIE_PROBE_DOMAIN", "http://localhost:8080")

    @property
    def details_url(self):
        return "/probe/%s/" % self.ID

    @hybrid_property
    def Image(self):
        return self._Image

    @Image.setter
    def set_Image(self, val):
        # use the below base64decoder if image is sent using json
        #self._Image = base64.b64decode(val) if str(val) != "image" else None
        #use he below code if the image is sent as a file from an html form
        self._Image = val


    @property
    def image_url(self):
        if self.CID and not self.Image:
            return "http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/PNG" % self.CID
        return ""

    @property
    def exclude_columns(self):
        return ['Image', 'Color']

    @property
    def random_color_fields(self):
        return set(["Color"])

    def basic_query(self, search_text):
        records = self.query.filter(Molecule.Name.like("%" + search_text + "%")).all()
        resp = [{"name": rec.Name,
                 "id": rec.ID,
                 "url": "/probe/%i" % rec.ID}
                for rec in records]
        return resp

    def save_image_from_pubchem(self):
        self.get_image_from_pubchem()
        self.save()

    def get_image_from_pubchem(self):
        if self.CID and self.image_url != "":
            res = requests.get(self.image_url)
            self._Image = res.content

    def find_formula(self):
        if self.CID and not self.Formula:
            url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/property/MolecularFormula/JSON" % self.CID
            resp = requests.get(url)
            pubchem_info = resp.json()
            if 'PropertyTable' in pubchem_info:
                info = pubchem_info['PropertyTable']
                if "Properties" in info:
                    info = info["Properties"][0]
                    return info["MolecularFormula"] if "MolecularFormula" in info else ""

    def find_description(self):
        if self.CID and not self.Description:
            url = "http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/classification/JSON?classification_type=simple" % self.CID
            resp = requests.get(url)
            pubchem_info = resp.json()
            if 'Hierarchies' in pubchem_info:
                info = pubchem_info['Hierarchies']
                if "Hierarchy" in info:
                    info = info['Hierarchy'][0]
                    if 'Node' in info:
                        info = info['Node'][0]
                        if "Information" in info:
                            info = info['Information']
                            if "Description" in info:
                                return info['Description'][0]
        return ""

    def get_keywords(self):
        from keyword import Keyword
        keywords = []
        if self.CID:
            url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/synonyms/JSON" % self.CID
            resp = requests.get(url)
            pubchem_info = resp.json()
            if 'InformationList' in pubchem_info:
                info = pubchem_info['InformationList']
                if 'Information' in info:
                    for pub_info in info['Information']:
                        if "Synonym" in pub_info:
                            for syn in pub_info['Synonym']:
                                syn = syn[0:299]
                                key = Keyword(Type='Molecules', ParentID=self.ID, Keyword=syn, DisplayFormat=syn, Category='Synonym')
                                keywords.append(key)
        return keywords

    def save_synonyms_from_pubchem(self):
        for key in self.get_keywords():
            db.session.add(key)
        db.session.commit()

    @validates("Name")
    def validate_name(self, key, name):
        assert name is not None, "Probe name is required"
        assert name != "", "Probe name is required"
        return ml_stripper.strip_tags(name)

    @validates("DisplayFormat")
    def validate_display_format(self, key, display_format):
        return ml_stripper.sanitize_html(display_format, ['sub', 'em', 'sup', 'span', 'p'])

    @validates("Image")
    def validate_image(self, key, image):
        has_image_already = False
        if self.ID:
            molecule = Molecule.query.filter_by(ID=self.ID).first()
            has_image_already = molecule.Image
        assert has_image_already or image is not None, "Please upload an image of the Probe"
        return image

    @validates("Isotope")
    def validate_isotope(self, key, isotope):
        assert isotope is not None, "Please give the Isotope"
        assert isotope != "", "Please give the Isotope"
        return isotope

    @validates("CID")
    def validate_cid(self, key, cid):
        max_int = 2147483647
        min_int = -2147483648
        if cid is None:
            return None
        assert int(cid) <= 2147483647 and int(cid) >= min_int, "CID must be an integer within range (%s-%s)" % (min_int, max_int)
        if cid:
            duplicate = Molecule.query.filter(and_(Molecule.ID != self.ID, Molecule.CID==cid)).first()
            assert not duplicate, "This probe already exists.  Search for %s" % (duplicate.Name)
        else:
            return None
        return cid

    def can_save(self, user):
        return user.role.Name == 'super-admin'

    @validates("CAS")
    def validate_cas(self, key, cas):
        if cas:
            duplicate = Molecule.query.filter(and_(Molecule.ID != self.ID, Molecule.CAS==cas)).first()
            assert not duplicate, "This probe already exists.  Search for %s" % (duplicate.Name)
        else:
            return None
        return cas

    def validate_required_fields(self):
        validations = {"Name": self.validate_name,
                       "Image": self.validate_image,
                       "Isotope": self.validate_isotope,
                       "CAS": self.validate_cas,
                       "CID": self.validate_cid}
        exceptions = []
        for col in validations:
            function = validations[col]
            val = getattr(self, col, None)
            try:
                print col
                function(col, val)
            except AssertionError as e:
                exceptions.append({"field": col, "message": str(e)})
        if len(exceptions) > 0:
            raise ValidationException(exceptions)

