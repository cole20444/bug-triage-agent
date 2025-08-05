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

# OpenAI API Key for LLM Analysis (optional)
OPENAI_API_KEY=your-openai-api-key-here

# Azure DevOps Token for repository access (optional)
AZURE_DEVOPS_TOKEN=your-azure-devops-token-here

# GitHub Token for repository access (optional)
GITHUB_TOKEN=your-github-token-here
```

2. Replace the placeholder values with your actual tokens:
   - `SLACK_BOT_TOKEN`: Copy from "OAuth & Permissions" → "Bot User OAuth Token" (step 4)
   - `SLACK_APP_TOKEN`: Copy from "Socket Mode" → "App-Level Token" (step 3)
   - `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/) for AI-powered analysis
   - `AZURE_DEVOPS_TOKEN`: Get from Azure DevOps for repository access
   - `GITHUB_TOKEN`: Get from GitHub for repository access

### 7. Install Dependencies

```bash
pip install -r requirements.txt
```

### 8. Run the Bot

```bash
python app.py
```

## Usage

### Basic Bug Reporting

1. Invite the bot to a channel: `/invite @Bug Triage Agent`
2. Mention the bot: `@Bug Triage Agent`
3. Follow the prompts to report a bug:
   - Brief summary
   - Affected pages (URLs)
   - Steps to reproduce
   - Templates/components involved (optional)

The bot will collect the information and format it into a structured bug report.

### Advanced Investigation Commands

Once you have repository configurations set up, you can use these commands:

- `investigate BUG-2025-001` - Deep dive investigation with AI-powered analysis
- `analyze changes` - Analyze recent code changes across repositories
- `config repo project_name type url [branch] [site_type] [hosting_platform]` - Configure repository
- `list repos` - Show repository configurations
- `list reports` - Show recent bug reports
- `search [term]` - Search for reports containing specific terms

### AI-Powered Analysis

When you run an investigation on a WordPress site, the bot will perform:

- **WordPress Core Analysis**: Version compatibility, configuration issues
- **Theme Analysis**: Template files, CSS conflicts, mobile responsiveness
- **Plugin Analysis**: Compatibility issues, performance impact, security vulnerabilities
- **Performance Analysis**: Core Web Vitals, database optimization, asset loading
- **Security Analysis**: Vulnerabilities, file permissions, malicious code detection
- **Risk Assessment**: AI-generated risk levels for different aspects
- **Smart Recommendations**: Actionable suggestions prioritized by impact and effort

## Features

- **Structured Data Collection**: Guides users through a step-by-step bug reporting process
- **Slack Integration**: Works seamlessly within Slack channels and DMs
- **Formatted Output**: Generates clean, organized bug reports for the development team
- **Socket Mode**: Uses Slack's Socket Mode for real-time communication
- **Repository Integration**: Connect GitHub, Azure DevOps, and other repositories for code analysis
- **🤖 AI-Powered LLM Analysis**: Advanced code analysis using OpenAI GPT-4 for comprehensive bug investigation
- **WordPress-Specific Analysis**: Deep analysis of WordPress sites including themes, plugins, performance, and security
- **Risk Assessment**: AI-generated risk levels for security, performance, stability, and maintenance
- **Automated Recommendations**: Intelligent suggestions for bug fixes and improvements

## Future Enhancements

- Persistent storage for bug reports
- Integration with issue tracking systems (Jira, GitHub Issues)
- Automated triage and assignment
- Analytics and reporting dashboard

