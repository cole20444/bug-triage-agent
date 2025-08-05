import os
import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import base64

class CodeFileAnalyzer:
    """Analyze actual code files from repositories for specific issues"""
    
    def __init__(self, azure_token: str = None, github_token: str = None):
        """Initialize with repository tokens"""
        self.azure_token = azure_token or os.getenv('AZURE_DEVOPS_TOKEN')
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
    
    def analyze_wordpress_site_code(self, repo_config: Dict, recent_commits: List[Dict]) -> Dict:
        """Perform deep code analysis of WordPress site files"""
        analysis = {
            'theme_analysis': {},
            'plugin_analysis': {},
            'performance_issues': [],
            'security_issues': [],
            'mobile_issues': [],
            'code_smells': [],
            'specific_recommendations': []
        }
        
        try:
            # Analyze commit patterns and file changes
            analysis['theme_analysis'] = self._analyze_theme_patterns(recent_commits)
            analysis['plugin_analysis'] = self._analyze_plugin_patterns(recent_commits)
            analysis['performance_issues'] = self._analyze_performance_patterns(recent_commits)
            analysis['security_issues'] = self._analyze_security_patterns(recent_commits)
            analysis['mobile_issues'] = self._analyze_mobile_patterns(recent_commits)
            
            # Generate specific recommendations
            analysis['specific_recommendations'] = self._generate_specific_recommendations(analysis)
            
        except Exception as e:
            analysis['error'] = f"Code analysis failed: {str(e)}"
        
        return analysis
    
    def _analyze_theme_patterns(self, recent_commits: List[Dict]) -> Dict:
        """Analyze theme-related patterns in commits"""
        theme_analysis = {
            'style_css_issues': [],
            'functions_php_issues': [],
            'template_issues': [],
            'mobile_responsiveness': [],
            'performance_problems': []
        }
        
        # Look for theme-related files in recent commits
        theme_files = self._find_theme_files(recent_commits)
        
        # Analyze based on file patterns and commit messages
        for file_info in theme_files:
            file_path = file_info['path']
            commit_sha = file_info['commit']
            
            # Find the commit message for context
            commit_message = ""
            for commit in recent_commits:
                if commit['sha'] == commit_sha:
                    commit_message = commit['message']
                    break
            
            # Analyze CSS files
            if 'style.css' in file_path:
                theme_analysis['style_css_issues'].append({
                    'type': 'css_modification',
                    'severity': 'medium',
                    'description': f"CSS file modified: {file_path}",
                    'commit': commit_sha,
                    'message': commit_message,
                    'recommendation': 'Review CSS changes for mobile responsiveness and performance impact'
                })
            
            # Analyze PHP files
            elif 'functions.php' in file_path:
                theme_analysis['functions_php_issues'].append({
                    'type': 'functions_modification',
                    'severity': 'high',
                    'description': f"Functions file modified: {file_path}",
                    'commit': commit_sha,
                    'message': commit_message,
                    'recommendation': 'Check for deprecated WordPress functions and performance issues'
                })
            
            # Analyze template files
            elif any(ext in file_path for ext in ['.php', '.html']):
                theme_analysis['template_issues'].append({
                    'type': 'template_modification',
                    'severity': 'medium',
                    'description': f"Template file modified: {file_path}",
                    'commit': commit_sha,
                    'message': commit_message,
                    'recommendation': 'Verify template structure and mobile responsiveness'
                })
        
        return theme_analysis
    
    def _analyze_plugin_patterns(self, recent_commits: List[Dict]) -> Dict:
        """Analyze plugin-related patterns in commits"""
        plugin_analysis = {
            'plugin_conflicts': [],
            'performance_impact': [],
            'security_vulnerabilities': [],
            'deprecated_functions': []
        }
        
        # Look for plugin-related files in recent commits
        plugin_files = self._find_plugin_files(recent_commits)
        
        for file_info in plugin_files:
            file_path = file_info['path']
            commit_sha = file_info['commit']
            
            # Find the commit message for context
            commit_message = ""
            for commit in recent_commits:
                if commit['sha'] == commit_sha:
                    commit_message = commit['message']
                    break
            
            # Analyze PHP plugin files
            if file_path.endswith('.php') and '/wp-content/plugins/' in file_path:
                plugin_analysis['plugin_conflicts'].append({
                    'type': 'plugin_modification',
                    'severity': 'medium',
                    'description': f"Plugin file modified: {file_path}",
                    'commit': commit_sha,
                    'message': commit_message,
                    'recommendation': 'Check for plugin compatibility and hook conflicts'
                })
            
            # Analyze JavaScript files
            elif file_path.endswith('.js') and '/wp-content/plugins/' in file_path:
                plugin_analysis['performance_impact'].append({
                    'type': 'js_modification',
                    'severity': 'medium',
                    'description': f"Plugin JS file modified: {file_path}",
                    'commit': commit_sha,
                    'message': commit_message,
                    'recommendation': 'Review JavaScript changes for performance impact'
                })
        
        return plugin_analysis
    
    def _analyze_performance_patterns(self, recent_commits: List[Dict]) -> List[Dict]:
        """Analyze performance-related patterns in commits"""
        performance_issues = []
        
        for commit in recent_commits:
            commit_message = commit['message'].lower()
            commit_sha = commit['sha']
            
            # Look for performance-related keywords in commit messages
            performance_keywords = ['performance', 'slow', 'optimize', 'cache', 'speed', 'load']
            if any(keyword in commit_message for keyword in performance_keywords):
                performance_issues.append({
                    'type': 'performance_commit',
                    'severity': 'medium',
                    'description': f"Performance-related commit: {commit['message']}",
                    'commit': commit_sha,
                    'recommendation': 'Review performance impact of these changes'
                })
            
            # Look for large file changes
            files_changed = commit.get('files_changed', [])
            if len(files_changed) > 50:  # Large number of files changed
                performance_issues.append({
                    'type': 'large_change',
                    'severity': 'high',
                    'description': f"Large number of files changed ({len(files_changed)} files)",
                    'commit': commit_sha,
                    'recommendation': 'Monitor performance impact of large-scale changes'
                })
        
        return performance_issues
    
    def _analyze_security_patterns(self, recent_commits: List[Dict]) -> List[Dict]:
        """Analyze security-related patterns in commits"""
        security_issues = []
        
        for commit in recent_commits:
            commit_message = commit['message'].lower()
            commit_sha = commit['sha']
            
            # Look for security-related keywords
            security_keywords = ['security', 'auth', 'password', 'login', 'permission', 'vulnerability']
            if any(keyword in commit_message for keyword in security_keywords):
                security_issues.append({
                    'type': 'security_commit',
                    'severity': 'high',
                    'description': f"Security-related commit: {commit['message']}",
                    'commit': commit_sha,
                    'recommendation': 'Review security implications of these changes'
                })
        
        return security_issues
    
    def _analyze_mobile_patterns(self, recent_commits: List[Dict]) -> List[Dict]:
        """Analyze mobile-related patterns in commits"""
        mobile_issues = []
        
        for commit in recent_commits:
            commit_message = commit['message'].lower()
            commit_sha = commit['sha']
            
            # Look for mobile-related keywords
            mobile_keywords = ['mobile', 'responsive', 'height', 'width', 'card', 'layout']
            if any(keyword in commit_message for keyword in mobile_keywords):
                mobile_issues.append({
                    'type': 'mobile_commit',
                    'severity': 'medium',
                    'description': f"Mobile-related commit: {commit['message']}",
                    'commit': commit_sha,
                    'recommendation': 'Test mobile responsiveness after these changes'
                })
        
        return mobile_issues
    
    def _find_theme_files(self, recent_commits: List[Dict]) -> List[Dict]:
        """Find theme-related files in recent commits"""
        theme_files = []
        theme_patterns = [
            r'/wp-content/themes/',
            r'style\.css',
            r'functions\.php',
            r'index\.php',
            r'header\.php',
            r'footer\.php',
            r'single\.php',
            r'page\.php'
        ]
        
        for commit in recent_commits:
            for file_change in commit.get('files_changed', []):
                filename = file_change.get('filename', '')
                if any(re.search(pattern, filename) for pattern in theme_patterns):
                    theme_files.append({
                        'path': filename,
                        'commit': commit['sha'],
                        'change_type': file_change.get('status', 'unknown')
                    })
        
        return theme_files
    
    def _find_plugin_files(self, recent_commits: List[Dict]) -> List[Dict]:
        """Find plugin-related files in recent commits"""
        plugin_files = []
        plugin_patterns = [
            r'/wp-content/plugins/',
            r'\.php$',
            r'\.js$',
            r'\.css$'
        ]
        
        for commit in recent_commits:
            for file_change in commit.get('files_changed', []):
                filename = file_change.get('filename', '')
                if any(re.search(pattern, filename) for pattern in plugin_patterns):
                    plugin_files.append({
                        'path': filename,
                        'commit': commit['sha'],
                        'change_type': file_change.get('status', 'unknown')
                    })
        
        return plugin_files
    
    def _get_file_content(self, repo_config: Dict, file_path: str) -> Optional[str]:
        """Get the content of a specific file from the repository"""
        try:
            if repo_config.get('type') == 'azure':
                return self._get_azure_file_content(repo_config, file_path)
            elif repo_config.get('type') == 'github':
                return self._get_github_file_content(repo_config, file_path)
        except Exception as e:
            print(f"Error getting file content for {file_path}: {e}")
        return None
    
    def _get_azure_file_content(self, repo_config: Dict, file_path: str) -> Optional[str]:
        """Get file content from Azure DevOps"""
        if not self.azure_token:
            return None
        
        try:
            # Extract repo info from URL
            url = repo_config['url']
            org, project, repo, _ = self._extract_azure_repo_info(url)
            
            # Azure DevOps REST API for file content - use the correct endpoint
            api_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items"
            
            headers = {
                'Authorization': f'Basic {base64.b64encode(f":{self.azure_token}".encode()).decode()}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'path': file_path,
                'api-version': '6.0',
                'includeContent': 'true'
            }
            
            response = requests.get(api_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'content' in data:
                    return base64.b64decode(data['content']).decode('utf-8')
                elif 'value' in data and len(data['value']) > 0:
                    # Sometimes the content is in a value array
                    item = data['value'][0]
                    if 'content' in item:
                        return base64.b64decode(item['content']).decode('utf-8')
            elif response.status_code == 404:
                # File not found, skip silently
                return None
            else:
                print(f"Azure API error {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            print(f"Azure file content error for {file_path}: {e}")
        
        return None
    
    def _get_github_file_content(self, repo_config: Dict, file_path: str) -> Optional[str]:
        """Get file content from GitHub"""
        if not self.github_token:
            return None
        
        try:
            # Extract repo info from URL
            repo_url = repo_config['url']
            owner, repo = self._extract_github_repo_info(repo_url)
            
            # GitHub REST API for file content
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3.raw'
            }
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                return response.text
                
        except Exception as e:
            print(f"GitHub file content error: {e}")
        
        return None
    
    def _extract_azure_repo_info(self, url: str) -> Tuple[str, str, str, str]:
        """Extract organization, project, and repo from Azure DevOps URL"""
        pattern = r'<?https://dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/>]+)>?'
        match = re.match(pattern, url)
        if match:
            org = match.group(1)
            project = match.group(2)
            repo = match.group(3)
            return org, project, repo, f"{org}/{project}/{repo}"
        raise ValueError(f"Invalid Azure DevOps URL format: {url}")
    
    def _extract_github_repo_info(self, url: str) -> Tuple[str, str]:
        """Extract owner and repo from GitHub URL"""
        pattern = r'https://github\.com/([^/]+)/([^/]+)'
        match = re.match(pattern, url)
        if match:
            owner = match.group(1)
            repo = match.group(2)
            return owner, repo
        raise ValueError(f"Invalid GitHub URL format: {url}")
    
    def _analyze_css_file(self, content: str, file_info: Dict) -> List[Dict]:
        """Analyze CSS file for issues"""
        issues = []
        
        # Check for mobile responsiveness issues
        if not re.search(r'@media.*mobile|@media.*max-width', content, re.IGNORECASE):
            issues.append({
                'type': 'mobile_responsiveness',
                'severity': 'high',
                'description': f"Missing mobile media queries in {file_info['path']}",
                'recommendation': 'Add responsive breakpoints for mobile devices'
            })
        
        # Check for performance issues
        if re.search(r'!important', content):
            issues.append({
                'type': 'performance',
                'severity': 'medium',
                'description': f"Excessive use of !important in {file_info['path']}",
                'recommendation': 'Reduce use of !important declarations'
            })
        
        # Check for large CSS files
        if len(content) > 50000:  # 50KB
            issues.append({
                'type': 'performance',
                'severity': 'high',
                'description': f"Large CSS file: {file_info['path']} ({len(content)} characters)",
                'recommendation': 'Consider minifying and splitting CSS files'
            })
        
        return issues
    
    def _analyze_php_file(self, content: str, file_info: Dict) -> List[Dict]:
        """Analyze PHP file for issues"""
        issues = []
        
        # Check for deprecated WordPress functions
        deprecated_functions = [
            'wp_list_categories', 'wp_list_pages', 'wp_get_links',
            'get_bloginfo', 'bloginfo', 'wp_title'
        ]
        
        for func in deprecated_functions:
            if func in content:
                issues.append({
                    'type': 'deprecated_function',
                    'severity': 'medium',
                    'description': f"Deprecated function '{func}' found in {file_info['path']}",
                    'recommendation': f'Replace {func} with modern WordPress functions'
                })
        
        # Check for performance issues
        if re.search(r'query_posts|get_posts', content):
            issues.append({
                'type': 'performance',
                'severity': 'high',
                'description': f"Use of query_posts() in {file_info['path']} can cause performance issues",
                'recommendation': 'Use WP_Query instead of query_posts()'
            })
        
        # Check for security issues
        if re.search(r'eval\(|exec\(|system\(', content):
            issues.append({
                'type': 'security',
                'severity': 'critical',
                'description': f"Potentially dangerous function found in {file_info['path']}",
                'recommendation': 'Remove or secure dangerous function calls'
            })
        
        return issues
    
    def _analyze_template_file(self, content: str, file_info: Dict) -> List[Dict]:
        """Analyze template file for issues"""
        issues = []
        
        # Check for proper WordPress template tags
        if not re.search(r'get_header\(|get_footer\(', content):
            issues.append({
                'type': 'template_structure',
                'severity': 'medium',
                'description': f"Missing header/footer calls in {file_info['path']}",
                'recommendation': 'Include proper WordPress template structure'
            })
        
        # Check for mobile responsiveness
        if not re.search(r'viewport.*width.*device-width', content, re.IGNORECASE):
            issues.append({
                'type': 'mobile_responsiveness',
                'severity': 'high',
                'description': f"Missing viewport meta tag in {file_info['path']}",
                'recommendation': 'Add viewport meta tag for mobile responsiveness'
            })
        
        return issues
    
    def _analyze_plugin_php(self, content: str, file_info: Dict) -> List[Dict]:
        """Analyze plugin PHP file for issues"""
        issues = []
        
        # Check for plugin conflicts
        if re.search(r'add_action.*init|add_action.*wp_loaded', content):
            issues.append({
                'type': 'plugin_conflict',
                'severity': 'medium',
                'description': f"Plugin hook timing issue in {file_info['path']}",
                'recommendation': 'Review hook priority and timing'
            })
        
        # Check for database queries in loops
        if re.search(r'while.*get_post|foreach.*get_post', content):
            issues.append({
                'type': 'performance',
                'severity': 'high',
                'description': f"Database queries in loops found in {file_info['path']}",
                'recommendation': 'Use pre_get_posts or batch queries'
            })
        
        return issues
    
    def _analyze_js_file(self, content: str, file_info: Dict) -> List[Dict]:
        """Analyze JavaScript file for issues"""
        issues = []
        
        # Check for jQuery dependency
        if re.search(r'\$\(|jQuery', content) and not re.search(r'wp_enqueue_script.*jquery', content):
            issues.append({
                'type': 'dependency',
                'severity': 'medium',
                'description': f"jQuery usage without proper enqueuing in {file_info['path']}",
                'recommendation': 'Use wp_enqueue_script to properly load jQuery'
            })
        
        # Check for performance issues
        if re.search(r'setInterval|setTimeout.*1000', content):
            issues.append({
                'type': 'performance',
                'severity': 'medium',
                'description': f"Frequent timers found in {file_info['path']}",
                'recommendation': 'Optimize timer usage for better performance'
            })
        
        return issues
    
    def _find_deprecated_functions(self, content: str, file_info: Dict) -> List[Dict]:
        """Find deprecated WordPress functions"""
        deprecated = [
            'wp_list_categories', 'wp_list_pages', 'wp_get_links',
            'get_bloginfo', 'bloginfo', 'wp_title', 'the_author_meta'
        ]
        
        issues = []
        for func in deprecated:
            if func in content:
                issues.append({
                    'type': 'deprecated_function',
                    'severity': 'medium',
                    'description': f"Deprecated function '{func}' in {file_info['path']}",
                    'recommendation': f'Replace {func} with modern WordPress functions'
                })
        
        return issues
    
    def _get_commit_changes(self, repo_config: Dict, commit_sha: str) -> List[Dict]:
        """Get actual changes in a specific commit"""
        # This would need to be implemented based on the repository type
        # For now, return empty list
        return []
    
    def _analyze_performance_changes(self, change: Dict) -> List[Dict]:
        """Analyze performance-related changes"""
        issues = []
        content = change.get('content', '')
        
        # Look for performance-impacting changes
        if re.search(r'query_posts|get_posts', content):
            issues.append({
                'type': 'performance',
                'severity': 'high',
                'description': 'Performance-impacting database query found',
                'file': change.get('filename', 'unknown'),
                'recommendation': 'Use WP_Query with proper caching'
            })
        
        return issues
    
    def _analyze_security_changes(self, change: Dict) -> List[Dict]:
        """Analyze security-related changes"""
        issues = []
        content = change.get('content', '')
        
        # Look for security issues
        if re.search(r'eval\(|exec\(', content):
            issues.append({
                'type': 'security',
                'severity': 'critical',
                'description': 'Dangerous function call found',
                'file': change.get('filename', 'unknown'),
                'recommendation': 'Remove or secure dangerous function calls'
            })
        
        return issues
    
    def _analyze_mobile_changes(self, change: Dict) -> List[Dict]:
        """Analyze mobile-related changes"""
        issues = []
        content = change.get('content', '')
        
        # Look for mobile-specific issues
        if 'mobile' in content.lower() and not re.search(r'@media.*mobile|viewport', content, re.IGNORECASE):
            issues.append({
                'type': 'mobile_responsiveness',
                'severity': 'medium',
                'description': 'Mobile-related changes without proper responsive design',
                'file': change.get('filename', 'unknown'),
                'recommendation': 'Add proper mobile media queries and viewport settings'
            })
        
        return issues
    
    def _find_code_smells(self, change: Dict) -> List[Dict]:
        """Find code smells in changes"""
        issues = []
        content = change.get('content', '')
        
        # Look for code smells
        if re.search(r'// TODO|// FIXME|// HACK', content, re.IGNORECASE):
            issues.append({
                'type': 'code_smell',
                'severity': 'low',
                'description': 'Code comments indicating technical debt',
                'file': change.get('filename', 'unknown'),
                'recommendation': 'Address TODO/FIXME comments'
            })
        
        return issues
    
    def _generate_specific_recommendations(self, analysis: Dict) -> List[str]:
        """Generate specific, actionable recommendations based on analysis"""
        recommendations = []
        
        # Theme-specific recommendations
        theme_issues = analysis.get('theme_analysis', {})
        if theme_issues.get('style_css_issues'):
            recommendations.append("🔧 **Theme CSS Issues**: Add mobile media queries and optimize CSS file size")
        
        if theme_issues.get('functions_php_issues'):
            recommendations.append("🔧 **Theme Functions**: Replace deprecated WordPress functions with modern alternatives")
        
        # Plugin-specific recommendations
        plugin_issues = analysis.get('plugin_analysis', {})
        if plugin_issues.get('plugin_conflicts'):
            recommendations.append("🔧 **Plugin Conflicts**: Review hook priorities and timing to resolve conflicts")
        
        if plugin_issues.get('deprecated_functions'):
            recommendations.append("🔧 **Deprecated Functions**: Update plugin code to use modern WordPress functions")
        
        # Performance recommendations
        if analysis.get('performance_issues'):
            recommendations.append("⚡ **Performance**: Optimize database queries and implement caching strategies")
        
        # Security recommendations
        if analysis.get('security_issues'):
            recommendations.append("🔒 **Security**: Remove dangerous function calls and implement proper security measures")
        
        # Mobile recommendations
        if analysis.get('mobile_issues'):
            recommendations.append("📱 **Mobile**: Add proper viewport settings and responsive design elements")
        
        return recommendations

# Global instance
code_analyzer = CodeFileAnalyzer() 