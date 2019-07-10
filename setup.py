from setuptools import setup

setup(
    name="Slack Scheduler Bot",
    version="0.0.4-ALPHA",
    packages=['flask', 'slackeventsapi', 'slackclient', 'pymongo'],
    long_description=open("readme.md").read(),
)
