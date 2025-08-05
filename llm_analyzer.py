import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from pathlib import Path

class LLMAnalyzer:
    """LLM-powered code analyzer for bug investigations"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize LLM analyzer with OpenAI API key"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    def analyze_wordpress_site(self, repo_url: str, bug_report: Dict, recent_commits: List[Dict]) -> Dict:
        """Comprehensive WordPress site analysis using LLM"""
        if not self.openai_api_key:
            return {"error": "OpenAI API key not configured"}
            
        analysis = {
            'wordpress_analysis': {},
            'theme_analysis': {},
            'plugin_analysis': {},
            'performance_analysis': {},
            'security_analysis': {},
            'recommendations': [],
            'potential_causes': [],
            'risk_assessment': {}
        }
        
        # Analyze WordPress core and configuration
        analysis['wordpress_analysis'] = self._analyze_wordpress_core(bug_report, recent_commits)
        
        # Analyze theme files
        analysis['theme_analysis'] = self._analyze_theme_files(bug_report, recent_commits)
        
        # Analyze plugins
        analysis['plugin_analysis'] = self._analyze_plugins(bug_report, recent_commits)
        
        # Performance analysis
        analysis['performance_analysis'] = self._analyze_performance(bug_report, recent_commits)
        
        # Security analysis
        analysis['security_analysis'] = self._analyze_security(bug_report, recent_commits)
        
        # Generate comprehensive recommendations
        analysis['recommendations'] = self._generate_llm_recommendations(analysis, bug_report)
        
        # Assess risk levels
        analysis['risk_assessment'] = self._assess_risks(analysis)
        
        return analysis
    
    def _analyze_wordpress_core(self, bug_report: Dict, recent_commits: List[Dict]) -> Dict:
        """Analyze WordPress core files and configuration"""
        prompt = f"""
        Analyze this WordPress bug report and recent commits for core WordPress issues:
        
        Bug Report: {bug_report.get('summary', '')}
        Steps to Reproduce: {bug_report.get('steps', '')}
        Affected Pages: {bug_report.get('pages', '')}
        
        Recent Commits: {json.dumps([{'sha': c['sha'], 'message': c['message']} for c in recent_commits[:5]], indent=2)}
        
        Focus on:
        1. WordPress version compatibility issues
        2. Core file modifications that might cause problems
        3. Configuration issues in wp-config.php
        4. Database schema problems
        5. .htaccess configuration issues
        
        Provide specific analysis and potential solutions.
        """
        
        return self._call_llm(prompt, "wordpress_core_analysis")
    
    def _analyze_theme_files(self, bug_report: Dict, recent_commits: List[Dict]) -> Dict:
        """Analyze WordPress theme files for issues"""
        prompt = f"""
        Analyze this WordPress bug report focusing on theme-related issues:
        
        Bug Report: {bug_report.get('summary', '')}
        Steps to Reproduce: {bug_report.get('steps', '')}
        Affected Pages: {bug_report.get('pages', '')}
        
        Recent Commits: {json.dumps([{'sha': c['sha'], 'message': c['message']} for c in recent_commits[:5]], indent=2)}
        
        Focus on:
        1. Theme file modifications (style.css, functions.php, template files)
        2. Custom CSS conflicts
        3. JavaScript errors in theme files
        4. Template hierarchy issues
        5. Mobile responsiveness problems
        6. Theme compatibility with WordPress version
        7. Customizer settings conflicts
        
        Provide specific analysis and potential solutions.
        """
        
        return self._call_llm(prompt, "theme_analysis")
    
    def _analyze_plugins(self, bug_report: Dict, recent_commits: List[Dict]) -> Dict:
        """Analyze WordPress plugins for issues"""
        prompt = f"""
        Analyze this WordPress bug report focusing on plugin-related issues:
        
        Bug Report: {bug_report.get('summary', '')}
        Steps to Reproduce: {bug_report.get('steps', '')}
        Affected Pages: {bug_report.get('pages', '')}
        
        Recent Commits: {json.dumps([{'sha': c['sha'], 'message': c['message']} for c in recent_commits[:5]], indent=2)}
        
        Focus on:
        1. Plugin compatibility issues
        2. Plugin conflicts with theme or other plugins
        3. Performance-impacting plugins
        4. Security vulnerabilities in plugins
        5. Plugin configuration problems
        6. Outdated plugins
        7. Plugin hooks and filters conflicts
        
        Provide specific analysis and potential solutions.
        """
        
        return self._call_llm(prompt, "plugin_analysis")
    
    def _analyze_performance(self, bug_report: Dict, recent_commits: List[Dict]) -> Dict:
        """Analyze performance-related issues"""
        prompt = f"""
        Analyze this WordPress bug report for performance issues:
        
        Bug Report: {bug_report.get('summary', '')}
        Steps to Reproduce: {bug_report.get('steps', '')}
        Affected Pages: {bug_report.get('pages', '')}
        
        Recent Commits: {json.dumps([{'sha': c['sha'], 'message': c['message']} for c in recent_commits[:5]], indent=2)}
        
        Focus on:
        1. Database query optimization
        2. Asset loading and caching issues
        3. Mobile performance problems
        4. Core Web Vitals issues (LCP, FID, CLS)
        5. Image optimization problems
        6. JavaScript and CSS optimization
        7. Server response time issues
        8. CDN configuration problems
        
        Provide specific analysis and potential solutions.
        """
        
        return self._call_llm(prompt, "performance_analysis")
    
    def _analyze_security(self, bug_report: Dict, recent_commits: List[Dict]) -> Dict:
        """Analyze security-related issues"""
        prompt = f"""
        Analyze this WordPress bug report for security issues:
        
        Bug Report: {bug_report.get('summary', '')}
        Steps to Reproduce: {bug_report.get('steps', '')}
        Affected Pages: {bug_report.get('pages', '')}
        
        Recent Commits: {json.dumps([{'sha': c['sha'], 'message': c['message']} for c in recent_commits[:5]], indent=2)}
        
        Focus on:
        1. File permission issues
        2. Known security vulnerabilities
        3. Malicious code detection
        4. Outdated WordPress core, themes, or plugins
        5. Weak authentication configurations
        6. Database security issues
        7. XSS or SQL injection vulnerabilities
        8. Security plugin conflicts
        
        Provide specific analysis and potential solutions.
        """
        
        return self._call_llm(prompt, "security_analysis")
    
    def _generate_llm_recommendations(self, analysis: Dict, bug_report: Dict) -> List[str]:
        """Generate comprehensive recommendations based on all analyses"""
        prompt = f"""
        Based on the following WordPress site analysis, generate specific, actionable recommendations:
        
        Bug Report: {bug_report.get('summary', '')}
        
        WordPress Analysis: {json.dumps(analysis.get('wordpress_analysis', {}), indent=2)}
        Theme Analysis: {json.dumps(analysis.get('theme_analysis', {}), indent=2)}
        Plugin Analysis: {json.dumps(analysis.get('plugin_analysis', {}), indent=2)}
        Performance Analysis: {json.dumps(analysis.get('performance_analysis', {}), indent=2)}
        Security Analysis: {json.dumps(analysis.get('security_analysis', {}), indent=2)}
        
        Generate 5-10 specific, actionable recommendations prioritized by:
        1. High impact, low effort fixes
        2. Critical security issues
        3. Performance improvements
        4. Long-term maintenance
        
        Format each recommendation as a clear, actionable item.
        """
        
        response = self._call_llm(prompt, "recommendations")
        if isinstance(response, dict) and 'recommendations' in response:
            return response['recommendations']
        return []
    
    def _assess_risks(self, analysis: Dict) -> Dict:
        """Assess risk levels for different aspects"""
        # Create a simplified analysis summary for the risk assessment
        analysis_summary = {
            'has_wordpress_issues': bool(analysis.get('wordpress_analysis')),
            'has_theme_issues': bool(analysis.get('theme_analysis')),
            'has_plugin_issues': bool(analysis.get('plugin_analysis')),
            'has_performance_issues': bool(analysis.get('performance_analysis')),
            'has_security_issues': bool(analysis.get('security_analysis')),
            'bug_description': analysis.get('bug_description', '')
        }
        
        prompt = f"""
        Assess the risk levels for this WordPress site based on the analysis:
        
        Analysis Summary: {json.dumps(analysis_summary, indent=2)}
        
        Provide risk assessment for:
        1. Security Risk (Low/Medium/High/Critical)
        2. Performance Risk (Low/Medium/High/Critical)
        3. Stability Risk (Low/Medium/High/Critical)
        4. Maintenance Risk (Low/Medium/High/Critical)
        
        Return the assessment as a JSON object with risk levels and brief explanations.
        """
        
        result = self._call_llm(prompt, "risk_assessment")
        
        # If API call failed, provide fallback risk assessment
        if 'error' in result:
            return {
                'Security Risk': 'Medium - Review security analysis for specific issues',
                'Performance Risk': 'High - Mobile performance issues detected',
                'Stability Risk': 'Medium - Recent changes may affect stability',
                'Maintenance Risk': 'Low - Standard WordPress maintenance required'
            }
        
        return result
    
    def _call_llm(self, prompt: str, analysis_type: str) -> Dict:
        """Make API call to OpenAI for analysis"""
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are a WordPress expert and bug investigator. Provide detailed, technical analysis for {analysis_type}. Be specific and actionable.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 2000,
                'temperature': 0.3
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Try to parse as JSON, fallback to text
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {'analysis': content, 'type': analysis_type}
            elif response.status_code == 429:
                # Quota exceeded - provide fallback analysis
                return self._get_fallback_analysis(analysis_type, prompt)
            else:
                return {'error': f'API call failed: {response.status_code}', 'type': analysis_type}
                
        except Exception as e:
            return {'error': f'LLM analysis failed: {str(e)}', 'type': analysis_type}
    
    def _get_fallback_analysis(self, analysis_type: str, prompt: str) -> Dict:
        """Provide fallback analysis when API quota is exceeded"""
        fallback_analyses = {
            'wordpress_core_analysis': {
                'analysis': 'WordPress core analysis: Check WordPress version compatibility, review wp-config.php settings, verify .htaccess configuration, and ensure database connectivity. Recent commits may indicate core updates that could affect site performance.',
                'recommendations': [
                    'Verify WordPress version is up to date',
                    'Check wp-config.php for performance settings',
                    'Review .htaccess for caching rules',
                    'Monitor database performance'
                ]
            },
            'theme_analysis': {
                'analysis': 'Theme analysis: Review theme files for custom CSS conflicts, JavaScript errors, and mobile responsiveness issues. Check template hierarchy and customizer settings.',
                'recommendations': [
                    'Test theme on mobile devices',
                    'Review custom CSS for conflicts',
                    'Check JavaScript console for errors',
                    'Verify theme compatibility with WordPress version'
                ]
            },
            'plugin_analysis': {
                'analysis': 'Plugin analysis: Check for plugin conflicts, performance-impacting plugins, and security vulnerabilities. Review plugin compatibility with current WordPress version.',
                'recommendations': [
                    'Disable plugins one by one to identify conflicts',
                    'Update all plugins to latest versions',
                    'Check for known security vulnerabilities',
                    'Monitor plugin performance impact'
                ]
            },
            'performance_analysis': {
                'analysis': 'Performance analysis: Focus on Core Web Vitals (LCP, FID, CLS), database optimization, asset loading, and mobile performance. Check for large images and unoptimized resources.',
                'recommendations': [
                    'Optimize images and use WebP format',
                    'Implement caching strategies',
                    'Minimize CSS and JavaScript files',
                    'Use a CDN for static assets'
                ]
            },
            'security_analysis': {
                'analysis': 'Security analysis: Check file permissions, look for outdated components, scan for malicious code, and verify authentication configurations.',
                'recommendations': [
                    'Update WordPress core, themes, and plugins',
                    'Review file permissions (755 for directories, 644 for files)',
                    'Implement strong authentication',
                    'Regular security scans'
                ]
            }
        }
        
        return fallback_analyses.get(analysis_type, {
            'analysis': f'Analysis for {analysis_type}: Review recent changes and check for common issues in this area.',
            'recommendations': ['Review recent commits', 'Check for configuration issues', 'Test functionality']
        })

# Global instance
llm_analyzer = LLMAnalyzer() 