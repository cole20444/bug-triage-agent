from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from report_handler import format_bug_report
from storage import storage
from repo_config import repo_manager, code_analyzer, RepositoryConfig, RepoType
from storage import storage
from llm_analyzer import llm_analyzer
from code_file_analyzer import code_analyzer as file_analyzer
from issue_focused_analyzer import issue_analyzer
import requests
from typing import Dict, List

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
    
    # Check if this is a management command first
    if handle_management_commands(text, user_id, say, channel_id=channel):
        return
    
    # If user is already in a conversation, try to parse their response
    if user_id in user_conversations:
        user_state = user_conversations[user_id]
        
        # Parse the response
        parsed_data = parse_bug_report(text)
        
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
                
            except Exception as e:
                report = format_bug_report(user_state["data"])
                say(f"✅ Here's your bug report:\n```{report}```\nI'll notify the dev team!")
            
            del user_conversations[user_id]
        return
    
    # Start new conversation with template
    user_conversations[user_id] = {"step": 0, "data": {}}
    
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

def handle_management_commands(text: str, user_id: str, say, channel_id: str = None) -> bool:
    """Handle management commands for bug reports"""

    # Extract bot mention if present
    import re
    bot_mention_match = re.search(r'<@([A-Z0-9]+)>', text)
    if bot_mention_match:
        bot_id = bot_mention_match.group(1)
        text = text.replace(f"<@{bot_id}>", "").strip()
    
    text_lower = text.lower().strip()

    
    # Check for management commands
    if text_lower in ['cancel', 'exit', 'quit', 'stop', 'nevermind']:
        # Cancel/exit bug entry session
        if user_id in user_conversations:
            del user_conversations[user_id]
            say("❌ Bug report cancelled. You can start a new one anytime!")
        else:
            say("No active bug report session to cancel.")
        return True
    
    elif text_lower.startswith('list reports') or text_lower.startswith('show reports') or text_lower.startswith('reports'):
        # List recent reports
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
                
                response += f"{status_emoji} {priority_emoji} *{report['report_id']}* - {report['summary']}\n"
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
    elif text_lower.startswith('search '):
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
                    response += f"🔍 *{report['report_id']}* - {report['summary']}\n"
                    response += f"   Status: {report['status']}, Created: {report['created_at'][:10]}\n\n"
            else:
                response = f"No reports found matching '{query}'."
            
            say(response)
            return True
    
    # Repository configuration commands
    elif 'config repo' in text_lower:
        # Format: config repo project_name repo_type repo_url [branch] [site_type] [hosting_platform]
        # Find the actual command part after bot mention
        # Parse the config repo command manually
        parts = text.split()
        if len(parts) >= 4 and parts[0].lower() == 'config' and parts[1].lower() == 'repo':
            project_name = parts[2]
            repo_type_str = parts[3].lower()
            repo_url = parts[4] if len(parts) > 4 else ""
            branch = parts[5] if len(parts) > 5 else "main"
            site_type = parts[6] if len(parts) > 6 else ""
            hosting_platform = parts[7] if len(parts) > 7 else ""
            
            try:
                repo_type = RepoType(repo_type_str)
                repo_config = RepositoryConfig(
                    name=project_name,
                    type=repo_type,
                    url=repo_url,
                    token="",  # Would need to be provided securely
                    branch=branch,
                    site_type=site_type,
                    hosting_platform=hosting_platform
                )
                
                success = repo_manager.add_channel_config(
                    channel_id, f"channel-{channel_id}", project_name, [repo_config]
                )
                
                if success:
                    response = f"✅ Repository configured for project: *{project_name}*\nType: {repo_type.value}\nURL: {repo_url}\nBranch: {branch}"
                    if site_type:
                        response += f"\nSite Type: {site_type}"
                    if hosting_platform:
                        response += f"\nHosting Platform: {hosting_platform}"
                    say(response)
                else:
                    say("❌ Failed to configure repository")
                    
            except ValueError:
                say(f"❌ Invalid repository type: {repo_type_str}\nSupported types: github, azure, bitbucket, adobe")
        else:
            say("❌ Usage: `config repo project_name repo_type repo_url [branch] [site_type] [hosting_platform]`\nExample: `config repo client-website github https://github.com/client/website main wordpress wordpress-vip`")
        return True
    
    # Add tags to repository
    elif text_lower.startswith('add tags'):
        # Format: add tags project_name tag1 tag2 tag3
        tag_match = re.search(r'add tags\s+(\S+)\s+(.+)', text, re.IGNORECASE)
        if tag_match:
            project_name = tag_match.group(1)
            tags_text = tag_match.group(2)
            tags = [tag.strip() for tag in tags_text.split()]
            
            # Get current config and update tags
            configs = repo_manager.list_channel_configs()
            for config in configs:
                for repo in config['repos']:
                    if repo['name'] == project_name:
                        # Update tags
                        current_tags = repo.get('custom_tags', [])
                        new_tags = list(set(current_tags + tags))  # Remove duplicates
                        repo['custom_tags'] = new_tags
                        
                        # Re-save the configuration
                        repo_config = RepositoryConfig(
                            name=repo['name'],
                            type=RepoType(repo['type']),
                            url=repo['url'],
                            token=repo.get('token', ''),
                            branch=repo.get('branch', 'main'),
                            site_type=repo.get('site_type', ''),
                            hosting_platform=repo.get('hosting_platform', ''),
                            business_domain=repo.get('business_domain', ''),
                            custom_tags=new_tags
                        )
                        
                        success = repo_manager.add_channel_config(
                            config['channel_id'], config['channel_name'], config['project_name'], [repo_config]
                        )
                        
                        if success:
                            say(f"✅ Added tags to *{project_name}*: {', '.join(tags)}\nAll tags: {', '.join(new_tags)}")
                        else:
                            say("❌ Failed to update repository tags")
                        return True
            
            say(f"❌ Project *{project_name}* not found")
        else:
            say("❌ Usage: `add tags project_name tag1 tag2 tag3`\nExample: `add tags client-website high-traffic seo-critical compliance`")
        return True
    
    # Analyze recent changes
    elif any(cmd in text_lower for cmd in ['analyze changes', 'recent changes', 'code analysis']):
        analysis = code_analyzer.analyze_recent_changes(channel_id)
        
        if "error" in analysis:
            say(f"❌ {analysis['error']}\nUse `config repo` to set up repository configuration first.")
        else:
            response = f"**Code Analysis for {analysis['project']}:**\n\n"
            for repo in analysis['repositories']:
                response += f"📁 *{repo['name']}* ({repo['type']})\n"
                response += f"   Status: {repo['status']}\n"
                if repo.get('recent_commits'):
                    response += f"   Recent commits: {len(repo['recent_commits'])}\n"
                response += "\n"
            
            say(response)
        return True
    
    # List repository configurations
    elif any(cmd in text_lower for cmd in ['list repos', 'show repos', 'repo configs', 'list repositories']):
        configs = repo_manager.list_channel_configs()
        
        if configs:
            response = "**Repository Configurations:**\n\n"
            for config in configs:
                response += f"📂 *{config['project_name']}* (Channel: {config['channel_name']})\n"
                for repo in config['repos']:
                    response += f"   • {repo['name']} ({repo['type']}) - {repo['url']}\n"
                    if repo.get('site_type'):
                        response += f"     Site Type: {repo['site_type']}\n"
                    if repo.get('hosting_platform'):
                        response += f"     Hosting: {repo['hosting_platform']}\n"
                    if repo.get('custom_tags'):
                        response += f"     Tags: {', '.join(repo['custom_tags'])}\n"
                response += "\n"
        else:
            response = "No repository configurations found.\nUse `config repo` to set up repositories."
        
        say(response)
        return True
    
    # Update bug report
    elif text_lower.startswith('update'):
        update_match = re.search(r'update\s+(\S+)\s+(summary|steps|pages|components|priority|status)\s+(.+)', text, re.IGNORECASE)
        if update_match:
            report_id = update_match.group(1)
            field = update_match.group(2).lower()
            new_value = update_match.group(3).strip()
            
            report = storage.get_bug_report(report_id)
            if not report:
                say(f"❌ Bug report *{report_id}* not found")
                return True
            
            # Update the specified field
            success = storage.update_bug_report(report_id, {field: new_value})
            if success:
                say(f"✅ Updated *{field}* for bug report *{report_id}*\nNew value: {new_value}")
            else:
                say(f"❌ Failed to update bug report *{report_id}*")
        else:
            say("❌ Usage: `update BUG-2025-001 summary New summary text`\nSupported fields: summary, steps, pages, components, priority, status\nExample: `update BUG-2025-001 priority high`")
        return True
    
    # Investigate specific bug report
    elif text_lower.startswith('investigate'):
        # Format: investigate BUG-2025-001
        investigate_match = re.search(r'investigate\s+(\S+)', text, re.IGNORECASE)
        if investigate_match:
            report_id = investigate_match.group(1)
            
            # Get the bug report
            report = storage.get_bug_report(report_id)
            if not report:
                say(f"❌ Bug report *{report_id}* not found")
                return True
            
            # Get repository configuration for this channel
            config = repo_manager.get_channel_config(channel_id)
            if not config:
                say(f"❌ No repository configuration found for this channel.\nUse `config repo` to set up repositories first.")
                return True
            
            # Analyze the bug with repository context
            investigation = _investigate_bug(report, config)
            
            # Format and send the investigation report
            response = _format_investigation_report(report, investigation)
            say(response)
            return True
        else:
            say("❌ Usage: `investigate BUG-2025-001`\nExample: `investigate BUG-2025-001`")
        return True
    
    # Help command
    elif text_lower in ['help', 'commands', 'what can you do']:
        help_text = """**Bug Triage Agent Commands:**

📝 **Report a Bug:**
Just mention me and describe the issue!
• `cancel` - Exit bug entry session

📋 **Management Commands:**
• `list reports` - Show recent bug reports
• `stats` - Show bug report statistics  
• `search [term]` - Search for reports
• `update BUG-2025-001 field value` - Update bug report fields
• `help` - Show this help message

🔧 **Repository Integration:**
• `config repo project_name type url [branch] [site_type] [hosting_platform]` - Configure repository
• `add tags project_name tag1 tag2` - Add tags to repository
• `list repos` - Show repository configurations
• `analyze changes` - Analyze recent code changes
• `recent changes` - Same as analyze changes

🔍 **Bug Investigation:**
• `investigate BUG-2025-001` - Deep dive investigation of a specific bug

**Repository Types:** github, azure, bitbucket, adobe
**Site Types:** wordpress, react, laravel, vue, etc.
**Hosting Platforms:** wordpress-vip, netlify, vercel, aws, etc.

**Examples:**
@Bug Triage Agent config repo client-website github https://github.com/client/website main wordpress wordpress-vip
@Bug Triage Agent add tags client-website high-traffic seo-critical
@Bug Triage Agent analyze changes
@Bug Triage Agent investigate BUG-2025-001
@Bug Triage Agent update BUG-2025-001 priority high
@Bug Triage Agent search mobile performance
@Bug Triage Agent cancel"""
        
        say(help_text)
        return True
    

    return False

