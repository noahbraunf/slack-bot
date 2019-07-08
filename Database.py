import re

from pymongo import MongoClient
from typing import List, Dict, Tuple
client = MongoClient('localhost', 27017)
db = client.dates

users = db.users


def parse_date(date: str) -> tuple:
    regex = r"(\d{4})?\-(0[0-9]|1[0-2])?\-(0[0-9]|1[0-9]|2[0-9]|3[0-1])?"

    regex = re.compile(regex)
    is_date = regex.match(date)

    if is_date:
        int_dates = int(date.replace("-", ""))
        date_array = date.split("-")
    else:
        raise SyntaxError(
            f"Invalid Syntax: The date inputed ({date}) should be in YYYY-MM-DD format"
        )
    # pprint(int_dates)
    return (int_dates, date_array)


def update_or_reset_user(user_id: str,
                         name: str,
                         start: int = None,
                         end: int = None):
    """Resets user if {start} and {end} field are taken. Otherwise changes the values of the user"""
    if start is not None and end is not None:
        assert start <= end
    else:
        raise ValueError(
            f"start ({start}) or end ({end}) value cannot be none")
    taken(user_id, start, end, 3)
    user = {
        'user_id': user_id,
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


class MongoTools():
    def __init__(self,
                 database: str = "users",
                 buffer_size: int = 3,
                 host="localhost",
                 port=27017):
        self.buffer = List[dict]
        self.database = MongoClient(host, port)[database]
        self.BUFFER_SIZE = buffer_size

    def append(self, other):
        for documents in other:
            assert documents is dict
        if len(self.buffer) + len(other) > self.BUFFER_SIZE:
            raise OverflowError
        else:
            self.buffer = [*self.buffer, *other]
            self.remove_duplicates()

    def remove_duplicates(self, id_list=None):
        if id_list is None:
            id_list = self.get_ids()
        nd_set = set(self.buffer)
        if len(id_list) == len(nd_set):
            raise TypeError("no duplicates to remove!")
        else:
            dif = sorted(id_list) - nd_set
            print(dif)  # ! DEBUG

            assert len(self.buffer) >= dif
            u_buffer = []
            for index, r_id in enumerate(dif):
                if self.buffer[index].get("_id") != r_id:
                    u_buffer.append(self.buffer[index])

            self.buffer = u_buffer

    def is_duplicates(self, remove_dupes=False) -> bool:
        assert self.buffer > 0
        ids = self.get_ids(self.buffer)
        if ids != set(ids):
            if remove_dupes:
                self.remove_duplicates(ids)
            return True
        return False

    def get_ids(self, buffer: List[dict] = None) -> List[str]:
        if buffer is None:
            buffer = self.buffer
        ids = []
        for document in buffer:
            ids.append(document.get("id"))
        return ids

    def push_to_collection(self, collection: str):
        col = self.database[collection]

        if self.is_duplicates():
            self.remove_duplicates(id_list=self.get_ids(buffer=self.buffer))
            raise Exception("Duplicates in List")

        col.update_many(filter={}, update={"$unset": self.buffer}, upsert=True)

    def __add__(self, other):
        assert other is list or MongoTools
        if len(self.buffer) + len(other) > self.BUFFER_SIZE:
            raise OverflowError
        else:
            self.buffer = [*self.buffer, *other]
            self.remove_duplicates()

    def __len__(self) -> int:
        return len(self.buffer)

    def __iter__(self) -> List[dict]:
        return self.buffer
