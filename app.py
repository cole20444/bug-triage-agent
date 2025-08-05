from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from report_handler import format_bug_report
from storage import storage
import requests

import os
from dotenv import load_dotenv

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])

def check_app_config():
    """Check and display the current app configuration"""
    try:
        # Get app info using the bot token
        headers = {
            "Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}",
            "Content-Type": "application/json"
        }
        
        # Get auth info to see scopes
        auth_response = requests.get("https://slack.com/api/auth.test", headers=headers)
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            if auth_data.get("ok"):
                print("✅ Bot authentication successful")
                print(f"   Bot User ID: {auth_data.get('user_id')}")
                print(f"   Team: {auth_data.get('team')}")
                print(f"   User: {auth_data.get('user')}")
            else:
                print(f"❌ Auth test failed: {auth_data.get('error')}")
        
        # Get app info using the app token (for scopes)
        app_headers = {
            "Authorization": f"Bearer {os.environ['SLACK_APP_TOKEN']}",
            "Content-Type": "application/json"
        }
        
        # Note: We can't get event subscriptions via API without admin permissions
        # But we can show what we expect vs what we have
        
        print("\n📋 Expected Configuration:")
        print("   Bot Token Scopes:")
        print("   - app_mentions:read")
        print("   - chat:write")
        print("   - im:history")
        print("   - im:read")
        print("   - im:write")
        print("   - channels:history (for channel messages)")
        print("   - groups:history (for private channel messages)")
        print("   - mpim:history (for group DMs)")
        print("\n   Event Subscriptions:")
        print("   - app_mention")
        print("   - message.channels")
        print("   - message.groups")
        print("   - message.im")
        print("   - message.mpim")
        
        print("\n🔧 To check your actual configuration:")
        print("   1. Go to https://api.slack.com/apps")
        print("   2. Select your 'Bug Triage Agent' app")
        print("   3. Check 'OAuth & Permissions' for scopes")
        print("   4. Check 'Event Subscriptions' for events")
        
    except Exception as e:
        print(f"❌ Error checking app config: {e}")

# Store conversation state per user
user_conversations = {}

REQUIRED_FIELDS = ["summary", "pages", "steps"]
OPTIONAL_FIELDS = ["components"]

def parse_bug_report(text):
    """Parse a bug report text to extract structured information"""
    import re
    
    # Initialize data structure
    data = {
        "summary": "",
        "pages": "",
        "steps": "",
        "components": ""
    }
    
    # Extract bot mention if present
    bot_mention_match = re.search(r'<@([A-Z0-9]+)>', text)
    if bot_mention_match:
        bot_id = bot_mention_match.group(1)
        text = text.replace(f"<@{bot_id}>", "").strip()
    
    # Try to extract information using common patterns
    lines = text.split('\n')
    
    # Look for common patterns and keywords
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Summary patterns
        if any(keyword in line_lower for keyword in ['summary:', 'issue:', 'problem:', 'bug:', 'error:']):
            data["summary"] = line.split(':', 1)[1].strip() if ':' in line else line.strip()
        elif not data["summary"] and i == 0 and len(line.strip()) > 10:
            # First substantial line is likely the summary
            data["summary"] = line.strip()
        
        # Pages/URLs patterns
        if any(keyword in line_lower for keyword in ['page:', 'url:', 'site:', 'website:', 'link:']):
            data["pages"] = line.split(':', 1)[1].strip() if ':' in line else line.strip()
        elif 'http' in line and not data["pages"]:
            # Extract URLs
            urls = re.findall(r'https?://[^\s]+', line)
            if urls:
                data["pages"] = ', '.join(urls)
        
        # Steps patterns
        if any(keyword in line_lower for keyword in ['step:', 'reproduce:', 'how to:', 'steps:']):
            data["steps"] = line.split(':', 1)[1].strip() if ':' in line else line.strip()
        
        # Components patterns
        if any(keyword in line_lower for keyword in ['component:', 'template:', 'module:', 'feature:']):
            data["components"] = line.split(':', 1)[1].strip() if ':' in line else line.strip()
    
    # If we have a multi-line response, try to intelligently parse
    if len(lines) > 2 and not any(data.values()):
        # Try to parse based on line position
        if len(lines) >= 1:
            data["summary"] = lines[0].strip()
        if len(lines) >= 2 and 'http' in lines[1]:
            data["pages"] = lines[1].strip()
        if len(lines) >= 3:
            data["steps"] = lines[2].strip()
        if len(lines) >= 4:
            data["components"] = lines[3].strip()
    
    return data

