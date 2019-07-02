
import re

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.takendates

users = db.users


def parse_date(date: str) -> int:
    regex = r"(\d\d\d\d)\-(0[0-9]|1[0-2])\-(0[0-9]|1[0-9]|2[0-9]|3[0-1])"

    regex = re.compile(regex)
    is_date = regex.match(date)

    if is_date:
        int_dates = int(date.replace("-", ""))
    else:
        raise SyntaxError(
            f"Invalid Syntax: The date inputed ({date}) should be in YYYY-MM-DD format")
    # pprint(int_dates)
    return int_dates


def update_or_reset_user(user_id: str, name: str, start: int = None, end: int = None):
    """Resets user if {start} and {end} field are taken. Otherwise changes the values of the user"""
    if start is not None and end is not None:
        assert start <= end
    taken(user_id, start, end, 3)
    user = {
        '_id': user_id,
        'name': name,
        'start_date': start,
        'end_date': end
    }
    users.update_one({'_id': user_id}, {'$set': user}, upsert=True)


# DEBUG CODE. # ! REMOVE LATER
# for document in users.find():
#     pprint(document)
# test_dates = ("2019-10-12", "2012-04-33", "2019-22-3", "2019-11-09", "2222-12-31")
# parse_dates(test_dates)

def check_day():
    pass


def taken(user_id: str, start: int, end: int, max_amount: int) -> bool:
    """
    Checks if dates are taken

    :param user_id: originally pulled from slack
    :param start: start date of availability
    :param max_amount: start date of availability
    :param end: end date of availability
    :rtype: bool
    """
    assert user_id is not None and start <= end

    current_scheduled = None  # ! TODO: make separate
    for data in users.find():
        parsed_start = parse_date(data.get("start"))
        parsed_end = parse_date(data.get("end"))
        if data is not None:
            # if >=
            if start >= parsed_start and end <= parsed_end and current_scheduled < max_amount:
                current_scheduled += 1
    return
