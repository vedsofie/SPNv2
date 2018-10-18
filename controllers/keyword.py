from flask import Blueprint, request, make_response, render_template, session, redirect, url_for, Response, flash
from models.keyword import Keyword, db
from sqlalchemy import and_
import json

keywordcontroller = Blueprint("keywordcontroller", __name__,url_prefix="/keyword")

@keywordcontroller.route("/", methods=["POST"])
def create_keywords():
    keywords = request.json['keywords']
    for key in keywords:
        if "KeywordID" in key:
            if "CreationDate" in key:
                del key['CreationDate']
            keyw = Keyword.query.filter_by(KeywordID=key['KeywordID']).first()
            keyw.merge_fields(**key)
        else:
            keyw = Keyword()
            keyw.merge_fields(**key)
            keyw.validate_required_fields()

        db.session.add(keyw)
    db.session.commit()
    return "OK"

@keywordcontroller.route("/<keyword_type>/<int:parent_id>/", methods=["GET"])
def get_keywords_for(keyword_type, parent_id):
    keywords = Keyword.query.filter(and_(Keyword.Type==keyword_type,Keyword.ParentID==parent_id)).all()
    resp = [keyword.to_hash() for keyword in keywords]
    return Response(json.dumps(resp), content_type='application/json')

@keywordcontroller.route("/delete", methods=["POST"])
def delete_keywords():
    keywords = request.json['keywordIds']
    keywords = [keyword for keyword in keywords]
    keys = Keyword.query.filter(Keyword.KeywordID.in_(keywords)).all()
    for key in keys:
        db.session.delete(key)
    db.session.commit()
    return "OK"
