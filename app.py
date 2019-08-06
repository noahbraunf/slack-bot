import atexit
import json
import logging
import os
from collections import defaultdict
from os.path import dirname, join
from pprint import pformat
from urllib.parse import quote
from urllib.request import unquote
from datetime import datetime

import requests
import slack
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, request
from slackeventsapi import SlackEventAdapter
import re

from BlockCreator import BlockBuilder, date_to_words
from Database import MongoTools, parse_date

app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

slack_event_adapter = SlackEventAdapter(  # * Create environment (.env) variables for your slack signing secret
    os.getenv('SLACK_SECRET'), "/slack/events", app)
client = slack.WebClient(  # * Create environment variables for your bot token secret
    os.getenv('SLACK_BOT_SECRET'))
user_client = slack.WebClient(
    token=os.getenv('SLACK_OAUTH_SECRET'))  # Used to get user data from slack
scheduler = BackgroundScheduler()
db = MongoTools(
)  # Creates a mongotools instance for helping with user management
logging.basicConfig(
    filename='debug.log',
    filemode='a',
    format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG)  # Creates logger to make debugging easier
atexit.register(lambda: scheduler.shutdown())

datepickers = {}  # Used as a cache


@slack_event_adapter.on(event="message")
def handle_message(event_data):
    """
    Does stuff with slack messages
    
    :param event_data: the payload sent from slack
    """
    logging.debug(pformat(event_data))  # * DEBUG

    message = event_data["event"]  # gets event payload
    user = message.get("user")  # Gets user id of user or None if not a user

    if user:  # Makes sure that message is not sent by a bot

        channel = message.get(
            "channel")  # Gets channel that message was sent in
        if message.get(
                "text") == "on call":  # Command to schedule when on call

            text = f"Hello <@{user}>! select the start date of the days you will be on call"

            block = BlockBuilder([]).section(text=text).divider().datepicker(
                text="Start Date").many_buttons(
                    name_value=(("Next", "yes0"), ("Cancel",
                                                   "no0"))).to_block()  # Block

            client.chat_postMessage(channel=channel, blocks=block)
            block = None
        elif message.get(
                "text"
        ) == "view on call":  # See who is on call on whichever dates

            db.push_to_collection('scheduled_users')

            block = BlockBuilder(
                []).section(text='*Dates People are on Call*').divider()

            collection = db.database['scheduled_users']
            c_time = datetime.now()
            user_images = {}
            for users in collection.find():
                start_date = users['start_date']
                end_date = users['end_date']
                if start_date and end_date and len(start_date) >= 3 and len(
                        end_date) >= 3:
                    user_data = user_client.users_profile_get(
                        user=users["user_id"])
                    user_images[
                        users['user_id']] = user_data['profile']['image_72']
                    if int(start_date[0]) <= c_time.year <= int(end_date[0]):
                        if int(start_date[1]) <= c_time.month <= int(
                                end_date[1]):
                            if int(start_date[2]) <= c_time.day <= int(
                                    end_date[2]):

                                block.context(data=((
                                    'img', user_images[users['user_id']],
                                    '_error displaying user image_'
                                ), ('text',
                                    f'<@{users["user_id"]}> is on call from the *{date_to_words(start_date[0], start_date[1], start_date[2])[0]}* to the *{date_to_words(end_date[0], end_date[1], end_date[2])[0]}*.\n_Contact them if you have any concerns_'
                                    ))).button(name="Ping",
                                               value=f'{users["user_id"]}')

            block = block.to_block()
            logging.debug(pformat(user_images))
            logging.debug(pformat(block))
            client.api_call("chat.postMessage",
                            json={
                                "channel": channel,
                                "blocks": block
                            })

            block = None

        elif message.get(
                "text") == "reset on call":  # Remove user from on call list

            db.database['scheduled_users'].update_one(
                filter={'user_id': user},
                update={'$set': {
                    'start_date': None,
                    'end_date': None
                }},
                upsert=True)
            client.chat_postEphemeral(
                user=user,
                channel=channel,
                text=f'Sucessfully removed you from on call list')

        elif message.get("text") == "help me schedule":  # Help Command

            block = BlockBuilder([]).section(
                text='_Beep Boop_. I am a bot who schedules things!'
            ).divider().section(
                text=
                '*Command*: `view on call`\n\nThis command displays who is on call on certain dates.\n>Usage: type `view on call` to see who is on call.'
            ).section(
                text=
                '*Command*: `view me`\n\nThis command shows only when you are on call.\n>Usage: type `view me` to view when you are on call.'
            ).section(
                text=
                '*Command*: `on call`\n\nThis command allows you to pick the dates you are on call.\n>Usage: type `on call` and follow the steps I display!'
            ).section(
                text=
                '*Command*: `reset on call`\n\nThis command removes you from the on call list.\n>Usage: type `reset on call` to be removed from the list'
            ).to_block()

            client.chat_postEphemeral(user=user, channel=channel, blocks=block)

            block = None
        elif message.get("text") == "view me":
            user_data = db.database['scheduled_users'].find_one(
                {'user_id': user})
            start_date = user_data.get("start_date")
            end_date = user_data.get("end_date")
            if not start_date and not end_date:
                client.chat_postMessage(
                    channel=channel,
                    text=
                    "You haven't specified when you will be on call! To specify, please type `on call` and follow the steps it gives you."
                )
                return

            block = BlockBuilder(
                []
            ).section(text="Showing when *you* are on call").divider().section(
                text=
                f"You are on call from the *{date_to_words(start_date[0], start_date[1], start_date[2])[0]}* to the *{date_to_words(end_date[0], end_date[1], end_date[2])[0]}*.\n>If you would like to change this, type `on call`. If you would like to remove yourself from the on call list, type `reset on call`."
            ).to_block()

            client.chat_postMessage(channel=channel, blocks=block)

            block = None