def _investigate_bug(report: Dict, config: Dict) -> Dict:
    """Investigate a bug report using repository analysis and LLM code analysis"""
    # First, analyze the bug report to determine the primary issue type
    issue_focus = issue_analyzer.analyze_bug_report(report)
    
    investigation = {
        'bug_report': report,
        'issue_focus': issue_focus,
        'repository_analysis': [],
        'potential_causes': [],
        'recommendations': [],
        'recent_changes': [],
        'affected_components': [],
        'llm_analysis': {},
        'risk_assessment': {},
        'focused_analysis': {}
    }
    
    # Analyze each repository in the configuration
    for repo_config in config['repos']:
        repo_type = repo_config.get('type', 'github')
        site_type = repo_config.get('site_type', '').lower()
        print(f"Analyzing {repo_type} repository: {repo_config['name']} (Site type: {site_type})")
        
        if repo_type == 'azure':
            repo_analysis = code_analyzer._analyze_azure_repo(repo_config, days=7)
        elif repo_type == 'github':
            repo_analysis = code_analyzer._analyze_github_repo(repo_config, days=7)
        else:
            repo_analysis = code_analyzer._analyze_github_repo(repo_config, days=7)  # fallback
        investigation['repository_analysis'].append(repo_analysis)
        
        # Extract potential causes from high-impact commits
        if repo_analysis.get('impact_analysis'):
            high_impact = repo_analysis['impact_analysis'].get('high_impact_commits', [])
            for commit in high_impact:
                investigation['potential_causes'].append({
                    'commit': commit['sha'],
                    'message': commit['message'],
                    'author': commit['author'],
                    'date': commit['date'],
                    'url': commit['url'],
                    'impact_score': commit['impact_score']
                })
        
        # Track recent changes
        if repo_analysis.get('recent_commits'):
            investigation['recent_changes'].extend(repo_analysis['recent_commits'][:3])
        
        # Track affected components
        if repo_analysis.get('changed_files'):
            investigation['affected_components'].extend(repo_analysis['changed_files'])
        
        # Perform LLM analysis for WordPress sites
        if site_type == 'wordpress' and repo_analysis.get('recent_commits'):
            print(f"Performing LLM analysis for WordPress site: {repo_config['name']}")
            llm_analysis = llm_analyzer.analyze_wordpress_site(
                repo_config['url'],
                report,
                repo_analysis['recent_commits']
            )
            investigation['llm_analysis'] = llm_analysis
            
            # Perform deep code file analysis
            print(f"Performing deep code analysis for WordPress site: {repo_config['name']}")
            code_analysis = file_analyzer.analyze_wordpress_site_code(
                repo_config,
                repo_analysis['recent_commits']
            )
            investigation['code_analysis'] = code_analysis
            
            # Add LLM recommendations to overall recommendations
            if llm_analysis.get('recommendations'):
                investigation['recommendations'].extend(llm_analysis['recommendations'])
            
            # Add code analysis recommendations
            if code_analysis.get('specific_recommendations'):
                investigation['recommendations'].extend(code_analysis['specific_recommendations'])
            
            # Add risk assessment
            if llm_analysis.get('risk_assessment'):
                investigation['risk_assessment'] = llm_analysis['risk_assessment']
            
            # Apply issue-focused filtering to the analysis results
            investigation['focused_analysis'] = issue_analyzer.filter_analysis_results({
                'code_analysis': code_analysis,
                'recommendations': investigation['recommendations']
            }, issue_focus)
    
    # Generate basic recommendations if no LLM analysis was performed
    if not investigation['recommendations']:
        investigation['recommendations'] = _generate_recommendations(report, config)
    
    return investigation

def _generate_recommendations(report: Dict, config: Dict) -> List[str]:
    """Generate recommendations based on bug report and repository context"""
    recommendations = []
    
    # Extract bug keywords
    bug_text = f"{report.get('summary', '')} {report.get('steps', '')}".lower()
    
    # Site type specific recommendations
    for repo in config['repos']:
        site_type = repo.get('site_type', '').lower()
        hosting = repo.get('hosting_platform', '').lower()
        
        if 'mobile' in bug_text and 'performance' in bug_text:
            if site_type == 'wordpress':
                recommendations.append("Check WordPress mobile optimization plugins and theme responsiveness")
                if hosting == 'wordpress-vip':
                    recommendations.append("Review VIP's mobile performance guidelines and caching configuration")
            elif site_type == 'react':
                recommendations.append("Check React component re-rendering and mobile-specific optimizations")
        
        if 'slow' in bug_text or 'performance' in bug_text:
            recommendations.append("Review recent code changes for performance impact")
            recommendations.append("Check for large file uploads or heavy database queries")
        
        if 'error' in bug_text or 'crash' in bug_text:
            recommendations.append("Review error logs and recent commits for breaking changes")
            recommendations.append("Check for missing dependencies or configuration issues")
    
    # General recommendations
    recommendations.append("Review recent commits for potential root causes")
    recommendations.append("Check affected files for syntax errors or logic issues")
    recommendations.append("Test the reported steps to reproduce the issue")
    
    return list(set(recommendations))  # Remove duplicates

