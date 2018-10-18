from flask.ext.sqlalchemy import SQLAlchemy


def get_db():
    return db


def generate_db(app):
    global db
    db = SQLAlchemy(app)
    return db
