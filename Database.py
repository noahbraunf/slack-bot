import re

from pymongo import MongoClient


def parse_date(date: str) -> tuple:
    """
    Converts date-string into a tuple, which contains an integer and a split date

    :param date: A date-string in the format `YYYY-MM-DD`\n
    :rtype: tuple of integer date first, then the date array
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
                raise ValueError(
                    f"Invalid Syntax: The date inputed ({date}) should be in YYYY-MM-DD format"
                )

            date_section = date_section.zfill(2)
            split_date[i] = date_section

            is_date = compiled_regex.match(date_section)
            if not is_date:
                raise ValueError(
                    f"Invalid Syntax: The date inputed ({date}) should be in YYYY-MM-DD format"
                )

    int_dates = int(''.join(split_date))
    return (int_dates, split_date)


class MongoTools():
    """
    Helper functions for MongoDB, specifically for slack applications
    """

    def __init__(self,
                 database: str = "users",
                 buffer_size: int = 3,
                 host="localhost",
                 port=27017,
                 **kwargs):
        """
        :param database: Database in MongoDB
        :param buffer_size: Size of buffer of users
        :param host: MongoDB host
        :param port: MongoDB port
        :param **kwargs: Not implemented yet
        """
        self.buffer = []
        self.mc = MongoClient(f'mongodb://{host}:{port}/')
        self.database = self.mc[database]
        self.BUFFER_SIZE = buffer_size

    def clear_buffer(self):
        self.buffer.clear()

    def append(self, other):
        """
        Append more elements into the mongo buffer

        :param other: either a list of dicts or another MongoBuffer
        """
        # for documents in other: # * Need to figure out how to use __iter__
        #    assert documents is dict # ? Deprecated
        assert type(other) is list or type(other) is MongoTools  # Fixed
        if len(self.buffer) + len(other) > self.BUFFER_SIZE:
            self.push_to_collection("scheduled_users")

        self.buffer = [*self.buffer, *other] if type(other) is list else [
            *self.buffer, *other.buffer
        ]
        self.remove_duplicates()

    def remove_user(self, collection, user_id):
        """
        Removes user from specified collecition
        
        :param collection: Collection user will be removed from
        :param user_id: user's ID
        """
        self.database[collection].remove(filter='user_id')

    def remove_duplicates(self, id_list=None):
        """
        Remove duplicates from the buffer
        """
        if id_list is None:
            id_list = self.get_ids()
        id_set = set(id_list)
        if len(id_list) == len(id_set):
            pass  # May add something here later
        elif len(id_list) > len(id_set):
            dif = [s if s not in id_list else None for s in id_set]
            dif = list(filter(lambda x: x, dif))

            assert len(self.buffer) >= len(dif)
            u_buffer = []
            for i, r_id in enumerate(dif):
                if self.buffer[i].get("user_id") != r_id:
                    u_buffer.append(self.buffer[i])

            self.buffer = u_buffer
        else:
            print('something went wrong...')

    def is_duplicates(self, remove_dupes=False) -> bool:
        """
        Checks if there are duplicates in buffer
        
        :param remove_dupes: If true, will also remove duplicates from buffer. Otherwise will only return a bool 
        """
        if len(self.buffer) >= 0:
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
        """
        Push to specified collection in MongoDB

        :param collection: The MongoDB Collection
        """
        col = self.database[collection]

        if self.is_duplicates():
            self.remove_duplicates(id_list=self.get_ids(buffer=self.buffer))

        for doc in self.buffer:
            col.update_one(filter={'user_id': doc['user_id']},
                           update={"$set": doc},
                           upsert=True)
        self.clear_buffer()

    def __add__(self, other):
        """
        Python '+' operator support
        
        :param other: Thing added to buffer. Has to be MongoBuffer or list
        """
        assert isinstance(other, list) or isinstance(other, MongoTools)
        if len(self.buffer) + len(other) > self.BUFFER_SIZE:
            self.push_to_collection("scheduled_users")
        self.buffer = [*self.buffer, *other] if type(other) is list else [
            *self.buffer, *other.buffer
        ]
        self.remove_duplicates()

    def __len__(self) -> int:
        return len(self.buffer)
