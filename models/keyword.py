import modules.database
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine, ForeignKey, LargeBinary, event, and_
from sqlalchemy.orm import relationship, backref, validates

db = modules.database.get_db()
import modules.ml_stripper as ml_stripper

from sobject import SObject


class Keyword(SObject, db.Model):
    __tablename__ = 'Keywords'
    KeywordID = db.Column(db.Integer, primary_key=True)
    Keyword = db.Column(db.String(160))
    ParentID = db.Column(db.Integer)
    Type = db.Column(db.String(160))
    CreationDate = db.Column(db.DateTime, default=datetime.datetime.now)
    Category = db.Column(db.String(160))
    DisplayFormat = db.Column(db.String(160))

    @staticmethod
    def add_search_word(searched_word, search_type=""):
        if searched_word:
            searched_word = str(searched_word)
            key = Keyword.query.filter_by(Keyword=searched_word).first()
            if not key:
                keyword = Keyword(Keyword=searched_word, Type="Search-%s" % search_type)
                keyword.save()

    @validates("Keyword")
    def validate_keyword(self, key, keyword):
        return ml_stripper.strip_tags(keyword)

    @validates("DisplayFormat")
    def validate_display_format(self, key, display_format):
        return ml_stripper.sanitize_html(display_format)

    @property
    def polymorphic_lookups(self):
        return {"Type": ["ParentID", ("Sequences", "Molecules", "Comments")]}

    def validate_required_fields(self):
        pass
