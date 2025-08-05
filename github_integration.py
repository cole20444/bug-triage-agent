import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from github import Github, GithubException
import re

class GitHubAnalyzer:
    """Analyze GitHub repositories for bug investigation"""
    
    def __init__(self, github_token: str = None):
        """Initialize GitHub API client"""
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        if self.github_token:
            self.github = Github(self.github_token)
        else:
            self.github = None
    
    def extract_repo_info(self, repo_url: str) -> Tuple[str, str]:
        """Extract owner and repo name from GitHub URL"""
        # Handle various GitHub URL formats
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
            r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, repo_url)
            if match:
                return match.group(1), match.group(2)
        
        raise ValueError(f"Invalid GitHub URL format: {repo_url}")
    
    def get_recent_commits(self, repo_url: str, days: int = 7, branch: str = "main") -> List[Dict]:
        """Get recent commits from a GitHub repository"""
        if not self.github:
            return []
        
        try:
            owner, repo_name = self.extract_repo_info(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Get commits from the specified branch
            commits = repo.get_commits(sha=branch, since=datetime.now() - timedelta(days=days))
            
            commit_data = []
            for commit in commits[:10]:  # Limit to 10 most recent commits
                commit_info = {
                    'sha': commit.sha[:8],
                    'message': commit.commit.message,
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date.isoformat(),
                    'url': commit.html_url,
                    'files_changed': []
                }
                
                # Get files changed in this commit
                try:
                    commit_detail = repo.get_commit(commit.sha)
                    for file in commit_detail.files:
                        commit_info['files_changed'].append({
                            'filename': file.filename,
                            'status': file.status,
                            'additions': file.additions,
                            'deletions': file.deletions,
                            'changes': file.changes
                        })
                except GithubException:
                    pass  # Skip if we can't get file details
                
                commit_data.append(commit_info)
            
            return commit_data
            
        except (GithubException, ValueError) as e:
            print(f"Error fetching GitHub commits: {e}")
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
            
            # Check for significant changes
            if file['changes'] > 50:
                analysis['score'] += 1  # Large changes
            
            # Check for deletions (potential breaking changes)
            if file['deletions'] > 10:
                analysis['score'] += 2
        
        analysis['file_types'] = list(analysis['file_types'])
        return analysis
    
    def detect_site_type_from_code(self, repo_url: str, branch: str = "main") -> Dict:
        """Detect site type and technology stack from repository structure"""
        if not self.github:
            return {'site_type': 'unknown', 'confidence': 'low'}
        
        try:
            owner, repo_name = self.extract_repo_info(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Get repository contents
            contents = repo.get_contents("", ref=branch)
            
            detection = {
                'site_type': 'unknown',
                'framework': 'unknown',
                'language': 'unknown',
                'confidence': 'low',
                'indicators': []
            }
            
            # Check for common framework indicators
            indicators = {
                'wordpress': ['wp-config.php', 'wp-content/', 'wp-admin/', 'wp-includes/'],
                'react': ['package.json', 'src/', 'public/', 'node_modules/'],
                'vue': ['package.json', 'src/', 'public/', 'vue.config.js'],
                'laravel': ['artisan', 'app/', 'resources/', 'routes/'],
                'django': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
                'rails': ['Gemfile', 'app/', 'config/', 'db/'],
                'nextjs': ['next.config.js', 'pages/', 'components/'],
                'nuxt': ['nuxt.config.js', 'pages/', 'components/']
            }
            
            file_names = [item.name for item in contents]
            
            for framework, files in indicators.items():
                matches = [f for f in files if any(f in fn for fn in file_names)]
                if matches:
                    detection['indicators'].extend(matches)
                    if len(matches) >= 2:
                        detection['site_type'] = framework
                        detection['framework'] = framework
                        detection['confidence'] = 'high'
                        break
                    elif detection['confidence'] == 'low':
                        detection['site_type'] = framework
                        detection['framework'] = framework
                        detection['confidence'] = 'medium'
            
            # Check for language indicators
            if any('.php' in fn for fn in file_names):
                detection['language'] = 'php'
            elif any('.js' in fn or '.ts' in fn for fn in file_names):
                detection['language'] = 'javascript'
            elif any('.py' in fn for fn in file_names):
                detection['language'] = 'python'
            elif any('.rb' in fn for fn in file_names):
                detection['language'] = 'ruby'
            
            return detection
            
        except (GithubException, ValueError) as e:
            print(f"Error detecting site type from GitHub: {e}")
            return {'site_type': 'unknown', 'confidence': 'low'}
    
    def get_repository_stats(self, repo_url: str, branch: str = "main") -> Dict:
        """Get repository statistics and metrics"""
        if not self.github:
            return {}
        
        try:
            owner, repo_name = self.extract_repo_info(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            stats = {
                'name': repo.name,
                'description': repo.description,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'last_updated': repo.updated_at.isoformat(),
                'size': repo.size,
                'default_branch': repo.default_branch
            }
            
            return stats
            
        except (GithubException, ValueError) as e:
            print(f"Error fetching repository stats: {e}")
            return {}

# Global instance
github_analyzer = GitHubAnalyzer() 