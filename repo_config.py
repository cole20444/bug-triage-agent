import sqlite3
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from github_integration import github_analyzer
from azure_integration import azure_analyzer

class RepoType(Enum):
    GITHUB = "github"
    AZURE = "azure"
    BITBUCKET = "bitbucket"
    ADOBE = "adobe"

@dataclass
class RepositoryConfig:
    name: str
    type: RepoType
    url: str
    token: str
    branch: str = "main"
    paths: List[str] = None
    ignore_patterns: List[str] = None
    site_type: str = ""  # e.g., "wordpress", "react", "laravel"
    hosting_platform: str = ""  # e.g., "wordpress-vip", "netlify", "vercel"
    business_domain: str = ""  # e.g., "healthcare", "finance", "education"
    custom_tags: List[str] = None  # e.g., ["high-traffic", "seo-critical", "compliance"]
    
    def __post_init__(self):
        if self.paths is None:
            self.paths = []
        if self.ignore_patterns is None:
            self.ignore_patterns = []
        if self.custom_tags is None:
            self.custom_tags = []

class RepositoryManager:
    def __init__(self, db_path: str = "bug_reports.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the channel-repository mapping table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channel_repos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    repos JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_channel_id ON channel_repos(channel_id)
            ''')
            
            conn.commit()
    
    def add_channel_config(self, channel_id: str, channel_name: str, project_name: str, repos: List[RepositoryConfig]) -> bool:
        """Add or update channel repository configuration"""
        repos_json = json.dumps([{
            'name': repo.name,
            'type': repo.type.value,
            'url': repo.url,
            'token': repo.token,
            'branch': repo.branch,
            'paths': repo.paths,
            'ignore_patterns': repo.ignore_patterns,
            'site_type': repo.site_type,
            'hosting_platform': repo.hosting_platform,
            'business_domain': repo.business_domain,
            'custom_tags': repo.custom_tags
        } for repo in repos])
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO channel_repos 
                (channel_id, channel_name, project_name, repos, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (channel_id, channel_name, project_name, repos_json, datetime.now()))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_channel_config(self, channel_id: str) -> Optional[Dict]:
        """Get repository configuration for a specific channel"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM channel_repos WHERE channel_id = ?
            ''', (channel_id,))
            
            row = cursor.fetchone()
            if row:
                config = dict(row)
                config['repos'] = json.loads(config['repos'])
                return config
            return None
    
    def list_channel_configs(self) -> List[Dict]:
        """List all channel configurations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM channel_repos ORDER BY project_name
            ''')
            
            configs = []
            for row in cursor.fetchall():
                config = dict(row)
                config['repos'] = json.loads(config['repos'])
                configs.append(config)
            
            return configs
    
    def delete_channel_config(self, channel_id: str) -> bool:
        """Delete channel configuration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM channel_repos WHERE channel_id = ?', (channel_id,))
            conn.commit()
            return cursor.rowcount > 0

