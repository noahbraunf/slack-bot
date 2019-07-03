import re

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.dates

users = db.users


def parse_date(date: str) -> int:
    regex = r"(\d{4,})?\-(0[0-9]|1[0-2])\-(0[0-9]|1[0-9]|2[0-9]|3[0-1])"

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
        'start_date': parse_date(start),
        'end_date': parse_date(end)
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

            if (start >= parsed_start and end <= parsed_end
                    and current_scheduled < max_amount):
                current_scheduled += 1
    return


class MongoBuffer():
    def __init__(self, database: str = "users", buffer_size: int = 3, host="localhost", port=27017):
        self.buffer = []
        self.database = MongoClient(host, port).dates
        self.BUFFER_SIZE = buffer_size

    def append(self, other):
        if other is MongoBuffer:
            if len(self.buffer) + len(other.buffer) > self.BUFFER_SIZE:
                raise TypeError
            else:
                self.buffer = [*self.buffer, *other.buffer]
        if other is list:
            if len(self.buffer) + len(other) > self.BUFFER_SIZE:
                raise TypeError
            else:
                self.buffer = [*self.buffer, *other]

    def remove_duplicates(self, d_list):
        assert self.buffer > 0
        nd_set = set(self.buffer)
        if len(d_list) == len(nd_set):
            # TODO: !? #[ ++<| <~~ *** ~~> |>++ ]# ?! :ODOT #
            raise TypeError("no duplicates to remove!")
        else:
            dif = sorted(d_list) - nd_set
            print(dif)  # ! DEBUG

            assert len(self.buffer) >= dif
            u_buffer = []
            for index, r_id in enumerate(dif):
                if self.buffer[index].get("_id") != r_id:
                    u_buffer.append(self.buffer[index])

            self.buffer = u_buffer

    def is_duplicates(self, remove_dupes=False):
        assert self.buffer > 0
        ids = []
        for document in self.buffer:
            ids.append(document.get("_id"))
        if ids != set(ids):
            if remove_dupes:
                remove_duplicates(ids, set(ids))
            return True
        return False

    def push_to_collection(self, collection):
        col = self.database["collection"]

        if is_duplicates():
            self.remove_duplicates()
            raise TypeError
        else:
            col.insert_many(self.buffer)

    def __add__(self, other):
        if other is MongoBuffer:
            if len(self.buffer) + len(other.buffer) > self.BUFFER_SIZE:
                raise TypeError
            else:
                self.buffer = [*self.buffer, *other.buffer]
                remove_duplicates(self.buffer)
        if other is list:
            if len(self.buffer) + len(other) > self.BUFFER_SIZE:
                raise TypeError
            else:
                self.buffer = [*self.buffer, *other]
                remove_duplicates(self.buffer)
