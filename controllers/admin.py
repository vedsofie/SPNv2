from flask import Blueprint, request, make_response, render_template, session, redirect, url_for, Response, g
from modules.database import get_db
from sqlalchemy import MetaData
import json
import base64
import time
from datetime import datetime
from copy import deepcopy
from sqlalchemy.engine import reflection

admincontroller = Blueprint("admincontroller", __name__, url_prefix="/admin")
db = get_db()

@admincontroller.route("/", methods=["GET"])
def index():
    tables = list_module_types()
    tables = sorted(tables, key=lambda s: s.lower())
    return render_template('admin/index.html', tables=json.dumps(tables), runninguser=json.dumps(g.user.to_hash()))


def list_module_types():
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    return metadata.tables.keys()

@admincontroller.route("/sfdc/search/<search_text>/", methods=["GET"])
def search_sfdc_by_name(search_text):
    import modules.sfdc as sfdc
    sf = sfdc.get_instance()
    accounts = sf.query(search_text);
    accounts = accounts['records']
    return Response(json.dumps(accounts), content_type='application/json')

@admincontroller.route("/<table_name>/search/<search_text>/", methods=["GET"])
def search_by_name(table_name, search_text):
    cls = get_class_by_tablename(table_name)
    resp = cls().basic_query(search_text)
    return Response(json.dumps(resp), headers={"Content-Type": "application/json"})

@admincontroller.route("/<table_name>/<int:object_id>/", methods=["GET"])
def get_from_id(table_name, object_id):
    cls = get_class_by_tablename(table_name)
    primary_key = get_primary_key(cls)
    res = cls.query.filter(primary_key == object_id).first()
    if res:
        resp = res.to_hash()
        resp["lookup_name"] = res.Name
        return Response(json.dumps(resp), headers={"Content-Type": "application/json"})
    return Response({}, headers={"Content-Type": "application/json"})

def get_primary_key(cls):
    for col in cls.__table__.columns:
        if col.primary_key:
            return col
    return None

def get_class_by_tablename(tablename, reload=False):
    for c in db.Model._decl_class_registry.values():
        if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
            return c

@admincontroller.route("/<table_name>/", methods=["POST"])
def set_table_name(table_name):
    print "set table name"
    cls = get_class_by_tablename(table_name)
    cols = get_column_info(table_name)

    jdata = request.json

    for record in jdata:
        pkey = get_primary_key(cls)
        pkey_name = pkey.name
        data_copy = deepcopy(record)
        for col in record:
            if col in cols:
                col_type = cols[col]['type']
                if col_type == "BYTEA" or col_type == "BLOB":
                    value = record[col]
                    if value == "image":
                        del data_copy[col]
                    elif value != None:
                        data_copy[col] = base64.b64decode(record[col])
                elif col_type == "DATETIME" or col_type == "TIMESTAMP WITHOUT TIME ZONE":
                    val = record[col]
                    if val:
                        val /= 1000
                        dt = datetime.fromtimestamp(val)
                        data_copy[col] = dt
            else:
                del data_copy[col]

        if pkey_name:
            pkey_val = data_copy[pkey_name]
            obj = cls.query.filter(pkey==pkey_val).update(data_copy)
            db.session.commit()
    return "OK"

@admincontroller.route("/<table_name>/", methods=["GET"])
def get_metadata(table_name):
    #get the first row
    print "get metadata"
    cls = get_class_by_tablename(table_name)
    cols = get_column_info(table_name)

    polys = cls().polymorphic_lookups
    polylookups = set()
    for lookup in polys.values():
        polylookups.add(lookup[0])

    random_colors = cls().random_color_fields
    sfdc_lookup_fields = cls().sfdc_lookups
    sfdc_lookups = sfdc_lookup_fields.keys()

    cols = [cols[col] for col in cols
            if col not in cls().exclude_columns
            and col not in polys.keys()
            and col not in polylookups
            and col not in random_colors
            and col not in sfdc_lookups]

    for object_type in polys:
        lookup_id = polys[object_type][0]
        types = list(polys[object_type][1])
        cols.append({
            "type": "PolymorphicLookup",
            "name": lookup_id,
            "lookup_driver": object_type,
            "types": types
        })

    for field_name in sfdc_lookup_fields:
        field_data = {
            "type": "SFDC",
            "name": field_name,
            "field_info": sfdc_lookup_fields[field_name]
        }
        cols.append(field_data)

    """
    for field_name in random_colors:
        cols.append({
            "type": "RandomColor",
            "name": field_name
        })
    """

    return Response(json.dumps(cols), headers={"Content-Type": "application/json"})

def get_column_info(table_name):
    insp = reflection.Inspector.from_engine(db.engine)
    cols = insp.get_columns(table_name)
    pkeys = insp.get_pk_constraint(table_name)
    pkey = pkeys['constrained_columns'][0]
    fkeys = insp.get_foreign_keys(table_name)
    meta = {c['name']: get_column_details(c) for c in cols}
    meta[pkey]["primary_key"] = True
    for fkey in fkeys:
        col = fkey['constrained_columns'][0]
        refed_table = fkey['referred_table']
        meta[col]['references'] = refed_table
    return meta

def get_column_details(column):
    data = {}

    data['type'] = str(column['type'])
    data['name'] = column['name']
    #data['primary_key'] = column['primary_key'] if 'primary_key' in column else False

    return data



@admincontroller.route("/<table_name>/records", methods=["GET"])
def get_records_for_table_name(table_name):
    cls = get_class_by_tablename(table_name)
    records = cls.query.all()
    res = [record.to_hash() for record in records]
    return Response(json.dumps(res), headers={"Content-Type": "application/json"})
