from datetime import datetime
from pymongo import MongoClient


def date_to_words(year: str, month: str, day: str) -> tuple:
    """
    Converts day to word


    :param year, month, day: year, month, and day
    :rtype: tuple
    """
    month_dict = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December"
    }

    day_dict = {
        "01": "first",
        "02": "second",
        "03": "third",
        "04": "fourth",
        "05": "fifth",
        "06": "sixth",
        "07": "seventh",
        "08": "eighth",
        "09": "ninth",
        "10": "tenth",
        "11": "eleventh",
        "12": "twelth",
        "13": "thirteenth",
        "14": "fourteenth",
        "15": "fifteenth",
        "16": "sixteenth",
        "17": "seventeenth",
        "18": "eighteenth",
        "19": "nineteenth",
        "20": "twentieth",
        "21": "twenty-first",
        "22": "twenty-second",
        "23": "twenty-third",
        "24": "twenty-fourth",
        "25": "twenty-fifth",
        "26": "twenty-sixth",
        "27": "twenty-seventh",
        "28": "twenty-eighth",
        "29": "twenty-ninth",
        "30": "thirtieth",
        "31": "thirty-first"
    }
    return f"{day_dict[day]} of {month_dict[month]}, {year}", [day_dict[day], month_dict[month], year]


class BlockBuilder:
    """A simple python script for creating slack blocks easily and quickly"""
    time = datetime.now()  # Gets the current time

    def __init__(self, block: list = []):
        # self.block = None
        self.block = block

    def divider(self):
        """
        Creates a slack divider

        :return: BlockBuilder
        """
        self.block.append({"type": "divider"})
        return BlockBuilder(block=self.block)

    def button(self, name: str = "Button", value: str = "value"):
        """Creates a button"""
        self.block.append({
            "type":
            "actions",
            "elements": [{
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": f"{name}",
                    "emoji": True
                },
                "value": f"{value}"
            }]
        })
        return BlockBuilder(block=self.block)

    def section(self, text: str = "text"):
        """Creates a section"""
        self.block.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })
        return BlockBuilder(block=self.block)

    def many_buttons(self,
                     name_value: tuple = (["Button1", "b1"], ["Button2",
                                                              "b2"])):
        """
        Creates many buttons. Names and values have to be the same length

        :param name_value: a tuple of tuples of names of buttons and values
        :rtype: BlockBuilder

        :usage: many_buttons(name_value=(("Button1", "b1"),...,("Button_n", "b_n"))
        """
        assert len(name_value) >= 1

        button_dict = {"type": "actions", "elements": []}

        for data in name_value:
            button_dict["elements"].append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": f"{data[0]}",
                    "emoji": True
                },
                "value": f"{data[1]}"
            })

        self.block.append(button_dict)

        return BlockBuilder(block=self.block)

    def img(self, title: str = "image", img_data: tuple = ("url", "alt text")):
        """
        Creates an image

        :param title: text above image
        :param img_data: url and alt text
        :rtype: BlockBuilder

        :usage: img(tile="an image", img_data=("https://url.com/img.png", "text for when image doesn't load")
        """
        assert len(img_data) == 2

        self.block.append({
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": f"{title}",
                "emoji": True
            },
            "image_url": f"{img_data[0]}",
            "alt_text": f"{img_data[1]}"
        })

        return BlockBuilder(block=self.block)

    def img_section(self,
                    text: str = "text",
                    img_data: tuple = ("url", "alt text")):
        assert len(img_data) == 2

        self.block.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{text}"
            },
            "accessory": {
                "type": "image",
                "image_url": f"{img_data[0]}",
                "alt_text": f"{img_data[1]}"
            }
        })

        return BlockBuilder(block=self.block)

    def datepicker(self,
                   text: str = "text",
                   year: int = time.year,
                   month: int = time.month,
                   day: int = time.day):
        assert month <= 12
        assert day <= 31

        self.block.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{text}"
            },
            "accessory": {
                "type": "datepicker",
                "initial_date": f"{year}-{month}-{day}",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select a date",
                    "emoji": True
                }
            }
        })

        return BlockBuilder(block=self.block)

    def dropdown(self,
                 section_text: str = "text",
                 button_text: str = "Select an item",
                 options: tuple = (())):
        assert len(options) > 0

        builder = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{section_text}"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": f"{button_text}",
                    "emoji": True
                },
                "options": []
            }
        }

        for data in options:
            builder["accessory"]["options"].append({
                "text": {
                    "type": "plain_text",
                    "text": f"{data[0]}",
                    "emoji": True
                },
                "value": f"{data[1]}"
            })

        self.block.append(builder)

        return BlockBuilder(block=self.block)

    def overflow(self, text: str = "text", options: tuple = (())):
        """

        :rtype: BlockBuilder
        """
        assert len(options) > 0

        builder = {
            "type": "section",
            "text": {
                "type": "overflow",
                "text": f"{text}"
            },
            "accessory": {
                "type": "overflow",
                "options": []
            }
        }

        for data in options:
            builder["accessory"]["options"].append({
                "text": {
                    "type": "plain_text",
                    "text": f"{data[0]}",
                    "emoji": True
                },
                "value": f"{data[1]}"
            })

        self.block.append(builder)

        return BlockBuilder(block=self.block)

    def context(self, data: tuple):
        def c_text(text="text", text_type="mrkdwn", emoji=True,
                   verbatim=False):
            return {
                "type": text_type,
                "text": text,
                "verbatim": verbatim
            }

        def c_img(url="your url here", alt_text="backup text"):
            return {"type": "image", "image_url": url, "alt_text": alt_text}

        builder = {"type": "context", "elements": []}

        for block in data:
            if block[0] == "text":
                builder["elements"].append(c_text(text=block[1]))
            if block[0] == "img":
                builder["elements"].append(
                    c_img(url=block[1], alt_text=block[2]))

        self.block.append(builder)

        return BlockBuilder(block=self.block)

    def append(self, json):
        """Use when ceating blocks not implemented"""
        self.block.append(json)

    def to_block(self):
        return self.block

    def __str__(self):
        return self.block


if __name__ == "__main__":
    slack_block = BlockBuilder().section(text="test").divider().button(
        name="test", value="test").img_section(
            text="hello",
            img_data=("text.com/example.jpg", "test")).divider().context(
                ("text", "this is a test"),
                ("img", "test_url.com/test.jpg", "test text")).to_block()
    print(slack_block)
