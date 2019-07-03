#!./env/bin/python3
import json
import os
from urllib.request import unquote

import slack
from flask import Flask, request
from slackeventsapi import SlackEventAdapter

from BlockCreator import BlockBuilder

app = Flask(__name__)

slack_event_adapter = SlackEventAdapter(  # ! Create environment variables for your slack signing secret
    os.environ.get("SLACK_SECRET"), "/slack/events", app)
client = slack.WebClient(  # ! Create environment variables for your bot token secret
    os.environ.get("SLACK_BOT_SECRET"))


@slack_event_adapter.on(event="message")
def handle_message(event_data):
    """Does stuff with slack messages"""
    print(event_data)  # DEBUG

    message = event_data["event"]  # gets event payload

    if message.get("user"):  # Makes sure that message is not sent by a bot
        if message.get("text") == "available":  # Command
            user = message["user"]  # Gets user id of user
            # Gets channel that message was sent in
            channel = message["channel"]
            message = f"Hello <@{user}>! select the days you will be available through below\n"

            block = BlockBuilder().section(
                text=message).to_block()  # TODO: Design message

            client.api_call(api_method="chat.postMessage",
                            json={
                                "channel": channel,
                                "blocks": block
                            })


@app.route("/slack/interactive", methods=['GET', 'POST'])
def handle_interaction():
    """Sends payload whenever interactive element (button, etc.) is pressed"""
    raw_data = request.get_data()  # Gets the data

    if raw_data is not None:
        # converts url-ified JSON into readable json # ! UNUSED
        req = json.loads(unquote(raw_data.decode()).replace("payload=", ""))
    else:
        return 'action unsuccessful: No Data Recieved'

    # TODO: Add interactivity

    return 'action successful'


if __name__ == "__main__":
    app.run(port=3000)  # Starts server for listening to slack web server
