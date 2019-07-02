from pprint import pprint
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.takendates

users = db.users


def reset_user(id, name, start: int = None, end: int = None):
    check_taken(start, end)
    user = {
        '_id': id,
        'name': name,
        'start_date': start,
        'end_date': end
    }
    users.update_one({'_id': id}, {'$set': user}, upsert=True)


# DEBUG CODE. TODO: REMOVE LATER
for document in users.find():
    pprint(document)


def check_taken(start, end):
    pass
    # TODO:
