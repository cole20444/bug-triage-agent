import os
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re

class AzureDevOpsAnalyzer:
    """Analyze Azure DevOps repositories for bug investigation"""
    
    def __init__(self, azure_token: str = None):
        """Initialize Azure DevOps API client"""
        self.azure_token = azure_token
        self.base_url = "https://dev.azure.com"
    
    def _get_token(self):
        """Get Azure token, reloading from environment if needed"""
        if not self.azure_token:
            self.azure_token = os.getenv('AZURE_DEVOPS_TOKEN')
        return self.azure_token
    
    def extract_repo_info(self, repo_url: str) -> Tuple[str, str, str, str]:
        """Extract organization, project, and repo name from Azure DevOps URL"""
        # Handle Azure DevOps URL format: https://dev.azure.com/org/project/_git/repo
        # Also handle URLs with angle brackets: <https://dev.azure.com/org/project/_git/repo>
        pattern = r'<?https://dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/>]+)>?'
        match = re.match(pattern, repo_url)
        if match:
            org = match.group(1)
            project = match.group(2)
            repo = match.group(3)
            return org, project, repo, f"{org}/{project}/{repo}"
        
        raise ValueError(f"Invalid Azure DevOps URL format: {repo_url}")
    
    def get_recent_commits(self, repo_url: str, days: int = 7, branch: str = "main") -> List[Dict]:
        """Get recent commits from an Azure DevOps repository"""
        azure_token = self._get_token()
        
        if not azure_token:
            print("No Azure DevOps token configured")
            return []
        
        try:
            org, project, repo, repo_id = self.extract_repo_info(repo_url)
            
            # Azure DevOps REST API endpoint for commits
            api_url = f"{self.base_url}/{org}/{project}/_apis/git/repositories/{repo}/commits"
            
            # Azure DevOps uses Basic auth with username:token format
            import base64
            auth_string = f":{azure_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json'
            }
            
            # Get the last 10 commits regardless of date
            params = {
                'api-version': '6.0',
                'searchCriteria.$top': 10,
                'searchCriteria.itemVersion.version': branch
            }
            
            response = requests.get(api_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                commits = []
                
                for commit in data.get('value', []):
                    commit_info = {
                        'sha': commit['commitId'][:8],
                        'message': commit['comment'],
                        'author': commit['author']['name'],
                        'date': commit['author']['date'],
                        'url': f"{self.base_url}/{org}/{project}/_git/{repo}/commit/{commit['commitId']}",
                        'files_changed': []
                    }
                    
                    # Get files changed in this commit
                    try:
                        changes_url = f"{self.base_url}/{org}/{project}/_apis/git/repositories/{repo}/commits/{commit['commitId']}/changes"
                        changes_response = requests.get(changes_url, headers=headers, params={'api-version': '6.0'})
                        
                        if changes_response.status_code == 200:
                            changes_data = changes_response.json()
                            for change in changes_data.get('changes', []):
                                commit_info['files_changed'].append({
                                    'filename': change['item']['path'],
                                    'status': change['changeType'],
                                    'additions': 0,  # Azure DevOps doesn't provide this easily
                                    'deletions': 0,
                                    'changes': 1
                                })
                    except Exception as e:
                        print(f"Error getting file changes: {e}")
                    
                    commits.append(commit_info)
                
                return commits
            else:
                print(f"Error fetching Azure DevOps commits: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error analyzing Azure DevOps repository: {e}")
            return []
    
    def analyze_commit_impact(self, commits: List[Dict], bug_keywords: List[str]) -> Dict:
        """Analyze commits for potential impact on reported bugs"""
        impact_analysis = {
            'high_impact_commits': [],
            'medium_impact_commits': [],
            'low_impact_commits': [],
            'potential_causes': [],
            'affected_files': set(),
            'total_changes': 0
        }
        
        for commit in commits:
            # Check commit message for bug-related keywords
            message_lower = commit['message'].lower()
            keyword_matches = [kw for kw in bug_keywords if kw.lower() in message_lower]
            
            # Analyze file changes
            file_impact = self._analyze_file_changes(commit['files_changed'], bug_keywords)
            
            # Determine commit impact level
            impact_score = len(keyword_matches) + file_impact['score']
            
            commit_info = {
                'sha': commit['sha'],
                'message': commit['message'],
                'author': commit['author'],
                'date': commit['date'],
                'url': commit['url'],
                'keyword_matches': keyword_matches,
                'file_impact': file_impact,
                'impact_score': impact_score
            }
            
            if impact_score >= 3:
                impact_analysis['high_impact_commits'].append(commit_info)
            elif impact_score >= 1:
                impact_analysis['medium_impact_commits'].append(commit_info)
            else:
                impact_analysis['low_impact_commits'].append(commit_info)
            
            # Track affected files
            for file in commit['files_changed']:
                impact_analysis['affected_files'].add(file['filename'])
            
            impact_analysis['total_changes'] += len(commit['files_changed'])
        
        impact_analysis['affected_files'] = list(impact_analysis['affected_files'])
        
        return impact_analysis
    
    def _analyze_file_changes(self, files: List[Dict], bug_keywords: List[str]) -> Dict:
        """Analyze individual file changes for bug relevance"""
        analysis = {
            'score': 0,
            'relevant_files': [],
            'file_types': set()
        }
        
        for file in files:
            filename = file['filename'].lower()
            
            # Check file type relevance
            if any(ext in filename for ext in ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss']):
                analysis['score'] += 1  # Frontend files
                analysis['file_types'].add('frontend')
            elif any(ext in filename for ext in ['.php', '.py', '.java', '.rb']):
                analysis['score'] += 1  # Backend files
                analysis['file_types'].add('backend')
            elif any(ext in filename for ext in ['.html', '.htm', '.xml']):
                analysis['score'] += 1  # Template files
                analysis['file_types'].add('template')
            
            # Check filename for bug-related keywords
            for keyword in bug_keywords:
                if keyword.lower() in filename:
                    analysis['score'] += 2
                    analysis['relevant_files'].append(file['filename'])
                    break
            
            # Check for deletions (potential breaking changes)
            if file['status'] == 'delete':
                analysis['score'] += 2
        
        analysis['file_types'] = list(analysis['file_types'])
        return analysis
    
    def get_repository_stats(self, repo_url: str, branch: str = "main") -> Dict:
        """Get repository statistics and metrics"""
        azure_token = self._get_token()
        
        if not azure_token:
            return {}
        
        try:
            org, project, repo, repo_id = self.extract_repo_info(repo_url)
            
            # Azure DevOps REST API endpoint for repository info
            api_url = f"{self.base_url}/{org}/{project}/_apis/git/repositories/{repo}"
            
            # Azure DevOps uses Basic auth with username:token format
            import base64
            auth_string = f":{azure_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json'
            }
            
            params = {'api-version': '6.0'}
            
            response = requests.get(api_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                stats = {
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'language': 'unknown',  # Azure DevOps doesn't provide this
                    'stars': 0,  # Azure DevOps doesn't have stars
                    'forks': 0,  # Azure DevOps doesn't have forks
                    'open_issues': 0,  # Would need separate API call
                    'last_updated': data.get('updatedDate', ''),
                    'size': data.get('size', 0),
                    'default_branch': data.get('defaultBranch', 'main')
                }
                
                return stats
            else:
                print(f"Error fetching Azure DevOps repository stats: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting Azure DevOps repository stats: {e}")
            return {}

# Global instance - will load token when needed
azure_analyzer = AzureDevOpsAnalyzer() 