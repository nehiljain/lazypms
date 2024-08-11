import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# GitHub configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = 'nehiljain'
REPO_NAME = 'langchain-by-lazypms'
RELEASE_TAG = 'langchain-openai==0.1.21'

# GitHub API URLs
RELEASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{RELEASE_TAG}'
UPDATE_RELEASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{{release_id}}'

# Headers for the GitHub API request
githubHeaders = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

def get_release():
    response = requests.get(RELEASE_URL, headers=githubHeaders)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

def update_release(release_id, new_body):
    update_data = {
        'body': new_body
    }
    response = requests.patch(UPDATE_RELEASE_URL.format(release_id=release_id), json=update_data, headers=githubHeaders)
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
        release = get_release()
        release_id = release['id']
        updated_release = update_release(release_id, 'hello world')
        say(f"<@{user}> accepted the request. Updated release notes to: {updated_release['body']}")
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
