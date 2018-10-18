from chat_server import db
from models.account import Account

acts = Account.query.all()
for act in acts:
    act_systems = act.systems
    if len(act_systems) > 0:
        sys = act_systems[0]
        act.Latitude = sys.Latitude
        act.Longitude = sys.Longitude

db.session.commit()
