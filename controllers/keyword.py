from flask import Blueprint, request, make_response, render_template, session, redirect, url_for, Response, flash
from models.keyword import Keyword, db
from sqlalchemy import and_
from flask import jsonify
import json
import html2text

keywordcontroller = Blueprint("keywordcontroller", __name__,url_prefix="/keyword")

@keywordcontroller.route("/", methods=["POST"])
def create_keywords():
    keywords = request.json['keywords']
    print keywords
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

@keywordcontroller.route("/save_synonym/<int:parent_id>/", methods=["POST"])
def create_synonyms(parent_id):
    # get form data
    data = request.form
    data = data.to_dict()
    keyw = Keyword()
    keyw.ParentID = parent_id
    keyw.DisplayFormat = data['DisplayFormat']
    keyw.Category = 'Synonym'
    keyw.Type = 'Molecules'
    # change displayformat to normal text
    keyw.Keyword = html2text.html2text(keyw.DisplayFormat)
    keyw.Keyword = keyw.Keyword.strip()
    # save everything
    keyw.save()
    data['ID'] = keyw.KeywordID
    data['Keyword']= keyw.Keyword
    return Response(json.dumps(data), content_type='application/json')

@keywordcontroller.route("/save_keyword/<int:parent_id>/", methods=["POST"])
def create_keyword(parent_id):
    # get form data
    data = request.form
    data = data.to_dict()
    keyw = Keyword()
    keyw.ParentID = parent_id
    keyw.DisplayFormat = data['DisplayFormat']
    keyw.Category = 'Keyword'
    keyw.Type = 'Molecules'
    # change displayformat to normal text
    keyw.Keyword = html2text.html2text(keyw.DisplayFormat)
    keyw.Keyword = keyw.Keyword.strip()
    # save everything
    keyw.save()
    data['ID'] = keyw.KeywordID
    data['Keyword']= keyw.Keyword
    return Response(json.dumps(data), content_type='application/json')

@keywordcontroller.route("/<keyword_type>/<int:parent_id>/", methods=["GET"])
def get_keywords_for(keyword_type, parent_id):
    keywords = Keyword.query.filter(and_(Keyword.Type==keyword_type,Keyword.ParentID==parent_id)).all()
    resp = [keyword.to_hash() for keyword in keywords]
    return Response(json.dumps(resp), content_type='application/json')

@keywordcontroller.route("/<keyword_type>/<int:parent_id>/synonym", methods=["GET"])
def get_keywords_synonyms_for(keyword_type, parent_id):
    keywords = Keyword.query.filter(and_(Keyword.Type==keyword_type,Keyword.ParentID==parent_id)).all()
    resp = [keyword.to_hash() for keyword in keywords if keyword.Category == "Synonym"]
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

@keywordcontroller.route("/<int:synonym_id>/delete_synonym/", methods=["POST"])
def delete_synonym(synonym_id):
    syn = Keyword.query.filter_by(KeywordID=synonym_id).first()
    db.session.delete(syn)
    db.session.commit()
    return str(synonym_id)

@keywordcontroller.route("/<int:keyword_id>/delete_keyword/", methods=["POST"])
def delete_keyword(keyword_id):
    keyw = Keyword.query.filter_by(KeywordID=keyword_id).first()
    db.session.delete(keyw)
    db.session.commit()
    return str(keyword_id)