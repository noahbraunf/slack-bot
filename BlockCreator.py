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
        "01": "First",
        "02": "Second",
        "03": "Third",
        "04": "Fourth",
        "05": "Fifth",
        "06": "Sixth",
        "07": "Seventh",
        "08": "Eighth",
        "09": "Ninth",
        "10": "Tenth",
        "11": "Eleventh",
        "12": "Twelth",
        "13": "Thirteenth",
        "14": "Fourteenth",
        "15": "Fifteenth",
        "16": "Sixteenth",
        "17": "Seventeenth",
        "18": "Eighteenth",
        "19": "Nineteenth",
        "20": "Twentieth",
        "21": "Twenty-first",
        "22": "Twenty-second",
        "23": "Twenty-third",
        "24": "Twenty-fourth",
        "25": "Twenty-fifth",
        "26": "Twenty-sixth",
        "27": "Twenty-seventh",
        "28": "Twenty-eighth",
        "29": "Twenty-ninth",
        "30": "Thirtieth",
        "31": "Thirty-first"
    }
    return f"{day_dict[day]} of {month_dict[month]}, {year}", [
        day_dict[day], month_dict[month], year
    ]


class BlockBuilder:
    """A simple python script for creating slack blocks easily and quickly"""

    def __init__(self, block: list = []):
        """Creates a BlockBuilder object"""
        # self.block = None
        self.block = block

    def divider(self):
        """
        Creates a slack divider

        :usage: divider()
        """
        self.block.append({"type": "divider"})
        return BlockBuilder(block=self.block)

    def button(self, name: str = "Button", value: str = "value"):
        """
        Creates a button
        
        :param name: What the button shows on the block
        :param value: The value sent went clicked
        """
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
        """
        Creates a section of text
        
        :param text: Text within section
        
        :usage: section(text="some text")
        """
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

        :usage: many_buttons(name_value=(["Button_1", "b_1"],...,["Button_n", "b_n"])
        """

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
        """
        Creates a section with an image to the side
        
        :param text: The section text
        :param img_data: a tuple of the url and text if image cannot be loaded
        
        :usage: img_section(text="section text", img_data=("www.example.com/image.jpg", "image didn't load"))
        """

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

    def datepicker(self, text: str = "text", year=None, month=None, day=None):
        """
        creates a datepicker element (default today's date) with a section
        
        :param text: Section text
        :param year: default year (leave alone if you want today's year)
        :param month: default month (leave alone if you want today's month)
        :param day: default day (leave alone if you want today's day)
        
        :usage: datepicker(text="section text") # * LEAVING THE REST BLANK TO GET TODAY'S DATE AS DEFAULT
        """
        time = datetime.now()
        # assert int(month) <= 12
        # assert int(day) <= 31
        self.block.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{text}"
            },
            "accessory": {
                "type": "datepicker",
                "initial_date": f"{time.year}-{time.month}-{time.day}",
                #"initial_date": "2019-8-5",
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
                 options: tuple = ([])):
        """
        Creates a dropdown menu with a section
        
        :param section_text: Section text
        :param button_text: Dropdown menu's text
        :param options: dropdown menu options text and value
        
        :usage: dropdown(section_text="section text", button_text="dropdown menu text", options=(["option_1", "value_1"],...,["option_n", "value_n"]))
        """
        # assert len(options) > 0

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
        Creates an overflow (...) menu
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
        """creates a context"""

        def c_text(text="text", text_type="mrkdwn", emoji=True,
                   verbatim=False):
            return {"type": text_type, "text": text, "verbatim": verbatim}

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
        """
        Converts Blockbuilder object into usable slack block
        
        :rtype: Array of dict(s)
        """
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
