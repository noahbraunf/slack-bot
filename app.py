import atexit
import json
import logging
import os
from os.path import dirname, join
from pprint import pformat
from urllib.request import unquote
from urllib.parse import quote
import requests
import slack
from apscheduler.schedulers.background import BackgroundScheduler
from colorama import Fore, Style
from dotenv import load_dotenv
from flask import Flask, request
from slackeventsapi import SlackEventAdapter

from BlockCreator import BlockBuilder, date_to_words
from Database import MongoTools, parse_date  # , update_or_reset_user # ? Unkown if needed

app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

slack_event_adapter = SlackEventAdapter(  # * Create environment (.env) variables for your slack signing secret
    os.getenv('SLACK_SECRET'), "/slack/events", app)
client = slack.WebClient(  # * Create environment variables for your bot token secret
    os.getenv('SLACK_BOT_SECRET'))
user_client = slack.WebClient(token=os.getenv('SLACK_OAUTH_SECRET'))
scheduler = BackgroundScheduler()
db = MongoTools(buffer_size=1)
logging.basicConfig(filename='debug.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
atexit.register(lambda: scheduler.shutdown())


@slack_event_adapter.on(event="message")
def handle_message(event_data):
    """
    Does stuff with slack messages
    
    :param event_data: the payload sent from slack
    """
    logging.debug(pformat(event_data))  # * DEBUG

    message = event_data["event"]  # gets event payload

    if message.get("user"):  # Makes sure that message is not sent by a bot
        user = message.get("user")  # Gets user id of user

        channel = message.get(
            "channel")  # Gets channel that message was sent in
        if message.get("text") == "on call":  # Command

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
            block = BlockBuilder(
                []).section(text='*Dates People are on Call*').divider()

            collection = db.database['scheduled_users']

            user_images = {}
            for users in collection.find():
                start_date, end_date = users['start_date'], users['end_date']

                user_data = user_client.users_profile_get(
                    user=users["user_id"])
                user_images[
                    users['user_id']] = user_data['profile']['image_72']
                block.context(data=((
                    'img', user_images[users['user_id']],
                    '_error displaying image_'
                ), ('text',
                    f'<@{users["user_id"]}>. _Contact them if you have any concerns_'
                    )))
                block.section(
                    text=
                    f'from the *{date_to_words(start_date[0], start_date[1], start_date[2])[0]}* to the *{date_to_words(end_date[0], end_date[1], end_date[2])[0]}*'
                )

            block = block.to_block()
            logging.debug(pformat(user_images))
            logging.debug(pformat(block))
            client.api_call("chat.postMessage",
                            json={
                                "channel": channel,
                                "blocks": block
                            })

            block = None
        if message.get("text") == "reset on call":
            pass  # TODO: allow user to reset their scheduled on-call dates
        if message.get("text") == "help me schedule":
            pass


@app.route("/slack/interactive", methods=['GET', 'POST'])
def handle_interaction():
    """Sends payload whenever interactive element (button, etc.) is pressed"""
    raw_data = request.get_data(
    )  # Gets the data fuck that when ABCDEFGHIJKLNMOP

    if raw_data is not None:
        # converts url-ified JSON payload into readable json
        try:
            req = json.loads(
                unquote(raw_data.decode()).replace("payload=", ""))
        except:
            print(
                f"{Fore.YELLOW}Something went wrong on slack's: side{Style.RESET_ALL}"
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
        db.append([{
            "user_id": user.get('id'),
            "name": user.get('name'),
            "start_date": start_date,
            "end_date": end_date
        }])
        logging.debug(pformat(db))
        handle_button_click(value, user.get('id'), channel, m_ts,
                            user.get('name'))
        client.api_call(
            "chat.delete",
            json={  #
                "channel": channel,
                "ts": m_ts
            })

    return 'action successful'


def handle_button_click(value, user, channel, ts, name):
    if value == 'no' or 'yes':
        if value == 'yes':
            # update_or_reset_user(user_id=user, name=name) # * DEPRECATED
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


def handle_date_selection(start_date, end_date) -> tuple:
    start = parse_date(start_date)[1]
    end = parse_date(end_date)[1]

    return (start, end)


def reset_log():
    with open('debug.log', 'w+') as f:
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
        minutes=1)
    scheduler.start()
    logging.info('started scheduled jobs successfully')

    app.run(port=3000
            )  # Starts server for listening to slack web api and interactivity
