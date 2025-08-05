import re
from typing import Dict, List, Set
from enum import Enum

class IssueType(Enum):
    PERFORMANCE = "performance"
    MOBILE = "mobile"
    SECURITY = "security"
    FUNCTIONALITY = "functionality"
    UI_UX = "ui_ux"
    COMPATIBILITY = "compatibility"
    DATABASE = "database"
    CACHING = "caching"
    LOADING = "loading"
    RESPONSIVE = "responsive"

class IssueFocusedAnalyzer:
    """Analyze issues with focus on the specific problem being reported"""
    
    def __init__(self):
        # Define issue keywords and their corresponding analysis types
        self.issue_patterns = {
            IssueType.PERFORMANCE: [
                'slow', 'performance', 'speed', 'loading', 'load time', 'slowdown',
                'lag', 'delay', 'timeout', 'core web vitals', 'lighthouse',
                'page speed', 'optimization', 'bottleneck'
            ],
            IssueType.MOBILE: [
                'mobile', 'phone', 'tablet', 'responsive', 'viewport',
                'mobile device', 'mobile browser', 'touch', 'swipe',
                'mobile load', 'mobile performance', 'mobile slow'
            ],
            IssueType.SECURITY: [
                'security', 'vulnerability', 'hack', 'breach', 'malware',
                'virus', 'attack', 'unauthorized', 'permission', 'access',
                'login', 'password', 'authentication'
            ],
            IssueType.FUNCTIONALITY: [
                'broken', 'not working', 'error', 'crash', 'bug', 'issue',
                'fails', 'doesn\'t work', 'broken link', '404', '500 error',
                'white screen', 'blank page'
            ],
            IssueType.UI_UX: [
                'design', 'layout', 'appearance', 'looks', 'visual',
                'styling', 'css', 'frontend', 'user interface', 'ui',
                'user experience', 'ux', 'design issue'
            ],
            IssueType.COMPATIBILITY: [
                'browser', 'chrome', 'firefox', 'safari', 'edge',
                'compatibility', 'works in', 'doesn\'t work in',
                'version', 'update', 'upgrade'
            ],
            IssueType.DATABASE: [
                'database', 'query', 'sql', 'mysql', 'postgresql',
                'data', 'content', 'posts', 'pages', 'admin',
                'backend', 'server', 'api'
            ],
            IssueType.CACHING: [
                'cache', 'caching', 'cdn', 'static', 'assets',
                'images', 'files', 'resources', 'minification'
            ],
            IssueType.LOADING: [
                'loading', 'load', 'load time', 'page load',
                'initial load', 'first load', 'subsequent load',
                'loading speed', 'load performance'
            ],
            IssueType.RESPONSIVE: [
                'responsive', 'responsive design', 'breakpoint',
                'media query', 'mobile first', 'adaptive',
                'flexible', 'fluid', 'grid'
            ]
        }
    
    def analyze_bug_report(self, bug_report: Dict) -> Dict:
        """Analyze bug report to determine the primary issue type and focus areas"""
        summary = bug_report.get('summary', '').lower()
        description = bug_report.get('description', '').lower()
        full_text = f"{summary} {description}"
        
        # Determine primary issue type
        primary_issue = self._identify_primary_issue(full_text)
        
        # Get relevant analysis areas
        analysis_areas = self._get_relevant_analysis_areas(primary_issue)
        
        # Get focused keywords for this issue
        focused_keywords = self._get_focused_keywords(primary_issue)
        
        return {
            'primary_issue': primary_issue,
            'analysis_areas': analysis_areas,
            'focused_keywords': focused_keywords,
            'issue_confidence': self._calculate_confidence(full_text, primary_issue),
            'related_issues': self._identify_related_issues(full_text)
        }
    
    def _identify_primary_issue(self, text: str) -> IssueType:
        """Identify the primary issue type from the bug report text"""
        issue_scores = {}
        
        for issue_type, keywords in self.issue_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            issue_scores[issue_type] = score
        
        # Return the issue type with the highest score
        if issue_scores:
            return max(issue_scores.items(), key=lambda x: x[1])[0]
        
        return IssueType.FUNCTIONALITY  # Default fallback
    
    def _get_relevant_analysis_areas(self, primary_issue: IssueType) -> List[str]:
        """Get the analysis areas that are relevant to the primary issue"""
        analysis_mapping = {
            IssueType.PERFORMANCE: [
                'performance_analysis',
                'database_queries',
                'caching_analysis',
                'asset_optimization',
                'server_response_times'
            ],
            IssueType.MOBILE: [
                'mobile_responsiveness',
                'viewport_analysis',
                'touch_interactions',
                'mobile_performance',
                'responsive_design'
            ],
            IssueType.SECURITY: [
                'security_vulnerabilities',
                'authentication_issues',
                'permission_checks',
                'input_validation',
                'secure_coding'
            ],
            IssueType.FUNCTIONALITY: [
                'code_errors',
                'logic_issues',
                'api_endpoints',
                'database_connections',
                'error_handling'
            ],
            IssueType.UI_UX: [
                'css_analysis',
                'layout_issues',
                'design_consistency',
                'user_interface',
                'frontend_performance'
            ],
            IssueType.COMPATIBILITY: [
                'browser_compatibility',
                'version_specific_issues',
                'cross_platform_testing',
                'feature_detection'
            ],
            IssueType.DATABASE: [
                'database_queries',
                'data_integrity',
                'connection_issues',
                'query_optimization'
            ],
            IssueType.CACHING: [
                'cache_configuration',
                'cache_invalidation',
                'static_asset_caching',
                'cdn_analysis'
            ],
            IssueType.LOADING: [
                'page_load_optimization',
                'resource_loading',
                'critical_rendering_path',
                'lazy_loading'
            ],
            IssueType.RESPONSIVE: [
                'responsive_design',
                'media_queries',
                'breakpoint_analysis',
                'mobile_layout'
            ]
        }
        
        return analysis_mapping.get(primary_issue, ['general_analysis'])
    
    def _get_focused_keywords(self, primary_issue: IssueType) -> List[str]:
        """Get focused keywords relevant to the specific issue type"""
        focused_keywords = {
            IssueType.PERFORMANCE: [
                'query_posts', 'get_posts', 'wp_query', 'database', 'cache',
                'optimization', 'performance', 'slow', 'speed', 'loading',
                'assets', 'images', 'scripts', 'css', 'minification'
            ],
            IssueType.MOBILE: [
                'mobile', 'responsive', 'viewport', 'media query', 'breakpoint',
                'touch', 'swipe', 'mobile device', 'mobile browser',
                'height', 'width', 'layout', 'cards', 'mobile load'
            ],
            IssueType.SECURITY: [
                'eval', 'exec', 'system', 'sql injection', 'xss',
                'csrf', 'authentication', 'authorization', 'permission',
                'input validation', 'sanitization', 'escaping'
            ],
            IssueType.FUNCTIONALITY: [
                'error', 'exception', 'crash', 'broken', 'not working',
                'fails', 'bug', 'issue', '404', '500', 'white screen'
            ],
            IssueType.UI_UX: [
                'css', 'styling', 'layout', 'design', 'appearance',
                'frontend', 'user interface', 'visual', 'looks'
            ],
            IssueType.COMPATIBILITY: [
                'browser', 'chrome', 'firefox', 'safari', 'edge',
                'version', 'compatibility', 'works in', 'doesn\'t work in'
            ],
            IssueType.DATABASE: [
                'database', 'query', 'sql', 'mysql', 'connection',
                'data', 'content', 'posts', 'pages', 'admin'
            ],
            IssueType.CACHING: [
                'cache', 'caching', 'cdn', 'static', 'assets',
                'minification', 'compression', 'cache invalidation'
            ],
            IssueType.LOADING: [
                'loading', 'load time', 'page load', 'initial load',
                'first load', 'subsequent load', 'loading speed'
            ],
            IssueType.RESPONSIVE: [
                'responsive', 'media query', 'breakpoint', 'mobile first',
                'adaptive', 'flexible', 'fluid', 'grid', 'viewport'
            ]
        }
        
        return focused_keywords.get(primary_issue, ['general'])
    
    def _calculate_confidence(self, text: str, issue_type: IssueType) -> float:
        """Calculate confidence level for the identified issue type"""
        keywords = self.issue_patterns.get(issue_type, [])
        matches = sum(1 for keyword in keywords if keyword in text)
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 0.0
        
        return min(matches / total_keywords, 1.0)
    
    def _identify_related_issues(self, text: str) -> List[IssueType]:
        """Identify related issue types that might be connected"""
        related_issues = []
        
        for issue_type, keywords in self.issue_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                related_issues.append(issue_type)
        
        return related_issues
    
    def filter_analysis_results(self, analysis_results: Dict, issue_focus: Dict) -> Dict:
        """Filter analysis results to focus only on relevant areas"""
        primary_issue = issue_focus['primary_issue']
        analysis_areas = issue_focus['analysis_areas']
        
        filtered_results = {
            'primary_issue': primary_issue.value,
            'issue_confidence': issue_focus['issue_confidence'],
            'focused_analysis': {},
            'relevant_recommendations': []
        }
        
        # Filter code analysis based on relevant areas
        if 'code_analysis' in analysis_results:
            code_analysis = analysis_results['code_analysis']
            filtered_code_analysis = {}
            
            # Only include analysis areas relevant to the issue
            if primary_issue in [IssueType.PERFORMANCE, IssueType.LOADING]:
                if 'performance_issues' in code_analysis:
                    filtered_code_analysis['performance_issues'] = code_analysis['performance_issues']
            
            if primary_issue == IssueType.MOBILE:
                if 'mobile_issues' in code_analysis:
                    filtered_code_analysis['mobile_issues'] = code_analysis['mobile_issues']
                if 'theme_analysis' in code_analysis:
                    # Only include mobile-related theme issues
                    theme_analysis = code_analysis['theme_analysis']
                    if 'mobile_responsiveness' in theme_analysis:
                        filtered_code_analysis['theme_analysis'] = {
                            'mobile_responsiveness': theme_analysis['mobile_responsiveness']
                        }
            
            if primary_issue == IssueType.SECURITY:
                if 'security_issues' in code_analysis:
                    filtered_code_analysis['security_issues'] = code_analysis['security_issues']
            
            if primary_issue == IssueType.FUNCTIONALITY:
                if 'code_smells' in code_analysis:
                    filtered_code_analysis['code_smells'] = code_analysis['code_smells']
            
            filtered_results['focused_analysis'] = filtered_code_analysis
        
        # Filter recommendations based on the issue
        if 'recommendations' in analysis_results:
            recommendations = analysis_results['recommendations']
            focused_keywords = issue_focus['focused_keywords']
            
            relevant_recommendations = []
            for rec in recommendations:
                rec_lower = rec.lower()
                if any(keyword in rec_lower for keyword in focused_keywords):
                    relevant_recommendations.append(rec)
            
            filtered_results['relevant_recommendations'] = relevant_recommendations[:5]  # Top 5 most relevant
        
        return filtered_results
    
    def generate_issue_specific_summary(self, issue_focus: Dict, analysis_results: Dict) -> str:
        """Generate a summary focused on the specific issue"""
        primary_issue = issue_focus['primary_issue']
        confidence = issue_focus['issue_confidence']
        
        summary_parts = []
        
        # Issue identification
        summary_parts.append(f"**🎯 Primary Issue Identified:** {primary_issue.value.replace('_', ' ').title()}")
        summary_parts.append(f"**📊 Confidence Level:** {confidence:.1%}")
        
        # Focused analysis results
        if 'focused_analysis' in analysis_results:
            focused = analysis_results['focused_analysis']
            
            if primary_issue == IssueType.MOBILE:
                if 'mobile_issues' in focused:
                    summary_parts.append(f"**📱 Mobile Issues Found:** {len(focused['mobile_issues'])}")
                if 'theme_analysis' in focused and 'mobile_responsiveness' in focused['theme_analysis']:
                    summary_parts.append(f"**📱 Responsive Design Issues:** {len(focused['theme_analysis']['mobile_responsiveness'])}")
            
            elif primary_issue == IssueType.PERFORMANCE:
                if 'performance_issues' in focused:
                    summary_parts.append(f"**⚡ Performance Issues Found:** {len(focused['performance_issues'])}")
            
            elif primary_issue == IssueType.SECURITY:
                if 'security_issues' in focused:
                    summary_parts.append(f"**🔒 Security Issues Found:** {len(focused['security_issues'])}")
        
        # Relevant recommendations
        if 'relevant_recommendations' in analysis_results:
            recs = analysis_results['relevant_recommendations']
            if recs:
                summary_parts.append(f"**🎯 Relevant Recommendations:** {len(recs)}")
        
        return "\n".join(summary_parts)

# Global instance
issue_analyzer = IssueFocusedAnalyzer() 