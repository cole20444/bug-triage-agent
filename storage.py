import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

class BugReportStorage:
    def __init__(self, db_path: str = "bug_reports.db"):
        """Initialize the storage system with SQLite database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create the database and tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create bug_reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bug_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    channel_id TEXT,
                    summary TEXT NOT NULL,
                    pages TEXT,
                    steps TEXT,
                    components TEXT,
                    status TEXT DEFAULT 'new',
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_to TEXT,
                    resolved_at TIMESTAMP,
                    notes TEXT
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_report_id ON bug_reports(report_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON bug_reports(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_id ON bug_reports(user_id)
            ''')
            
            conn.commit()
    
    def generate_report_id(self) -> str:
        """Generate a unique report ID in format BUG-YYYY-NNN"""
        year = datetime.now().year
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM bug_reports 
                WHERE report_id LIKE ? AND created_at >= ?
            ''', (f'BUG-{year}-%', f'{year}-01-01'))
            count = cursor.fetchone()[0]
        
        return f"BUG-{year}-{count + 1:03d}"
    
    def save_bug_report(self, user_id: str, channel_id: str, data: Dict[str, str]) -> str:
        """Save a new bug report and return the report ID"""
        report_id = self.generate_report_id()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bug_reports (
                    report_id, user_id, channel_id, summary, pages, steps, components,
                    status, priority, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                user_id,
                channel_id,
                data.get('summary', ''),
                data.get('pages', ''),
                data.get('steps', ''),
                data.get('components', ''),
                'new',
                self._determine_priority(data),
                datetime.now(),
                datetime.now()
            ))
            conn.commit()
        
        return report_id
    
    def _determine_priority(self, data: Dict[str, str]) -> str:
        """Determine priority based on content analysis"""
        text = ' '.join(data.values()).lower()
        
        # High priority keywords
        high_priority = ['critical', 'urgent', 'broken', 'down', 'error', 'crash', 'security']
        if any(word in text for word in high_priority):
            return 'high'
        
        # Medium priority keywords
        medium_priority = ['slow', 'performance', 'issue', 'problem', 'bug']
        if any(word in text for word in medium_priority):
            return 'medium'
        
        return 'low'
    
    def get_bug_report(self, report_id: str) -> Optional[Dict]:
        """Retrieve a bug report by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM bug_reports WHERE report_id = ?
            ''', (report_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_bug_reports(self, status: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get bug reports with optional status filter"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM bug_reports 
                    WHERE status = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT * FROM bug_reports 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_bug_report(self, report_id: str, updates: Dict) -> bool:
        """Update a bug report"""
        if not updates:
            return False
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['summary', 'pages', 'steps', 'components', 'status', 'priority', 'assigned_to', 'notes']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.now())
        values.append(report_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE bug_reports 
                SET {', '.join(set_clauses)}
                WHERE report_id = ?
            ''', values)
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_bug_report(self, report_id: str) -> bool:
        """Delete a bug report"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bug_reports WHERE report_id = ?', (report_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_stats(self) -> Dict:
        """Get bug report statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total reports
            cursor.execute('SELECT COUNT(*) FROM bug_reports')
            total = cursor.fetchone()[0]
            
            # Reports by status
            cursor.execute('''
                SELECT status, COUNT(*) FROM bug_reports 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Reports by priority
            cursor.execute('''
                SELECT priority, COUNT(*) FROM bug_reports 
                GROUP BY priority
            ''')
            priority_counts = dict(cursor.fetchall())
            
            # Recent reports (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM bug_reports 
                WHERE created_at >= datetime('now', '-7 days')
            ''')
            recent = cursor.fetchone()[0]
            
            return {
                'total': total,
                'by_status': status_counts,
                'by_priority': priority_counts,
                'recent_7_days': recent
            }
    
    def search_bug_reports(self, query: str, limit: int = 10) -> List[Dict]:
        """Search bug reports by text content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM bug_reports 
                WHERE summary LIKE ? OR pages LIKE ? OR steps LIKE ? OR components LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (search_term, search_term, search_term, search_term, limit))
            
            return [dict(row) for row in cursor.fetchall()]

# Global storage instance
storage = BugReportStorage()
