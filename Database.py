import re

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.takendates

users = db.users


def parse_dates(dates: tuple):
    regex = r"(\d\d\d\d)\-(0[0-9]|1[0-2])\-(0[0-9]|1[0-9]|2[0-9]|3[0-1])"
    regex = re.compile(regex)
    int_dates: list[int] = []
    for date in dates:
        is_date = regex.match(date)

        if is_date:
            int_dates.append(int(date.replace("-", "")))
    # pprint(int_dates)
    return int_dates


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
# for document in users.find():
#     pprint(document)
# test_dates = ("2019-10-12", "2012-04-33", "2019-22-3", "2019-11-09", "2222-12-31")
# parse_dates(test_dates)


def check_taken(user_id, start, end) -> bool:
    assert user_id is not None and start <= end
    """Checks if dates are taken"""
    for data in users.find():
        if data.get("end") > start > data.get("start"):
            pass  # TODO: Implement Check to see if allowed
        if data.get("start") < end < data.get("end"):
            pass  # TODO: Implement Check to see if allowed
    return True