def _format_investigation_report(report: Dict, investigation: Dict) -> str:
    """Format the investigation report for Slack"""
    response = f"🔍 **Bug Investigation Report - {report['report_id']}**\n\n"
    
    # Bug summary
    response += f"**Bug Summary:**\n{report.get('summary', 'N/A')}\n\n"
    
    # Issue-Focused Analysis Summary
    if investigation.get('issue_focus'):
        issue_focus = investigation['issue_focus']
        response += issue_analyzer.generate_issue_specific_summary(issue_focus, investigation.get('focused_analysis', {}))
        response += "\n\n"
    
    # Risk Assessment (if available)
    if investigation.get('risk_assessment'):
        risk = investigation['risk_assessment']
        response += "**🚨 Risk Assessment:**\n"
        for risk_type, level in risk.items():
            if isinstance(level, dict) and 'level' in level:
                response += f"• {risk_type}: {level['level']}\n"
            elif isinstance(level, str):
                response += f"• {risk_type}: {level}\n"
        response += "\n"
    
    # Repository analysis status
    if investigation['repository_analysis']:
        response += "**Repository Analysis:**\n"
        for repo_analysis in investigation['repository_analysis']:
            repo_name = repo_analysis.get('name', 'Unknown')
            repo_type = repo_analysis.get('type', 'unknown')
            status = repo_analysis.get('status', 'unknown')
            
            if status == 'analyzed':
                commits_count = len(repo_analysis.get('recent_commits', []))
                files_count = len(repo_analysis.get('changed_files', []))
                response += f"• {repo_name} ({repo_type}): {commits_count} recent commits, {files_count} files changed\n"
            elif status == 'error':
                error = repo_analysis.get('error', 'Unknown error')
                response += f"• {repo_name} ({repo_type}): ❌ Error - {error}\n"
            else:
                response += f"• {repo_name} ({repo_type}): ⏳ Analysis pending\n"
        response += "\n"
    
    # Issue-Focused Code Analysis Results (if available)
    if investigation.get('focused_analysis') and investigation['focused_analysis'].get('focused_analysis'):
        focused_analysis = investigation['focused_analysis']['focused_analysis']
        response += "**🎯 Issue-Focused Code Analysis:**\n"
        
        # Show only relevant analysis based on the issue type
        if focused_analysis.get('mobile_issues'):
            response += f"• **📱 Mobile Issues:** {len(focused_analysis['mobile_issues'])} issues found\n"
        
        if focused_analysis.get('performance_issues'):
            response += f"• **⚡ Performance Issues:** {len(focused_analysis['performance_issues'])} issues found\n"
        
        if focused_analysis.get('security_issues'):
            response += f"• **🔒 Security Issues:** {len(focused_analysis['security_issues'])} issues found\n"
        
        if focused_analysis.get('theme_analysis'):
            theme_analysis = focused_analysis['theme_analysis']
            if theme_analysis.get('mobile_responsiveness'):
                response += f"• **📱 Responsive Design Issues:** {len(theme_analysis['mobile_responsiveness'])} issues found\n"
        
        response += "\n"
    
    # LLM Analysis Results (if available)
    if investigation.get('llm_analysis'):
        llm_analysis = investigation['llm_analysis']
        response += "**🤖 AI-Powered Analysis:**\n"
        
        # WordPress Core Analysis
        if llm_analysis.get('wordpress_analysis'):
            wp_analysis = llm_analysis['wordpress_analysis']
            if isinstance(wp_analysis, dict) and 'analysis' in wp_analysis:
                response += f"• **WordPress Core:** {wp_analysis['analysis'][:200]}...\n"
        
        # Theme Analysis
        if llm_analysis.get('theme_analysis'):
            theme_analysis = llm_analysis['theme_analysis']
            if isinstance(theme_analysis, dict) and 'analysis' in theme_analysis:
                response += f"• **Theme Issues:** {theme_analysis['analysis'][:200]}...\n"
        
        # Plugin Analysis
        if llm_analysis.get('plugin_analysis'):
            plugin_analysis = llm_analysis['plugin_analysis']
            if isinstance(plugin_analysis, dict) and 'analysis' in plugin_analysis:
                response += f"• **Plugin Issues:** {plugin_analysis['analysis'][:200]}...\n"
        
        # Performance Analysis
        if llm_analysis.get('performance_analysis'):
            perf_analysis = llm_analysis['performance_analysis']
            if isinstance(perf_analysis, dict) and 'analysis' in perf_analysis:
                response += f"• **Performance:** {perf_analysis['analysis'][:200]}...\n"
        
        response += "\n"
    
    # Recent changes analysis
    if investigation['recent_changes']:
        response += "**Recent Code Changes:**\n"
        for commit in investigation['recent_changes'][:3]:
            response += f"• {commit['sha']} - {commit['message'][:50]}...\n"
        response += "\n"
    
    # Potential causes
    if investigation['potential_causes']:
        response += "**Potential Root Causes:**\n"
        for cause in investigation['potential_causes'][:3]:
            response += f"• {cause['commit']} - {cause['message'][:60]}...\n"
            response += f"  Impact Score: {cause['impact_score']}\n"
        response += "\n"
    
    # Affected components
    if investigation['affected_components']:
        response += "**Affected Components:**\n"
        for component in investigation['affected_components'][:5]:
            response += f"• {component}\n"
        response += "\n"
    
    # Issue-Focused Recommendations
    if investigation.get('focused_analysis') and investigation['focused_analysis'].get('relevant_recommendations'):
        relevant_recs = investigation['focused_analysis']['relevant_recommendations']
        response += "**🎯 Issue-Focused Recommendations:**\n"
        for i, rec in enumerate(relevant_recs, 1):
            response += f"{i}. {rec}\n"
    elif investigation['recommendations']:
        response += "**🎯 Recommendations:**\n"
        for i, rec in enumerate(investigation['recommendations'][:5], 1):
            response += f"{i}. {rec}\n"
    
    # Add helpful message about tokens if no commits were found
    if not investigation['recent_changes'] and investigation['repository_analysis']:
        response += "\n💡 **To get detailed code analysis:**\n"
        response += "• Add `AZURE_DEVOPS_TOKEN` to your `.env` file for Azure repositories\n"
        response += "• Add `GITHUB_TOKEN` to your `.env` file for GitHub repositories\n"
        response += "• Add `OPENAI_API_KEY` to your `.env` file for AI-powered analysis\n"
        response += "• Get tokens from your platform's developer settings\n"
    
    return response

@app.event("message")
def handle_message(event, say):
    user_id = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "").strip()
    event_type = event.get("type")
    

    
    # Skip bot messages and messages without user
    if not user_id or event.get("bot_id"):
        return
    
    # Check if user is in an active conversation
    if user_id not in user_conversations:
        return

    user_state = user_conversations[user_id]
    step = user_state["step"]

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
