from chat_server import db
from models.keyword import Keyword


all_keywords = Keyword.query.all()
for keyword in all_keywords:
    if keyword.DisplayFormat is None or keyword.DisplayFormat == "":
        keyword.DisplayFormat = keyword.Keyword
        keyword.save()


