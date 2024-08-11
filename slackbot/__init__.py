import os
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

# Listens to incoming messages that mention the bot
@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    logger.debug(f"Received app_mention event: {body}")
    user = body['event']['user']
    text = body['event']['text']
    
    if "button" in text.lower():
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Release Notes for:\n*<https://github.com/nehiljain/langchain-by-lazypms/releases/tag/langchain-openai%3D%3D0.1.21|langchain-openai==0.1.21>*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Changes since langchain-openai==0.1.20\n\nopenai[patch]: Release 0.1.21 (#25269)\npartners: fix of issue #24880 (#25229)\ninfra: temp skip oai embeddings test (#25148)\nopenai[patch]: Release 0.1.21rc2 (#25146)\nopenai[patch]: ChatOpenAI.with_structured_output json_schema support (#25123)\nopenai[patch]: Release 0.1.21rc1 (#25116)\ncore[patch], openai[patch]: enable strict tool calling (#25111)\npatch[Partners] Unified fix of incorrect variable declarations in all check_imports (#25014)"
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
                            "text": "Go Ahead"
                        },
                        "value": "accepted",
                        "action_id": "accepted"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Let me make some changes"
                        },
                        "value": "rejected",
                        "action_id": "rejected"
                    }
                ]
            }
        ]
        say(blocks=blocks, text="Choose an option:")
    else:
        say(f"Hey there <@{user}>!")

# Listens to button clicks
@app.action("accepted")
def handle_option_1(ack, body, say, logger):
    ack()
    logger.debug(f"Option 1 selected: {body}")
    user = body['user']['id']
    say(f"<@{user}> accepted the request")

@app.action("rejected")
def handle_option_2(ack, body, say, logger):
    ack()
    logger.debug(f"Option 2 selected: {body}")
    user = body['user']['id']
    say(f"<@{user}> rejected the request")

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()