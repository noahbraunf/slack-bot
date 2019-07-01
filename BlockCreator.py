from datetime import datetime

"""A simple python script for creating slack blocks easily and quickly"""


class BlockBuilder:
    time = datetime.now()

    def __init__(self, block: list = []):
        # self.block = None
        self.block = block

    def divider(self):
        self.block.append({"type": "divider"})
        return BlockBuilder(self.block)

    def button(self, name: str = "Button", value: str = "value"):
        self.block.append({"type": "actions", "elements": [{"type": "button", "text": {
                          "type": "plain_text", "text": "Button", "emoji": True}, "value": "click_me_123"}]})
        return BlockBuilder(self.block)

    def section(self, text: str = "text"):
        self.block.append({"type": "section", "text": {
                          "type": "mrkdwn", "text": text}})
        return BlockBuilder(self.block)

    def many_buttons(self, names: list, values: list):
        assert (len(names) and len(values)) != 0 and len(names) == len(values)

        button_dict = {"type": "actions", "elements": []}

        for name, value in zip(names, values):
            button_dict["elements"].append(
                {"type": "button", "text": {"type": "plain_text", "text": f"{name}", "emoji": True},
                 "value": f"{value}"})
        self.block.append(button_dict)

        return BlockBuilder(self.block)

    def img(self, title: str = "image", img_data: tuple = ("url", "alt text")):
        assert len(img_data) == 2

        self.block.append({"type": "image", "title": {"type": "plain_text", "text": f"{title}", "emoji": True},
                           "image_url": f"{img_data[0]}",
                           "alt_text": f"{img_data[1]}"
                           })

        return BlockBuilder(self.block)

    def img_section(self, text: str = "text", img_data: tuple = ("url", "alt text")):
        assert len(img_data) == 2

        self.block.append({"type": "section", "text": {"type": "mrkdwn", "text": f"{text}"},
                           "accessory": {"type": "image",
                                         "image_url": f"{img_data[0]}",
                                         "alt_text": f"{img_data[1]}"}})

        return BlockBuilder(self.block)

    def datepicker(self, text: str = "text", year: int = time.year, month: int = time.month,
                   day: int = time.day):
        assert month <= 12
        assert day <= 31

        self.block.append({"type": "section", "text": {"type": "mrkdwn", "text": f"{text}"},
                           "accessory": {"type": "datepicker", "initial_date": f"{year}-{month}-{day}",
                                         "placeholder": {"type": "plain_text", "text": "Select a date",
                                                         "emoji": True}}})

        return BlockBuilder(self.block)

    def dropdown(self, section_text: str = "text", button_text: str = "Select an item", options: tuple = (())):
        assert len(options) > 0

        builder = {"type": "section", "text": {"type": "mrkdwn", "text": f"{section_text}"},
                   "accessory": {"type": "static_select",
                                 "placeholder": {"type": "plain_text", "text": f"{button_text}", "emoji": True},
                                 "options": []}}

        for data in options:
            builder["accessory"]["options"].append(
                {"text": {"type": "plain_text", "text": f"{data[0]}", "emoji": True}, "value": f"{data[1]}"})

        self.block.append(builder)

        return BlockBuilder(self.block)

    def overflow(self, text: str = "text", options: tuple = (())):
        assert len(options) > 0

        builder = {"type": "section", "text": {"type": "overflow", "text": f"{text}"},
                   "accessory": {"type": "overflow", "options": []}}

        for data in options:
            builder["accessory"]["options"].append(
                {"text": {"type": "plain_text", "text": f"{data[0]}", "emoji": True}, "value": f"{data[1]}"})

        self.block.append(builder)

        return BlockBuilder(self.block)

    def to_block(self):
        return self.block

    def __str__(self):
        return self.block


if __name__ == "__main__":
    slack_block = BlockBuilder().section(text="test").divider().button(name="test", value="test").img_section(
        text="hello", img_data=("text.com/example.jpg", "test")).divider()
    print(slack_block)
