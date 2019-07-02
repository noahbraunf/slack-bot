from pprint import pprint  # DEBUG IMPORT

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.takendates

users = db.users


def update_or_reset_user(user_id: str, name: str, start: int = None, end: int = None):
    """Resets user if {start} and {end} field are taken. Otherwise changes the values of the user"""
    if start is not None and end is not None:
        assert start <= end
    check_taken(user_id, start, end)
    user = {
        '_id': user_id,
        'name': name,
        'start_date': start,
        'end_date': end
    }
    users.update_one({'_id': user_id}, {'$set': user}, upsert=True)


# DEBUG CODE. TODO: REMOVE LATER
for document in users.find():
    pprint(document)


def check_taken(user_id, start, end) -> bool:
    assert user_id is not None and start <= end
    """Checks if dates are taken"""
    for data in users.find():
        if data.get("end") > start > data.get("start"):
            pass  # TODO: Implement Check to see if allowed
        if data.get("start") < end < data.get("end"):
            pass  # TODO: Implement Check to see if allowed
    return True