@app.event("app_mention")
def handle_mention(event, say):
    user_id = event["user"]
    channel = event.get("channel")
    text = event.get("text", "").strip()
    
    print(f"Received mention from user {user_id} in channel {channel}: {text[:50]}...")
    
    # Check if this is a management command first
    print(f"Checking for management commands in: '{text[:50]}...'")
    if handle_management_commands(text, user_id, say):
        print("Management command handled successfully")
        return
    else:
        print("No management command found, proceeding with normal flow")
    
    # If user is already in a conversation, try to parse their response
    if user_id in user_conversations:
        user_state = user_conversations[user_id]
        print(f"User {user_id} already in conversation, parsing response...")
        
        # Parse the response
        parsed_data = parse_bug_report(text)
        print(f"Parsed data: {parsed_data}")
        
        # Update existing data with new parsed data
        for key, value in parsed_data.items():
            if value and not user_state["data"].get(key):
                user_state["data"][key] = value
        
        # Check what's missing
        missing_fields = []
        if not user_state["data"].get("summary"):
            missing_fields.append("brief summary")
        if not user_state["data"].get("pages"):
            missing_fields.append("affected pages/URLs")
        if not user_state["data"].get("steps"):
            missing_fields.append("steps to reproduce")
        
        if missing_fields:
            missing_text = ", ".join(missing_fields[:-1])
            if len(missing_fields) > 1:
                missing_text += f" and {missing_fields[-1]}"
            else:
                missing_text = missing_fields[0]
            
            say(f"<@{user_id}> I still need the *{missing_text}*. Please provide this information.")
        else:
            # We have all required fields, save to database and generate the report
            try:
                report_id = storage.save_bug_report(user_id, channel, user_state["data"])
                report = format_bug_report(user_state["data"])
                
                # Add report ID to the formatted report
                report_with_id = f"**Bug Report - {report_id}**\n\n{report}"
                
                say(f"✅ Here's your bug report:\n```{report_with_id}```\nI'll notify the dev team!")
                print(f"Saved bug report {report_id} to database")
                
            except Exception as e:
                print(f"Error saving bug report: {e}")
                report = format_bug_report(user_state["data"])
                say(f"✅ Here's your bug report:\n```{report}```\nI'll notify the dev team!")
            
            del user_conversations[user_id]
        return
    
    # Start new conversation with template
    user_conversations[user_id] = {"step": 0, "data": {}}
    print(f"Started new conversation with user {user_id} in channel {channel}")
    
    template_message = f"""<@{user_id}> Thanks for reporting a bug! 

Please provide the following information in your response:

*Summary:* Brief description of the issue
*Pages:* Full URLs of affected pages (e.g., https://example.com/page)
*Steps:* How to reproduce the issue
*Components:* Any templates/components involved (optional)

You can format it like this:
```
Summary: Mobile load issue affecting Core Web Vitals
Pages: https://wnpf.org/, https://wnpf.org/about
Steps: Open mobile browser, navigate to homepage, check PageSpeed Insights
Components: Header template, mobile navigation
```

Or just describe the issue naturally and I'll try to extract the information."""
    
    say(template_message)

def handle_management_commands(text: str, user_id: str, say) -> bool:
    """Handle management commands for bug reports"""
    # Extract bot mention if present
    import re
    bot_mention_match = re.search(r'<@([A-Z0-9]+)>', text)
    if bot_mention_match:
        bot_id = bot_mention_match.group(1)
        text = text.replace(f"<@{bot_id}>", "").strip()
    
    text_lower = text.lower().strip()
    print(f"Checking management command: '{text_lower}'")
    
    # List recent reports
    if any(cmd in text_lower for cmd in ['list reports', 'show reports', 'reports', 'list']):
        print(f"Executing list reports command")
        reports = storage.get_bug_reports(limit=5)
        if reports:
            response = "**Recent Bug Reports:**\n"
            for report in reports:
                status_emoji = {
                    'new': '🆕',
                    'in_progress': '🔄',
                    'resolved': '✅',
                    'closed': '🔒'
                }.get(report['status'], '❓')
                
                priority_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴',
                    'critical': '🚨'
                }.get(report['priority'], '⚪')
                
                response += f"{status_emoji} {priority_emoji} *{report['report_id']}* - {report['summary'][:50]}...\n"
                response += f"   Status: {report['status']}, Priority: {report['priority']}, Created: {report['created_at'][:10]}\n\n"
        else:
            response = "No bug reports found."
        
        say(response)
        return True
    
    # Show stats
    elif any(cmd in text_lower for cmd in ['stats', 'statistics', 'show stats']):
        stats = storage.get_stats()
        response = "**Bug Report Statistics:**\n"
        response += f"📊 Total Reports: {stats['total']}\n"
        response += f"📈 Recent (7 days): {stats['recent_7_days']}\n\n"
        
        if stats['by_status']:
            response += "**By Status:**\n"
            for status, count in stats['by_status'].items():
                response += f"  {status}: {count}\n"
        
        if stats['by_priority']:
            response += "\n**By Priority:**\n"
            for priority, count in stats['by_priority'].items():
                response += f"  {priority}: {count}\n"
        
        say(response)
        return True
    
    # Search reports
    elif text_lower.startswith('search ') or 'search' in text_lower:
        # Extract search query - look for 'search' keyword and get everything after it
        if text_lower.startswith('search '):
            query = text[7:].strip()  # Remove 'search ' prefix
        else:
            # Find 'search' in the text and get everything after it
            search_index = text_lower.find('search')
            query = text[search_index + 6:].strip()  # Remove 'search' keyword
        if query:
            reports = storage.search_bug_reports(query, limit=3)
            if reports:
                response = f"**Search Results for '{query}':**\n"
                for report in reports:
                    response += f"🔍 *{report['report_id']}* - {report['summary'][:60]}...\n"
                    response += f"   Status: {report['status']}, Created: {report['created_at'][:10]}\n\n"
            else:
                response = f"No reports found matching '{query}'."
            
            say(response)
            return True
    
    # Help command
    elif text_lower in ['help', 'commands', 'what can you do']:
        help_text = """**Bug Triage Agent Commands:**

📝 **Report a Bug:**
Just mention me and describe the issue!

📋 **Management Commands:**
• `list reports` - Show recent bug reports
• `stats` - Show bug report statistics  
• `search [term]` - Search for reports
• `help` - Show this help message

**Example:**
@Bug Triage Agent search mobile performance"""
        
        say(help_text)
        return True
    
    return False

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
    print("🔍 Checking app configuration...")
    check_app_config()
    print("\n🚀 Starting bot...")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
