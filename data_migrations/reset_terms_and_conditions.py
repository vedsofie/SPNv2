from chat_server import db
from models.user import User

users = User.query.all()
for usr in users:
    usr.TermsAndConditions = None
    usr.save()
    
