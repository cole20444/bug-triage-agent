# Bug Triage Agent (Phase 1)

This Slack bot collects structured bug reports from users and summarizes them for triage.

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name: `Bug Triage Agent`
5. Select your workspace
6. Click "Create App"

### 2. Configure App Permissions

1. In your app settings, go to "OAuth & Permissions" in the left sidebar
2. Under "Scopes" → "Bot Token Scopes", add these permissions:
   - `app_mentions:read` - To respond when mentioned
   - `chat:write` - To send messages
   - `im:history` - To read direct messages
   - `im:read` - To read direct messages
   - `im:write` - To send direct messages

### 3. Enable Socket Mode

1. Go to "Socket Mode" in the left sidebar
2. Toggle "Enable Socket Mode" to ON
3. Enter an app-level token name (e.g., `bug-triage-agent`)
4. Copy the generated token (starts with `xapp-`) - this is your `SLACK_APP_TOKEN`

### 4. Install App to Workspace

1. Go to "Install App" in the left sidebar
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`) - this is your `SLACK_BOT_TOKEN`

### 5. Configure Event Subscriptions

1. Go to "Event Subscriptions" in the left sidebar
2. Toggle "Enable Events" to ON
3. Under "Subscribe to bot events", add:
   - `app_mention` - To respond when the bot is mentioned
   - `message.im` - To handle direct messages

### 6. Set Up Environment Variables

1. Create a `.env` file in the project root with the following content:
```bash
# Bot User OAuth Token (starts with xoxb-)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# App-Level Token for Socket Mode (starts with xapp-)
SLACK_APP_TOKEN=xapp-your-app-token-here
```

2. Replace the placeholder values with your actual tokens:
   - `SLACK_BOT_TOKEN`: Copy from "OAuth & Permissions" → "Bot User OAuth Token" (step 4)
   - `SLACK_APP_TOKEN`: Copy from "Socket Mode" → "App-Level Token" (step 3)

### 7. Install Dependencies

```bash
pip install -r requirements.txt
```

### 8. Run the Bot

```bash
python app.py
```

## Usage

1. Invite the bot to a channel: `/invite @Bug Triage Agent`
2. Mention the bot: `@Bug Triage Agent`
3. Follow the prompts to report a bug:
   - Brief summary
   - Affected pages (URLs)
   - Steps to reproduce
   - Templates/components involved (optional)

The bot will collect the information and format it into a structured bug report.

## Features

- **Structured Data Collection**: Guides users through a step-by-step bug reporting process
- **Slack Integration**: Works seamlessly within Slack channels and DMs
- **Formatted Output**: Generates clean, organized bug reports for the development team
- **Socket Mode**: Uses Slack's Socket Mode for real-time communication

## Future Enhancements

- Persistent storage for bug reports
- Integration with issue tracking systems (Jira, GitHub Issues)
- Automated triage and assignment
- Analytics and reporting dashboard

