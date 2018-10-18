from chat_server import db
from models.user import User

users = User.query.all()
for user in users:
    user.Active = True
    user.save()