import json
import os
from os.path import join, dirname
from dotenv import load_dotenv
from urllib.request import unquote
from pprint import pprint
import slack
from flask import Flask, request
from slackeventsapi import SlackEventAdapter

from BlockCreator import BlockBuilder
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

slack_event_adapter = SlackEventAdapter(  # ! Create environment variables for your slack signing secret
    os.getenv('SLACK_SECRET'), "/slack/events", app)
client = slack.WebClient(  # ! Create environment variables for your bot token secret
    os.getenv('SLACK_BOT_SECRET'))
scheduler = BackgroundScheduler()

atexit.register(lambda: scheduler.shutdown())


@slack_event_adapter.on(event="message")
def handle_message(event_data):
    """Does stuff with slack messages"""
    print(event_data)  # DEBUG

    message = event_data["event"]  # gets event payload

    if message.get("user"):  # Makes sure that message is not sent by a bot
        if message.get("text") == "on call":  # Command
            user = message["user"]  # Gets user id of user
            # Gets channel that message was sent in
            channel = message.get("channel")
            text = f"Hello <@{user}>! select the days you will be available through below"

            block = BlockBuilder().section(
                text=text).divider().datepicker(
                    text="Start Date").datepicker(
                        text="End Date").many_buttons(
                            name_value=(
                                ("Submit", "yes"), ("Cancel", "no"))).to_block()  # Block

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
        # converts url-ified JSON payload into readable json
        req = json.loads(unquote(raw_data.decode()).replace("payload=", ""))
        user = req.get('user').get('id')
        channel = req.get('channel').get('id')
        m_ts = req.get('message').get('ts')
        actions = req.get('actions')
    else:
        return 'action unsuccessful: No Data Recieved'  # Slack Problem

    if actions[0].get('type') == 'button':
        value = actions[0].get('value')
        handle_button_click(value, user, channel, m_ts)

    return 'action successful'


def handle_button_click(value, user, channel, ts):
    if value == 'no' or 'yes':
        if value == 'yes':
            client.api_call("chat.postEphemeral", json={"attachments": [
                            {"text": ":tada: *Scheduling...* :tada:\nPlease allow up to 30 minutes for the dates to be updated/scheduled"}], "user": user,
                "channel": channel})
        elif value == 'no':
            client.api_call("chat.postEphemeral", json={"attachments": [
                            {"pretext": ":tada: *Deleting message...* :tada:", "text": "No longer scheduling"}], "user": user,
                "channel": channel})
        client.api_call("chat.delete", json={
            "channel": channel, "ts": ts})


if __name__ == "__main__":
    app.run(port=3000)  # Starts server for listening to slack web server
