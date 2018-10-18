from chat_server import db
from models.keyword import Keyword
from modules import ml_stripper


all_keywords = Keyword.query.all()

for keyword in all_keywords:
    if keyword.DisplayFormat is not None and keyword.DisplayFormat != "":
        keyword.DisplayFormat = keyword.DisplayFormat.replace('&lt;p&gt;', '')
        keyword.DisplayFormat = keyword.DisplayFormat.replace('&lt;/p&gt;', '')
        keyword.save()


