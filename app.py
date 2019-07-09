import atexit
import json
import logging
import os
from os.path import dirname, join
from pprint import pformat
from urllib.request import unquote

import slack
from apscheduler.schedulers.background import BackgroundScheduler
from colorama import Fore, Style
from dotenv import load_dotenv
from flask import Flask, request
from slackeventsapi import SlackEventAdapter

from BlockCreator import BlockBuilder
from Database import MongoTools, parse_date, update_or_reset_user

app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

slack_event_adapter = SlackEventAdapter(  # * Create environment variables for your slack signing secret
    os.getenv('SLACK_SECRET'), "/slack/events", app)
client = slack.WebClient(  # * Create environment variables for your bot token secret
    os.getenv('SLACK_BOT_SECRET'))
scheduler = BackgroundScheduler()
db = MongoTools(buffer_size=4)
logging.basicConfig(filename='debug.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
atexit.register(lambda: scheduler.shutdown())


@slack_event_adapter.on(event="message")
def handle_message(event_data):
    """Does stuff with slack messages"""
    logging.debug(pformat(event_data))  # * DEBUG

    message = event_data["event"]  # gets event payload

    if message.get("user"):  # Makes sure that message is not sent by a bot
        if message.get("text") == "on call":  # Command
            user = message["user"]  # Gets user id of user
            # Gets channel that message was sent in
            channel = message.get("channel")
            text = f"Hello <@{user}>! select the days you will be available through below"

            block = BlockBuilder([]).section(text=text).divider().datepicker(
                text="Start Date").datepicker(text="End Date").many_buttons(
                    name_value=(("Submit", "yes"), ("Cancel",
                                                    "no"))).to_block()  # Block

            client.api_call(api_method="chat.postMessage",
                            json={
                                "channel": channel,
                                "blocks": block
                            })
            block = None
        if message.get("text") == "view on call":
            pass
        if message.get("text") == "reset on call":
            pass
        if message.get("text") == "help":
            pass


@app.route("/slack/interactive", methods=['GET', 'POST'])
def handle_interaction():
    """Sends payload whenever interactive element (button, etc.) is pressed"""
    raw_data = request.get_data()  # Gets the data

    if raw_data is not None:
        # converts url-ified JSON payload into readable json
        try:
            req = json.loads(
                unquote(raw_data.decode()).replace("payload=", ""))
        except:
            print(
                f"{Fore.YELLOW}Something went wrong on slack's side{Style.RESET_ALL}"
            )
            raise

        logging.debug(pformat(req))
        message = req.get('message')
        user = req.get('user')

        channel = req.get('channel').get('id')
        m_ts = message.get('ts')
        actions = req.get('actions')
    else:
        print(f"{Fore.YELLOW}Slack sent no data back!{Style.RESET_ALL}")
        return 'action unsuccessful: No Data Recieved'  # Slack Problem

    if actions[0].get('type') == 'button' and actions[0].get(
            'value') == "yes" or actions[0].get('value') == "no":
        value = actions[0].get('value')
        datepickers = []
        for data in message.get('blocks'):
            if len(datepickers) >= 2:
                break
            try:
                if data.get('text').get('text') and data.get('accessory'):
                    datepickers.append(
                        data.get('accessory').get('initial_date'))
            except:
                continue
        start_date, end_date = handle_date_selection(datepickers[0],
                                                     datepickers[1])
        db.append({
            "user_id": user.get('id'),
            "name": user.get('name'),
            "start_date": start_date,
            "end_date": end_date
        })
        logging.debug(pformat(db))
        handle_button_click(value, user.get('id'), channel, m_ts,
                            user.get('name'))

    return 'action successful'


def handle_button_click(value, user, channel, ts, name):
    if value == 'no' or 'yes':
        if value == 'yes':
            update_or_reset_user(user_id=user, name=name)
            client.api_call(
                "chat.postEphemeral",
                json={
                    "attachments": [{
                        "pretext":
                        ":tada: *Scheduling...* :tada:",
                        "text":
                        "Please allow up to 30 minutes for the dates to be updated/scheduled"
                    }],
                    "user":
                    user,
                    "channel":
                    channel
                })

        elif value == 'no':
            client.api_call("chat.postEphemeral",
                            json={
                                "attachments": [{
                                    "pretext":
                                    ":tada: *Deleting message...* :tada:",
                                    "text": "No longer scheduling"
                                }],
                                "user":
                                user,
                                "channel":
                                channel
                            })
        # client.api_call("chat.delete", json={ # * Disabled for debug reasons.
        #     "channel": channel, "ts": ts})


def handle_date_selection(start_date, end_date) -> tuple:
    start = parse_date(start_date)[1]
    end = parse_date(end_date)[1]

    return (start, end)


def reset_log():
    f = open('debug.log', 'w')
    f.close()


if __name__ == "__main__":
    reset_log()

    scheduler.add_job(func=reset_log,
                      trigger='cron',
                      year='*',
                      month='*',
                      day='*',
                      hour='0')
    scheduler.add_job(
        func=lambda: db.push_to_collection(collection="scheduled_users"),
        trigger='interval',
        minutes=30)  # ? Do I need to start each job or just one
    scheduler.start()
    logging.info('started scheduled jobs successfully')

    app.run(port=3000)  # Starts server for listening to slack web server
