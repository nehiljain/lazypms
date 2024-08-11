import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import logging
import agent

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# GitHub configuration
REPO_OWNER = 'nehiljain'
REPO_NAME = 'langchain-by-lazypms'
RELEASE_TAG = 'langchain-openai==0.1.21'

# GitHub API URLs
RELEASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{RELEASE_TAG}'
UPDATE_RELEASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{{release_id}}'

# Headers for the GitHub API request
githubHeaders = {
    'Accept': 'application/vnd.github.v3+json',
}

def get_release():
    response = requests.get(RELEASE_URL, headers=githubHeaders)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

def update_release(release_id, new_body, access_token):
    update_data = {
        'body': new_body
    }
    headers = {**githubHeaders, 'Authorization': f'token {os.environ.get("GITHUB_ACCESS_TOKEN")}'}
    response = requests.patch(UPDATE_RELEASE_URL.format(release_id=release_id), json=update_data, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

# Listens to incoming messages that mention the bot
@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    logger.debug(f"Received app_mention event: {body}")
    user = body['event']['user']
    text = body['event']['text']
    
    if "suggest some changes" in text.lower():
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "After looking at your GitHub releases on that repo, I've noticed that they could use some improvement in making them more informative. Would you like me to take a crack at rewriting those?"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Yes, please!"
                        },
                        "value": "suggest_edits_please",
                        "action_id": "suggest_edits_please"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Not right now, thanks"
                        },
                        "value": "no_thanks_edits",
                        "action_id": "no_thanks_edits"
                    }
                ]
            }
        ]
        say(blocks=blocks)
    else:
        say(f"Hey there <@{user}>!")

# Listens to button clicks

release_notes = ""

@app.action("suggest_edits_please")
def handle_suggest_edits(ack, body, say, logger):
    ack()
    logger.debug(f"Suggest edits: {body}")
    
    say(blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "I'm reading through <https://github.com/nehiljain/langchain-by-lazypms/releases/tag/langchain-openai%3D%3D0.1.21|your latest release (langchain-openai==0.1.21)>... I'll let you know as soon as I have a draft of potential improvements to the release notes."
            }
        },
    ])

    # Kick off the thing
    global release_notes
    release_notes = agent.run_agent()

    say(blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Okay, I'm back! Here's my first draft of what I think would be a better version of the release notes for <https://github.com/nehiljain/langchain-by-lazypms/releases/tag/langchain-openai%3D%3D0.1.21|your latest release (langchain-openai==0.1.21)>:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": release_notes
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Would you like to make any changes to this or shall I go ahead and make those changes for you?"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Yes, please!"
                    },
                    "value": "accepted",
                    "action_id": "accepted"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Not right now, thanks"
                    },
                    "value": "rejected",
                    "action_id": "rejected"
                }
            ]
        }
    ])

@app.action("no_thanks_edits")
def handle_no_thanks_edits(ack, body, say, logger):
    ack()
    
    say(blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Okay, I won't make any changes!"
            }
        },
    ])

@app.action("accepted")
def handle_option_1(ack, body, say, logger):
    ack()
    logger.debug(f"Option 1 selected: {body}")
    user = body['user']['id']
    
    try:
        global release_notes

        release = get_release()
        release_id = release['id']
        # Assume access_token has been retrieved and stored somewhere
        access_token = 'your_retrieved_access_token'
        update_release(release_id, release_notes, access_token)
        say(f"Great, I've updated <https://github.com/nehiljain/langchain-by-lazypms/releases/tag/langchain-openai%3D%3D0.1.21|the release notes (langchain-openai==0.1.21)> as described above")
    except Exception as e:
        logger.error(f"Failed to update release notes: {e}")
        say(f"<@{user}> there was an error updating the release notes.")

@app.action("rejected")
def handle_option_2(ack, body, say, logger):
    ack()
    logger.debug(f"Option 2 selected: {body}")
    user = body['user']['id']
    say(f"<@{user}> rejected the request")

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
