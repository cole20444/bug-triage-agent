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
    text = event.get("text", "").strip()
    
    print(f"Received mention from user {user_id} in channel {channel}: {text[:50]}...")
    
    # If user is already in a conversation, try to extract their response from the mention
    if user_id in user_conversations:
        user_state = user_conversations[user_id]
        step = user_state["step"]
        print(f"User {user_id} already in conversation at step {step}")
        
        # Try to extract the actual message content (remove the bot mention)
        # The text format is usually: "<@BOT_ID> actual message content"
        # Extract bot ID from the mention in the text
        import re
        bot_mention_match = re.search(r'<@([A-Z0-9]+)>', text)
        if bot_mention_match:
            bot_id = bot_mention_match.group(1)
            actual_message = text.replace(f"<@{bot_id}>", "").strip()
        else:
            actual_message = text.strip()
        
        if actual_message and len(actual_message) > 5:  # If there's actual content
            print(f"Extracted message from mention: {actual_message[:50]}...")
            # Process the message as if it came through the message handler
            if step == 0:
                user_state["data"]["summary"] = actual_message
                say("Which *page(s)* are affected? (Please paste full URLs)")
                user_state["step"] = 1
            elif step == 1:
                user_state["data"]["pages"] = actual_message
                say("How can we *reproduce* the issue?")
                user_state["step"] = 2
            elif step == 2:
                user_state["data"]["steps"] = actual_message
                say("Are there any *templates or components* involved? _(Optional)_")
                user_state["step"] = 3
            elif step == 3:
                user_state["data"]["components"] = actual_message
                report = format_bug_report(user_state["data"])
                say(f"✅ Here's your bug report:\n```{report}```\nI'll notify the dev team!")
                del user_conversations[user_id]
            return
        else:
            # No actual message content, just remind them what we need
            if step == 0:
                say(f"<@{user_id}> I'm waiting for your *brief summary* of the issue. Please provide a summary of what's happening.")
            elif step == 1:
                say(f"<@{user_id}> I'm waiting for the *affected page(s)*. Please paste the full URLs of the pages that are affected.")
            elif step == 2:
                say(f"<@{user_id}> I'm waiting for the *steps to reproduce* the issue. Please describe how to reproduce this problem.")
            elif step == 3:
                say(f"<@{user_id}> I'm waiting for any *templates or components* involved. If none, just say 'none' or 'N/A'.")
            return
    
    # Start new conversation
    user_conversations[user_id] = {"step": 0, "data": {}}
    print(f"Started new conversation with user {user_id} in channel {channel}")
    say(f"<@{user_id}> Thanks for reporting a bug! Let's gather some details.\nFirst, what's a *brief summary* of the issue?")

@app.event("message")
def handle_message(event, say):
    user_id = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "").strip()
    event_type = event.get("type")
    
    # Debug all message events
    print(f"Received message event - Type: {event_type}, User: {user_id}, Channel: {channel}, Text: {text[:50]}...")
    
    # Skip bot messages and messages without user
    if not user_id or event.get("bot_id"):
        print(f"Skipping message - no user or bot message")
        return
    
    # Check if user is in an active conversation
    if user_id not in user_conversations:
        print(f"User {user_id} not in active conversation")
        return

    user_state = user_conversations[user_id]
    step = user_state["step"]
    
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
