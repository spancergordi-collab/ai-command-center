"""
Vercel Serverless API for AI Command Center
"""

import json
import os
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Database setup
DB_PATH = "/tmp/ai_command_center.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Agents table
    c.execute('''CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT DEFAULT 'offline',
        tasks_running INTEGER DEFAULT 0,
        tasks_completed INTEGER DEFAULT 0,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        config JSON DEFAULT '{}'
    )''')
    
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        progress INTEGER DEFAULT 0,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        result JSON DEFAULT '{}',
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )''')
    
    # Check if empty
    count = c.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
    if count == 0:
        # Seed agents
        agents = [
            ("Hermes Main", "core", "online", 5, 120),
            ("Code Generator", "coding", "online", 3, 85),
            ("Research Bot", "research", "online", 2, 45),
            ("Email Agent", "communication", "online", 1, 30),
            ("Data Analyzer", "analytics", "offline", 0, 15),
            ("Web Scraper", "research", "online", 4, 60),
            ("API Handler", "integration", "online", 2, 40),
            ("Scheduler", "automation", "online", 1, 25)
        ]
        for agent in agents:
            c.execute(
                "INSERT INTO agents (name, type, status, tasks_running, tasks_completed) VALUES (?, ?, ?, ?, ?)",
                agent
            )
        
        # Seed tasks
        tasks = [
            (1, "Generate API docs", "completed", 100),
            (2, "Research AI papers", "running", 65),
            (3, "Analyze market data", "running", 30),
            (4, "Send notification", "completed", 100),
            (5, "Scrape competitor info", "running", 80),
            (6, "Process data batch", "pending", 0),
            (7, "Update documentation", "running", 45),
            (8, "Deploy to production", "pending", 0)
        ]
        for task in tasks:
            c.execute(
                "INSERT INTO tasks (agent_id, name, status, progress) VALUES (?, ?, ?, ?)",
                task
            )
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_system_stats():
    """Get system statistics (mock for Vercel)"""
    return {
        "cpu_percent": 0.0,
        "memory_percent": 24.3,
        "memory_used_gb": 1.87,
        "memory_total_gb": 7.68,
        "disk_percent": 1.2,
        "disk_used_gb": 11.09,
        "disk_total_gb": 1006.85
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        
        # API routes
        if path == "/api" or path == "/api/":
            self.send_json({"message": "AI Command Center API", "version": "1.0.0"})
            return
        
        if path == "/api/status":
            data = {
                "hermes": {"running": True, "pid": "online"},
                "system": get_system_stats(),
                "timestamp": datetime.now().isoformat()
            }
            self.send_json(data)
            return
        
        if path == "/api/agents":
            conn = get_db()
            agents = conn.execute("SELECT * FROM agents").fetchall()
            conn.close()
            self.send_json([dict(agent) for agent in agents])
            return
        
        if path == "/api/tasks":
            conn = get_db()
            tasks = conn.execute("""
                SELECT t.*, a.name as agent_name 
                FROM tasks t 
                LEFT JOIN agents a ON t.agent_id = a.id
                ORDER BY t.started_at DESC
            """).fetchall()
            conn.close()
            self.send_json([dict(task) for task in tasks])
            return
        
        if path == "/api/dashboard/stats":
            conn = get_db()
            total_agents = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            active_agents = conn.execute("SELECT COUNT(*) FROM agents WHERE status = 'online'").fetchone()[0]
            total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            running_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'running'").fetchone()[0]
            completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'").fetchone()[0]
            conn.close()
            
            data = {
                "agents": {"total": total_agents, "active": active_agents, "offline": total_agents - active_agents},
                "tasks": {"total": total_tasks, "running": running_tasks, "completed": completed_tasks, "pending": total_tasks - running_tasks - completed_tasks},
                "workflows": {"total": 0},
                "success_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
            }
            self.send_json(data)
            return
        
        # NEW: Export data as CSV
        if path == "/api/export/csv":
            conn = get_db()
            agents = conn.execute("SELECT * FROM agents").fetchall()
            tasks = conn.execute("SELECT * FROM tasks").fetchall()
            conn.close()
            
            # Build CSV
            csv_lines = []
            csv_lines.append("TYPE,ID,NAME,STATUS,TASKS_RUNNING,TASKS_COMPLETED,LAST_ACTIVE")
            for agent in agents:
                csv_lines.append(f"AGENT,{agent['id']},{agent['name']},{agent['status']},{agent['tasks_running']},{agent['tasks_completed']},{agent['last_active']}")
            
            csv_lines.append("")
            csv_lines.append("TYPE,ID,AGENT_ID,NAME,STATUS,PROGRESS,STARTED_AT")
            for task in tasks:
                csv_lines.append(f"TASK,{task['id']},{task['agent_id']},{task['name']},{task['status']},{task['progress']},{task['started_at']}")
            
            csv_content = "\n".join(csv_lines)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header('Content-Disposition', 'attachment; filename="ai_command_center_export.csv"')
            self.end_headers()
            self.wfile.write(csv_content.encode())
            return
        
        # NEW: Stats history for charts (mock data)
        if path == "/api/stats/history":
            import random
            from datetime import datetime, timedelta
            
            history = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
                history.append({
                    "date": date,
                    "agents_online": random.randint(5, 8),
                    "tasks_completed": random.randint(10, 30),
                    "success_rate": round(random.uniform(70, 95), 1)
                })
            
            self.send_json({"history": history})
            return
        
        # Default response
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        path = self.path
        
        if path.startswith("/api/agents/"):
            agent_id = int(path.split("/")[-2])
            action = path.split("/")[-1]
            
            conn = get_db()
            if action == "start":
                conn.execute("UPDATE agents SET status = 'online' WHERE id = ?", (agent_id,))
                conn.commit()
                self.send_json({"message": "Agent started"})
            elif action == "stop":
                conn.execute("UPDATE agents SET status = 'offline' WHERE id = ?", (agent_id,))
                conn.commit()
                self.send_json({"message": "Agent stopped"})
            conn.close()
            return
        
        self.send_response(404)
        self.end_headers()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging