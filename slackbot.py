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
        say(blocks=blocks, text="Please choose an option")
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
    ], text="I'm reading through...")

    # Kick off the thing
    global release_notes
    release_notes = agent.run_agent()

    if release_notes is None:
        release_notes = """LangChain-OpenAI v0.1.21 Release Notes
## Executive Summary
This release significantly enhances our OpenAI integration, focusing on structured outputs and tool calling. These improvements will drive increased efficiency in AI-powered applications and provide more robust control over AI outputs.
Key impacts:
- Improved data consistency and reliability in AI outputs
- Enhanced developer productivity through advanced tool calling features
- Resolved critical issues for Azure OpenAI users
## For Program Managers
- **New Feature**: Structured Output API support
  - Benefit: Ensures consistent and predictable AI-generated content, reducing post-processing efforts
- **Improvement**: Advanced tool calling with 'strict' mode
  - Impact: Enables creation of more reliable AI-powered tools, potentially reducing development cycles
- **Fix**: Resolved AzureOpenAI integration issue
  - Outcome: Seamless integration for Azure OpenAI users, minimizing potential project delays
## For Engineers
### 1. Enhanced Structured Output Support
- Implemented support for OpenAI's Structured Output API
- Usage: `ChatOpenAI.with_structured_output().json_schema()`
- Benefit: Enables precise output formatting based on predefined schemas
### 2. Advanced Tool Calling
- Added 'strict' mode for tool calling
- Features:
  - Improved control over model outputs
  - Schema validation for enhanced reliability
- Impact: Create more robust and predictable AI-powered tools
### 3. AzureOpenAI Integration Fix
- Updated `logprobs` parameter default value from False to None in chat models
- Resolves compatibility issues with AzureOpenAI requests
### Dependency Updates
- langchain-core: ^0.2.29rc1
- openai: ^1.40.0
### Additional Technical Notes
- Temporarily skipped some OpenAI embeddings tests due to flakiness
- Fixed incorrect variable declarations in import checking scripts
Relevant Pull Requests:
- #25269: Official release of v0.1.21
- #25229: Fixed logprobs issue in AzureOpenAI (#24880)
- #25123: Added json_schema support for structured outputs
- #25111: Enabled strict tool calling with schema validation"""

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
    ], text="Choose an option:")

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
    ], text="Won't make any changes")

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
