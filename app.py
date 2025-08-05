from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from report_handler import format_bug_report

import os
from dotenv import load_dotenv

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Store conversation state per user
user_conversations = {}

REQUIRED_FIELDS = ["summary", "pages", "steps"]
OPTIONAL_FIELDS = ["components"]

@app.event("app_mention")
def handle_mention(event, say):
    user_id = event["user"]
    channel = event.get("channel")
    user_conversations[user_id] = {"step": 0, "data": {}}
    print(f"Started conversation with user {user_id} in channel {channel}")
    say(f"<@{user_id}> Thanks for reporting a bug! Let's gather some details.\nFirst, what's a *brief summary* of the issue?")

@app.event("message")
def handle_message(event, say):
    user_id = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "").strip()
    
    # Skip bot messages and messages without user
    if not user_id or event.get("bot_id"):
        return
    
    # Check if user is in an active conversation
    if user_id not in user_conversations:
        return

    user_state = user_conversations[user_id]
    step = user_state["step"]
    
    # Add some debugging
    print(f"Processing message from user {user_id} in channel {channel}, step {step}: {text[:50]}...")

    if step == 0:
        user_state["data"]["summary"] = text
        say("Which *page(s)* are affected? (Please paste full URLs)")
    elif step == 1:
        user_state["data"]["pages"] = text
        say("How can we *reproduce* the issue?")
    elif step == 2:
        user_state["data"]["steps"] = text
        say("Are there any *templates or components* involved? _(Optional)_")
    elif step == 3:
        user_state["data"]["components"] = text
        report = format_bug_report(user_state["data"])
        say(f"✅ Here's your bug report:\n```{report}```\nI'll notify the dev team!")
        del user_conversations[user_id]
        return

    user_state["step"] += 1

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
