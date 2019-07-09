import re

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.dates

users = db.users


def parse_date(date: str) -> tuple:
    """
    Converts date-string into a tuple, which contains an integer and a split date

    :param date: A date-string in the format 'YYYY-MM-DD'
    :rtype: tuple
    """
    split_date = date.split('-')
    regex_arr = [
        r"(\d{4}?)", r"(0[0-9]|1[0-2])", r"(0[0-9]|1[0-9]|2[0-9]|3[0-1])"
    ]

    for i, (date_section,
            regex_section) in enumerate(zip(split_date, regex_arr)):
        compiled_regex = re.compile(regex_section)
        is_date = compiled_regex.match(date_section)
        if not is_date:
            if len(split_date[0]) != 4:
                raise SyntaxError(
                    f"Invalid Syntax: The date inputed ({date}) should be in YYYY-MM-DD format"
                )

            date_section = date_section.zfill(2)
            split_date[i] = date_section

            is_date = compiled_regex.match(date_section)
            if not is_date:
                raise SyntaxError(
                    f"Invalid Syntax: The date inputed ({date}) should be in YYYY-MM-DD format"
                )

    int_dates = int(''.join(split_date))

    # pprint(int_dates)
    return (int_dates, split_date)


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


# DEBUG CODE. # * REMOVE LATER
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

    current_scheduled = 0
    for data in users.find({}):
        parsed_start = parse_date(data.get("start"))
        parsed_end = parse_date(data.get("end"))
        if data is not None:
            if (start >= parsed_start and end <= parsed_end
                    and current_scheduled < max_amount):
                current_scheduled += 1
    return True if current_scheduled <= max_amount else False


class MongoTools():
    """
    Helper functions for MongoDB, specifically for slack
    """

    def __init__(self,
                 database: str = "users",
                 buffer_size: int = 3,
                 host="localhost",
                 port=27017,
                 **kwargs):
        self.buffer = []
        self.database = MongoClient(host, port)[database]
        self.BUFFER_SIZE = buffer_size

    def clear_buffer(self):
        self.buffer.clear()

    def append(self, other):
        """
        Append more elements into the mongo buffer

        :param other: either a list of dicts or another MongoBuffer
        """
        # for documents in other: # * Need to know how to use __iter__
        #    assert documents is dict
        assert other is list or other is MongoTools
        if len(self.buffer) + len(other) > self.BUFFER_SIZE:
            self.push_to_collection("scheduled_users")

        self.buffer = [*self.buffer, *other
                       ] if other is list else [*self.buffer, *other.buffer]
        self.remove_duplicates()

    def remove_duplicates(self, id_list=None):
        if id_list is None:
            id_list = self.get_ids()
        nd_set = set(self.buffer)
        if len(id_list) == len(nd_set):
            print("no duplicates to remove!")
        else:
            dif = sorted(id_list) - nd_set
            # print(dif)  # * DEBUG

            assert len(self.buffer) >= dif
            u_buffer = []
            for index, r_id in enumerate(dif):
                if self.buffer[index].get("user_id") != r_id:
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

    def get_ids(self, buffer: list = None) -> list:
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

        col.update_many(filter={}, update={"$set": self.buffer}, upsert=True)
        self.clear_buffer()

    def __add__(self, other):
        assert other is list or other is MongoTools
        if len(self.buffer) + len(other) > self.BUFFER_SIZE:
            self.push_to_collection("scheduled_users")
        self.buffer = [*self.buffer, *other
                       ] if other is list else [*self.buffer, *other.buffer]
        self.remove_duplicates()

    def __len__(self) -> int:
        return len(self.buffer)