class CodeAnalyzer:
    """Analyze code changes and repository content"""
    
    def __init__(self, repo_manager: RepositoryManager):
        self.repo_manager = repo_manager
    
    def detect_site_type(self, repo_config: Dict) -> Dict[str, str]:
        """Detect site type and technology stack from repository"""
        # This would analyze the repository structure and files
        # For now, return placeholder detection logic
        detection = {
            'site_type': '',
            'hosting_platform': '',
            'framework': '',
            'language': '',
            'confidence': 'low'
        }
        
        # Example detection logic (would be implemented with actual API calls)
        if repo_config.get('url', '').startswith('https://github.com'):
            # Would fetch repository files and analyze
            detection['site_type'] = 'detected_from_code'
            detection['confidence'] = 'medium'
        
        return detection
    
    def analyze_recent_changes(self, channel_id: str, days: int = 7) -> Dict:
        """Analyze recent code changes for a channel's repositories"""
        config = self.repo_manager.get_channel_config(channel_id)
        if not config:
            return {"error": "No repository configuration found for this channel"}
        
        results = {
            "project": config['project_name'],
            "analysis_date": datetime.now().isoformat(),
            "repositories": []
        }
        
        for repo_config in config['repos']:
            repo_analysis = self._analyze_repository(repo_config, days)
            results["repositories"].append(repo_analysis)
        
        return results
    
    def _analyze_repository(self, repo_config: Dict, days: int) -> Dict:
        """Analyze a single repository"""
        repo_type = RepoType(repo_config['type'])
        
        if repo_type == RepoType.GITHUB:
            return self._analyze_github_repo(repo_config, days)
        elif repo_type == RepoType.AZURE:
            return self._analyze_azure_repo(repo_config, days)
        elif repo_type == RepoType.BITBUCKET:
            return self._analyze_bitbucket_repo(repo_config, days)
        else:
            return {
                "name": repo_config['name'],
                "type": repo_config['type'],
                "error": f"Repository type {repo_config['type']} not yet supported"
            }
    
    def _analyze_github_repo(self, repo_config: Dict, days: int) -> Dict:
        """Analyze GitHub repository"""
        print(f"Analyzing GitHub repo: {repo_config['name']} - {repo_config['url']}")
        try:
            # Get recent commits
            commits = github_analyzer.get_recent_commits(
                repo_config['url'], 
                days=days, 
                branch=repo_config.get('branch', 'main')
            )
            
            # Extract bug-related keywords from the repository metadata
            bug_keywords = self._extract_bug_keywords(repo_config)
            
            # Analyze commit impact
            impact_analysis = github_analyzer.analyze_commit_impact(commits, bug_keywords)
            
            # Get repository stats
            stats = github_analyzer.get_repository_stats(
                repo_config['url'], 
                branch=repo_config.get('branch', 'main')
            )
            
            return {
                "name": repo_config['name'],
                "type": "github",
                "url": repo_config['url'],
                "recent_commits": commits,
                "changed_files": impact_analysis['affected_files'],
                "potential_issues": impact_analysis['high_impact_commits'],
                "impact_analysis": impact_analysis,
                "stats": stats,
                "status": "analyzed"
            }
            
        except Exception as e:
            print(f"Error analyzing GitHub repository: {e}")
            return {
                "name": repo_config['name'],
                "type": "github",
                "url": repo_config['url'],
                "recent_commits": [],
                "changed_files": [],
                "potential_issues": [],
                "status": "error",
                "error": str(e)
            }
    
    def _extract_bug_keywords(self, repo_config: Dict) -> List[str]:
        """Extract bug-related keywords from repository metadata"""
        keywords = []
        
        # Add site type specific keywords
        site_type = repo_config.get('site_type', '').lower()
        if site_type == 'wordpress':
            keywords.extend(['wordpress', 'wp', 'plugin', 'theme', 'hook', 'filter'])
        elif site_type == 'react':
            keywords.extend(['react', 'component', 'state', 'props', 'hook', 'render'])
        elif site_type == 'laravel':
            keywords.extend(['laravel', 'php', 'controller', 'model', 'migration'])
        
        # Add hosting platform specific keywords
        hosting = repo_config.get('hosting_platform', '').lower()
        if hosting == 'wordpress-vip':
            keywords.extend(['vip', 'performance', 'caching', 'cdn'])
        elif hosting == 'netlify':
            keywords.extend(['netlify', 'deploy', 'build', 'function'])
        elif hosting == 'vercel':
            keywords.extend(['vercel', 'deploy', 'build', 'function'])
        
        # Add custom tags as keywords
        custom_tags = repo_config.get('custom_tags', [])
        keywords.extend([tag.lower() for tag in custom_tags])
        
        # Add general bug-related keywords
        general_keywords = ['bug', 'fix', 'issue', 'error', 'performance', 'mobile', 'slow', 'break', 'crash']
        keywords.extend(general_keywords)
        
        return list(set(keywords))  # Remove duplicates
    
    def _analyze_azure_repo(self, repo_config: Dict, days: int) -> Dict:
        """Analyze Azure DevOps repository"""
        print(f"Analyzing Azure repo: {repo_config['name']} - {repo_config['url']}")
        try:
            # Get recent commits
            commits = azure_analyzer.get_recent_commits(
                repo_config['url'], 
                days=days, 
                branch=repo_config.get('branch', 'main')
            )
            
            # Extract bug-related keywords from the repository metadata
            bug_keywords = self._extract_bug_keywords(repo_config)
            
            # Analyze commit impact
            impact_analysis = azure_analyzer.analyze_commit_impact(commits, bug_keywords)
            
            # Get repository stats
            stats = azure_analyzer.get_repository_stats(
                repo_config['url'], 
                branch=repo_config.get('branch', 'main')
            )
            
            return {
                "name": repo_config['name'],
                "type": "azure",
                "url": repo_config['url'],
                "recent_commits": commits,
                "changed_files": impact_analysis['affected_files'],
                "potential_issues": impact_analysis['high_impact_commits'],
                "impact_analysis": impact_analysis,
                "stats": stats,
                "status": "analyzed"
            }
            
        except Exception as e:
            print(f"Error analyzing Azure DevOps repository: {e}")
            return {
                "name": repo_config['name'],
                "type": "azure",
                "url": repo_config['url'],
                "recent_commits": [],
                "changed_files": [],
                "potential_issues": [],
                "status": "error",
                "error": str(e)
            }
    
    def _analyze_bitbucket_repo(self, repo_config: Dict, days: int) -> Dict:
        """Analyze Bitbucket repository"""
        return {
            "name": repo_config['name'],
            "type": "bitbucket",
            "url": repo_config['url'],
            "recent_commits": [],
            "changed_files": [],
            "potential_issues": [],
            "status": "analysis_pending"
        }

# Global instances
repo_manager = RepositoryManager()
code_analyzer = CodeAnalyzer(repo_manager) 