import Database
import json
import slack

from BlockCreator import BlockBuilder
from flask import Flask, request
from pprint import pprint
from slackeventsapi import SlackEventAdapter
from urllib.request import unquote

app = Flask(__name__)

value = 0
slack_event_adapter = SlackEventAdapter(
    "9a3a31459067ead3f356e43c2214e3a9", "/slack/events", app)
client = slack.WebClient(
    "xoxb-675245215444-666074695570-4R88WCBuW3D1CkblzgSFk9T5")


@slack_event_adapter.on(event="message")
def handle_message(event_data):
    print(event_data)

    message = event_data["event"]

    if message.get("user"):
        if message.get("text") == "avail":
            user = message["user"]
            channel = message["channel"]
            message = f"Hello <@{user}>! select the days you will be available through below\n"

            block = BlockBuilder().section(text=message).to_block()

            client.api_call(api_method="chat.postMessage", json={
                "channel": channel, "blocks": block})


@app.route("/slack/interactive", methods=['GET', 'POST'])
def handle_interaction():
    global value
    raw_data = request.get_data()

    if raw_data is not None:
        req = json.loads(unquote(raw_data.decode()).replace("payload=", ""))
    else:
        return 'action unsuccessful: No Data Recieved'

    return 'action successful'


def check_db():
    pass


def update_database(start_date: int, end_date: int):
    pass


if __name__ == "__main__":
    app.run(port=3000)
