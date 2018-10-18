# Resets all the client images with exclusion to clients with names:

exclude_list = ['Sofie Biosciences', 'Johns Hopkins PET Center']
from chat_server import db
from models.account import Account

all_accounts = Account.query.all()
for account in all_accounts:
    if account.Name not in exclude_list:
        account._image = None
        account.save()