# @slack_event_adapter.on(event="message.im")
# def handle_dm(event_data):
#     logging.debug(pformat(event_data))
#     event = event_data.get("event")
#     user_id = event.get("user")
#     if user_id:
#         im_channel = client.im_open(user=user_id)["channel"]["id"]
#         channel = event.get('channel')
#         text = event.get('text')
#         logging.debug(pformat(im_channel))
#         print(pformat(im_channel))
#         client.chat_postMessage(channel=im_channel, text="hello to you!")


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
            logging.debug(
                "Something went wrong on slack's side")  # Slack Problem
            raise

        logging.debug(pformat(req))
        message = req.get('message')
        user = req.get('user')

        channel = req.get('channel').get('id')
        m_ts = message.get('ts')
        actions = req.get('actions')
    else:
        logging.debug("Slack sent no data back!")
        return 'action unsuccessful: No Data Recieved'  # Slack Problem
    logging.debug(pformat(req))
    global datepickers

    if actions[0].get(
            'type'
    ) == 'button':  # Uses a dict-cache to save values of previous datepicker
        handle_button_click(value=actions[0].get('value'),
                            user=user['id'],
                            channel=channel,
                            ts=m_ts)
        if re.match(re.compile(r"\w{9}"), actions[0].get('value')):
            dm_payload = client.im_open(user=actions[0].get('value'))

            client.chat_postMessage(
                channel=dm_payload['channel']['id'],
                text=
                f'<@{user["id"]}> wants to talk to you about when you\'re on call. Please shoot them a dm.'
            )
            return 'action successful'

        if actions[0].get('value') == "no0" or actions[0].get(
                'value') == "no1" or actions[0].get('value') == "yes1":
            if actions[0].get('value') == "yes1":
                logging.debug(pformat(datepickers))
                if datepickers.get(user['id']):
                    if datepickers.get(user['id']).get('start_date'):
                        start_date = datepickers.get(
                            user['id']).get('start_date')
                    else:
                        start_date = message['blocks'][2]['accessory'][
                            'initial_date']
                    if datepickers.get(user['id']).get('end_date'):
                        end_date = datepickers.get(user['id']).get('end_date')
                    else:
                        end_date = message['blocks'][2]['accessory'][
                            'initial_date']
                else:
                    start_date = message['blocks'][2]['accessory'][
                        'initial_date']
                    end_date = message['blocks'][2]['accessory'][
                        'initial_date']
                db.append(other=[{
                    'user_id': user['id'],
                    'name': user['username'],
                    'start_date': parse_date(start_date)[1],
                    'end_date': parse_date(end_date)[1]
                }])
            client.api_call("chat.delete",
                            json={
                                "channel": channel,
                                "ts": m_ts
                            })
            datepickers.pop(user['id'])

    if actions[0].get('type') == 'datepicker':
        if message.get('blocks')[-1].get('elements')[0].get('value') == 'yes0':
            try:
                datepickers[user['id']] = {
                    'start_date': actions[0].get('selected_date')
                }
            except Exception as e:
                logging.exception(e)
                datepickers[user['id']] = {
                    'start_date': actions[0].get('initial_date')
                }
            logging.debug(pformat(datepickers))
        if message.get('blocks')[-1].get('elements')[0].get('value') == 'yes1':
            try:
                try:
                    datepickers[user['id']] = {
                        'start_date': datepickers[user['id']].get('start_date')
                    }
                except:
                    datepickers[user['id']] = {
                        'start_date': actions[0].get('initial_date')
                    }
                datepickers[user['id']]['end_date'] = actions[0].get(
                    'selected_date')
            except Exception as e:
                logging.exception(e)
                try:
                    datepickers[user['id']] = {
                        'start_date': datepickers[user['id']].get('start_date')
                    }
                except Exception as e:
                    logging.exception(e)
                    datepickers[user['id']] = {
                        'start_date': actions[0].get('initial_date')
                    }
                datepickers[user['id']]['end_date'] = {
                    actions[0].get('initial_date')
                }
            logging.debug(pformat(datepickers))

    return 'action successful'


