import sqlite3
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

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
    
    def __post_init__(self):
        if self.paths is None:
            self.paths = []
        if self.ignore_patterns is None:
            self.ignore_patterns = []

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
            'ignore_patterns': repo.ignore_patterns
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
        # This would integrate with GitHub API
        # For now, return placeholder structure
        return {
            "name": repo_config['name'],
            "type": "github",
            "url": repo_config['url'],
            "recent_commits": [],
            "changed_files": [],
            "potential_issues": [],
            "status": "analysis_pending"
        }
    
    def _analyze_azure_repo(self, repo_config: Dict, days: int) -> Dict:
        """Analyze Azure DevOps repository"""
        return {
            "name": repo_config['name'],
            "type": "azure",
            "url": repo_config['url'],
            "recent_commits": [],
            "changed_files": [],
            "potential_issues": [],
            "status": "analysis_pending"
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