def handle_button_click(
        value,
        user,
        channel,
        ts,
):
    """
    Handles user interaction with date selection block interaction
    
    :param value: button value
    :param user: user id
    :param channel: channel posting
    :ts: timestamp of actual message
    """
    if value == 'yes0':
        block = BlockBuilder([]).section(
            text=f'Now select the end date, <@{user}>.').divider().datepicker(
                text="End Date").many_buttons(name_value=(("Submit", "yes1"),
                                                          ("Cancel",
                                                           "no1"))).to_block()

        client.api_call("chat.update",
                        json={
                            "text": '',
                            "channel": channel,
                            "ts": ts,
                            "blocks": block
                        })
        block = None

    elif value == 'no0':
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

    elif value == 'yes1':
        client.api_call(
            "chat.postEphemeral",
            json={
                'attachments': [{
                    'pretext':
                    ':tada: *Scheduling message...* :tada:',
                    'text':
                    'Please allow up to `10` minutes for your scheduling to be saved.'
                }],
                'user':
                user,
                'channel':
                channel
            })
    elif value == 'no1':
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


if __name__ == "__main__":
    open('debug.log', 'w+').close()

    scheduler.add_job(func=lambda: open('debug.log', 'w+').close(),
                      trigger='cron',
                      year='*',
                      month='*',
                      day='*',
                      hour='0')  # Adds job to reset logs @ 12:00 AM Every Day
    scheduler.add_job(
        func=lambda: db.push_to_collection(collection="scheduled_users"),
        trigger='interval',
        minutes=10)  # Pushes to collection every 10 minutes
    scheduler.start()
    logging.info('started scheduled jobs successfully')

    app.run(port=3000
            )  # Starts server for listening to slack web api and interactivity
