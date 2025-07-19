# The Complete Model Context Protocol (MCP) Guide - 2025

## Table of Contents
1. [What is MCP?](#what-is-mcp)
2. [Architecture & Core Concepts](#architecture--core-concepts)
3. [Protocol Specifications](#protocol-specifications)
4. [Development SDKs](#development-sdks)
5. [Building Your First MCP Server](#building-your-first-mcp-server)
6. [Advanced Server Development](#advanced-server-development)
7. [Debugging & Troubleshooting](#debugging--troubleshooting)
8. [Real-World Examples](#real-world-examples)
9. [Best Practices](#best-practices)
10. [2025 Updates & Ecosystem](#2025-updates--ecosystem)

---

## What is MCP?

The Model Context Protocol (MCP) is an open standard introduced by Anthropic in late 2024 that enables secure, two-way connections between AI applications and external data sources, tools, and services. Think of it as **"USB for AI integrations"** - a universal connector that standardizes how AI models interact with the outside world.

### Why MCP Matters in 2025

- **Solves the M×N Problem**: Instead of building custom integrations for each AI application and tool combination, MCP provides a unified protocol
- **Standardization**: Universal API for connecting AI systems with data sources
- **Security & Privacy**: Explicit user approval for every access, local execution by default
- **Dynamic Discovery**: Automatic detection of available servers and capabilities
- **Ecosystem Growth**: Over 1,000 open-source connectors by February 2025

---

## Architecture & Core Concepts

### The Four Components

```
┌─────────────────────────────────────────────────────────────┐
│                        HOST                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   CLIENT    │  │   CLIENT    │  │   CLIENT    │        │
│  │      │      │  │      │      │  │      │      │        │
│  └──────┼──────┘  └──────┼──────┘  └──────┼──────┘        │
└─────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │  SERVER  │      │  SERVER  │      │  SERVER  │
    │  (Tools) │      │(Resources)│      │(Prompts) │
    └──────────┘      └──────────┘      └──────────┘
```

1. **Hosts**: AI applications (Claude Desktop, Cursor, VS Code)
2. **Clients**: Connection managers (one per server)
3. **Servers**: External programs exposing capabilities
4. **Protocol**: JSON-RPC 2.0 over stdio/HTTP/WebSocket

### The Three Primitives

#### 1. Tools (Model-controlled)
Functions that LLMs can call to perform actions:
```python
@mcp.tool()
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"
```

#### 2. Resources (Application-controlled)
Data sources that LLMs can access (like GET endpoints):
```python
@mcp.resource("weather://{location}")
def weather_data(location: str) -> str:
    """Weather data resource."""
    return f"Current conditions for {location}"
```

#### 3. Prompts (User-controlled)
Pre-defined templates for optimal interactions:
```python
@mcp.prompt()
def weather_report_prompt(location: str) -> str:
    """Generate weather report prompt."""
    return f"Create a detailed weather report for {location}"
```

---

## Protocol Specifications

### Communication Flow

1. **Initialization**: Handshake with capability exchange
2. **Discovery**: Client requests available tools/resources/prompts
3. **Invocation**: LLM calls tools or accesses resources
4. **Execution**: Server processes requests and returns results
5. **Response**: Results sent back to LLM

### Protocol Version: 2024-11-05

Current stable version used across the ecosystem. **Critical**: All servers must use this exact version.

### Transport Mechanisms

#### STDIO Transport (Recommended for Local)
```json
{
  "command": "/path/to/python",
  "args": ["/path/to/server.py"],
  "env": {"PYTHONPATH": "/path/to/modules"}
}
```

#### HTTP/SSE Transport (For Remote)
```json
{
  "type": "sse",
  "url": "https://api.example.com/mcp",
  "headers": {"Authorization": "Bearer token"}
}
```

### JSON-RPC Message Format

All messages use JSON-RPC 2.0:

**Initialize Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {"listChanged": true},
      "sampling": {}
    },
    "clientInfo": {
      "name": "Claude Desktop",
      "version": "1.0.0"
    }
  }
}
```

**Server Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "logging": {},
      "tools": {"listChanged": true},
      "resources": {"subscribe": true, "listChanged": true},
      "prompts": {"listChanged": true}
    },
    "serverInfo": {
      "name": "Weather Server",
      "version": "1.0.0"
    }
  }
}
```

---

## Development SDKs

### Python SDK (Official)

**Installation:**
```bash
pip install mcp
```

**Basic Server:**
```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create server
app = Server("my-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="echo",
            description="Echo text back",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "echo":
        return [TextContent(type="text", text=arguments["text"])]

    raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream,
                     InitializationOptions(
                         server_name="my-server",
                         server_version="1.0.0",
                         capabilities=app.get_capabilities()
                     ))

if __name__ == "__main__":
    asyncio.run(main())
```

### FastMCP (Pythonic Framework)

**Installation:**
```bash
pip install fastmcp
```

**Example:**
```python
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Demo Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.resource("config://version")
def get_version() -> str:
    """Get server version."""
    return "1.0.0"

@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: int) -> dict:
    """Get user profile by ID."""
    return {"name": f"User {user_id}", "active": True}

@mcp.prompt()
def summarize_data(data: str) -> str:
    """Create a data summary prompt."""
    return f"Please summarize this data: {data}"

if __name__ == "__main__":
    mcp.run()
```

### JavaScript/TypeScript SDK (Official)

**Installation:**
```bash
npm install @modelcontextprotocol/sdk
```

**Example:**
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server({
  name: "example-server",
  version: "1.0.0",
}, {
  capabilities: {
    tools: {},
    resources: {},
    prompts: {}
  }
});

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [{
      name: "echo",
      description: "Echo text back",
      inputSchema: {
        type: "object",
        properties: {
          text: { type: "string" }
        },
        required: ["text"]
      }
    }]
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "echo") {
    return {
      content: [{
        type: "text",
        text: request.params.arguments.text
      }]
    };
  }

  throw new McpError(ErrorCode.ToolNotFound, "Tool not found");
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## Building Your First MCP Server

### Step-by-Step Tutorial

#### 1. Project Setup

```bash
# Create project directory
mkdir my-mcp-server
cd my-mcp-server

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install mcp fastmcp
```

#### 2. Create Basic Server

**server.py:**
```python
from fastmcp import FastMCP
import json
import os
from datetime import datetime

# Initialize MCP server
mcp = FastMCP("File Manager Server")

@mcp.tool()
def read_file(filepath: str) -> str:
    """Read contents of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@mcp.tool()
def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {e}"

@mcp.tool()
def list_directory(dirpath: str = ".") -> str:
    """List contents of a directory."""
    try:
        items = []
        for item in os.listdir(dirpath):
            full_path = os.path.join(dirpath, item)
            item_type = "dir" if os.path.isdir(full_path) else "file"
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
            items.append(f"{item_type}: {item} ({size} bytes)")
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

@mcp.resource("file://{filepath}")
def file_resource(filepath: str) -> str:
    """Access file as a resource."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

@mcp.prompt()
def file_analysis_prompt(filepath: str) -> str:
    """Generate a prompt for file analysis."""
    return f"""Please analyze the file at {filepath}:
1. Summarize its contents
2. Identify the file type and purpose
3. Note any patterns or important elements
4. Suggest improvements if applicable"""

if __name__ == "__main__":
    mcp.run()
```

#### 3. Configuration

**config.json:**
```json
{
  "mcpServers": {
    "file-manager": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/server.py"],
      "env": {}
    }
  }
}
```

#### 4. Testing

```bash
# Test server directly
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python server.py

# Expected output:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "read_file",
        "description": "Read contents of a file.",
        "inputSchema": {...}
      }
    ]
  }
}
```

---

## Advanced Server Development

### Complex Tool Implementation

```python
import sqlite3
from typing import List, Dict, Any
from fastmcp import FastMCP

mcp = FastMCP("Database Manager")

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

db = DatabaseManager("users.db")

@mcp.tool()
def create_user(name: str, email: str) -> str:
    """Create a new user."""
    try:
        db.execute_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        return f"User {name} created successfully"
    except Exception as e:
        return f"Error creating user: {e}"

@mcp.tool()
def search_users(query: str) -> str:
    """Search users by name or email."""
    try:
        results = db.execute_query(
            "SELECT * FROM users WHERE name LIKE ? OR email LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
        if not results:
            return "No users found"

        output = []
        for user in results:
            output.append(f"ID: {user['id']}, Name: {user['name']}, Email: {user['email']}")
        return "\n".join(output)
    except Exception as e:
        return f"Error searching users: {e}"

@mcp.resource("users://all")
def all_users() -> str:
    """Get all users as a resource."""
    try:
        users = db.execute_query("SELECT * FROM users ORDER BY name")
        return json.dumps(users, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.resource("users://{user_id}")
def user_by_id(user_id: int) -> str:
    """Get specific user by ID."""
    try:
        users = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if not users:
            return "User not found"
        return json.dumps(users[0], indent=2)
    except Exception as e:
        return f"Error: {e}"
```

### Error Handling and Logging

```python
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".mcp" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@mcp.tool()
def safe_operation(data: str) -> str:
    """Example of safe tool with comprehensive error handling."""
    try:
        logger.info(f"Processing operation with data length: {len(data)}")

        # Validation
        if not data or len(data) > 10000:
            raise ValueError("Data must be between 1 and 10000 characters")

        # Processing
        result = data.upper()

        logger.info("Operation completed successfully")
        return result

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return f"Validation error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"Internal error occurred"
```

### Async Operations

```python
import asyncio
import aiohttp
from fastmcp import FastMCP

mcp = FastMCP("Async Web Server")

@mcp.tool()
async def fetch_url(url: str) -> str:
    """Fetch content from a URL asynchronously."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    return f"Status: {response.status}\nContent: {content[:1000]}..."
                else:
                    return f"Error: HTTP {response.status}"
    except Exception as e:
        return f"Error fetching URL: {e}"

@mcp.tool()
async def fetch_multiple_urls(urls: List[str]) -> str:
    """Fetch multiple URLs concurrently."""
    try:
        async def fetch_single(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return f"{url}: {response.status}"

        results = await asyncio.gather(*[fetch_single(url) for url in urls])
        return "\n".join(results)
    except Exception as e:
        return f"Error in batch fetch: {e}"
```

---

## Debugging & Troubleshooting

### Debug Mode

```bash
# Enable debug logging
claude --mcp-debug -p 'test message'

# Check server logs
tail -f ~/.mcp/logs/server_*.log

# Manual server testing
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0.0"},"capabilities":{}},"id":1}' | python server.py
```

### Common Issues & Solutions

#### 1. Connection Closed Errors

**Symptoms:**
```
MCP server "name": Connection failed: McpError: MCP error -32000: Connection closed
```

**Solutions:**
- Check absolute paths in configuration
- Verify Python executable exists
- Test server independently
- Check protocol version (must be "2024-11-05")
- Ensure virtual environment is activated

#### 2. Import Errors

**Debugging:**
```python
# Add to server start
import sys
print(f"Python: {sys.executable}", file=sys.stderr)
print(f"Path: {sys.path}", file=sys.stderr)
```

**Solutions:**
- Use absolute paths for PYTHONPATH
- Install dependencies in correct venv
- Check module availability

#### 3. Protocol Version Mismatch

**Error:**
```json
{
  "code": -32602,
  "message": "Unsupported protocol version",
  "data": {
    "supported": ["2024-11-05"],
    "requested": "1.0.0"
  }
}
```

**Solution:**
Always use protocol version "2024-11-05"

### Shell Debugging Functions

```bash
# List MCP tools
mcp_tools() {
    local server_command=("${@}")
    echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | "${server_command[@]}" | jq
}

# Call MCP tool
mcp_call() {
    local tool="$1"
    local args="$2"
    shift 2
    local server_command=("${@}")
    echo "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"id\":1,\"params\":{\"name\":\"$tool\",\"arguments\":$args}}" | "${server_command[@]}" | jq
}

# Test server initialization
mcp_init() {
    local server_command=("${@}")
    echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0.0"},"capabilities":{}},"id":1}' | "${server_command[@]}" | jq
}
```

---

## Real-World Examples

### 1. GitHub Integration Server

```python
from fastmcp import FastMCP
import requests
import os

mcp = FastMCP("GitHub Server")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

@mcp.tool()
def list_repositories(username: str) -> str:
    """List user's repositories."""
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(f"{GITHUB_API}/users/{username}/repos", headers=headers)

        if response.status_code == 200:
            repos = response.json()
            output = []
            for repo in repos[:10]:  # Limit to 10
                output.append(f"• {repo['name']}: {repo['description'] or 'No description'}")
            return "\n".join(output)
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_issue(repo: str, title: str, body: str) -> str:
    """Create a GitHub issue."""
    try:
        if not GITHUB_TOKEN:
            return "Error: GitHub token required"

        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        data = {"title": title, "body": body}

        response = requests.post(f"{GITHUB_API}/repos/{repo}/issues",
                               json=data, headers=headers)

        if response.status_code == 201:
            issue = response.json()
            return f"Issue created: #{issue['number']} - {issue['html_url']}"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"

@mcp.resource("github://repos/{owner}/{repo}/issues")
def repo_issues(owner: str, repo: str) -> str:
    """Get repository issues."""
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                              headers=headers)

        if response.status_code == 200:
            return json.dumps(response.json(), indent=2)
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
```

### 2. Database Analytics Server

```python
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from fastmcp import FastMCP

mcp = FastMCP("Analytics Server")

@mcp.tool()
def analyze_csv(filepath: str) -> str:
    """Analyze a CSV file and return statistics."""
    try:
        df = pd.read_csv(filepath)

        analysis = []
        analysis.append(f"Dataset shape: {df.shape}")
        analysis.append(f"Columns: {', '.join(df.columns)}")
        analysis.append("\nData types:")
        for col, dtype in df.dtypes.items():
            analysis.append(f"  {col}: {dtype}")

        analysis.append("\nNumeric columns summary:")
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary = df[numeric_cols].describe()
            analysis.append(summary.to_string())

        analysis.append(f"\nMissing values:")
        missing = df.isnull().sum()
        for col, count in missing.items():
            if count > 0:
                analysis.append(f"  {col}: {count}")

        return "\n".join(analysis)
    except Exception as e:
        return f"Error analyzing CSV: {e}"

@mcp.tool()
def create_chart(data: str, chart_type: str = "bar") -> str:
    """Create a chart from data."""
    try:
        # Parse data (expecting JSON format)
        import json
        chart_data = json.loads(data)

        plt.figure(figsize=(10, 6))

        if chart_type == "bar":
            plt.bar(chart_data.keys(), chart_data.values())
        elif chart_type == "line":
            plt.plot(list(chart_data.keys()), list(chart_data.values()))
        else:
            return f"Unsupported chart type: {chart_type}"

        plt.title("Data Visualization")
        plt.xlabel("Categories")
        plt.ylabel("Values")

        # Save to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_b64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"Chart created successfully. Base64 data: data:image/png;base64,{chart_b64}"
    except Exception as e:
        return f"Error creating chart: {e}"
```

### 3. System Monitoring Server

```python
import psutil
import platform
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("System Monitor")

@mcp.tool()
def get_system_info() -> str:
    """Get comprehensive system information."""
    try:
        info = []

        # System info
        info.append(f"System: {platform.system()} {platform.release()}")
        info.append(f"Machine: {platform.machine()}")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Architecture: {platform.architecture()[0]}")

        # CPU info
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)
        info.append(f"\nCPU Cores: {cpu_count}")
        info.append(f"CPU Usage: {cpu_usage}%")

        # Memory info
        memory = psutil.virtual_memory()
        info.append(f"\nMemory Total: {memory.total // (1024**3)} GB")
        info.append(f"Memory Available: {memory.available // (1024**3)} GB")
        info.append(f"Memory Usage: {memory.percent}%")

        # Disk info
        disk = psutil.disk_usage('/')
        info.append(f"\nDisk Total: {disk.total // (1024**3)} GB")
        info.append(f"Disk Free: {disk.free // (1024**3)} GB")
        info.append(f"Disk Usage: {(disk.used / disk.total) * 100:.1f}%")

        # Network info
        network = psutil.net_io_counters()
        info.append(f"\nBytes Sent: {network.bytes_sent // (1024**2)} MB")
        info.append(f"Bytes Received: {network.bytes_recv // (1024**2)} MB")

        return "\n".join(info)
    except Exception as e:
        return f"Error getting system info: {e}"

@mcp.tool()
def get_running_processes(limit: int = 10) -> str:
    """Get list of running processes."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)

        output = []
        output.append(f"{'PID':<8} {'NAME':<25} {'CPU%':<8} {'MEM%':<8}")
        output.append("-" * 50)

        for proc in processes[:limit]:
            output.append(f"{proc['pid']:<8} {proc['name'][:24]:<25} "
                         f"{proc['cpu_percent'] or 0:<8.1f} {proc['memory_percent'] or 0:<8.1f}")

        return "\n".join(output)
    except Exception as e:
        return f"Error getting processes: {e}"

@mcp.resource("system://status")
def system_status() -> str:
    """System status as a resource."""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        return json.dumps(status, indent=2)
    except Exception as e:
        return f"Error: {e}"
```

---

## Best Practices

### 1. Security

```python
import os
import hashlib
from pathlib import Path

# Environment validation
def validate_environment():
    """Validate server environment before starting."""
    required_vars = ["MCP_SERVER_NAME", "MCP_DATA_DIR"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing environment variables: {missing}")

# Input sanitization
def sanitize_path(path: str) -> str:
    """Sanitize file paths to prevent directory traversal."""
    # Resolve to absolute path and check it's within allowed directory
    abs_path = os.path.abspath(path)
    allowed_dir = os.path.abspath(os.getenv("MCP_DATA_DIR", "/tmp"))

    if not abs_path.startswith(allowed_dir):
        raise ValueError("Path outside allowed directory")

    return abs_path

# Rate limiting
from time import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_calls: int = 100, window: int = 60):
        self.max_calls = max_calls
        self.window = window
        self.calls = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time()
        client_calls = self.calls[client_id]

        # Remove old calls
        self.calls[client_id] = [call_time for call_time in client_calls
                                if now - call_time < self.window]

        if len(self.calls[client_id]) >= self.max_calls:
            return False

        self.calls[client_id].append(now)
        return True

rate_limiter = RateLimiter()

@mcp.tool()
def secure_operation(data: str, client_id: str = "default") -> str:
    """Example of secure tool implementation."""
    # Rate limiting
    if not rate_limiter.is_allowed(client_id):
        return "Rate limit exceeded"

    # Input validation
    if len(data) > 10000:
        return "Data too large"

    # Process safely
    return f"Processed: {len(data)} characters"
```

### 2. Performance

```python
import asyncio
import time
from functools import wraps
from typing import Any, Callable

# Caching decorator
def cache_result(ttl_seconds: int = 300):
    """Cache tool results for specified TTL."""
    cache = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache[key] = (result, time.time())
            return result

        return wrapper
    return decorator

# Async batch processing
@cache_result(ttl_seconds=60)
@mcp.tool()
async def batch_process_files(filepaths: List[str]) -> str:
    """Process multiple files concurrently."""
    async def process_single_file(filepath: str) -> str:
        # Simulate processing
        await asyncio.sleep(0.1)
        return f"Processed: {filepath}"

    # Process in batches to avoid overwhelming system
    batch_size = 10
    results = []

    for i in range(0, len(filepaths), batch_size):
        batch = filepaths[i:i + batch_size]
        batch_results = await asyncio.gather(*[process_single_file(fp) for fp in batch])
        results.extend(batch_results)

    return "\n".join(results)
```

### 3. Configuration Management

```python
import os
import json
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for MCP server."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.getenv("MCP_CONFIG_PATH", "config.json")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment."""
        config = {}

        # Load from file
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                config.update(json.load(f))

        # Override with environment variables
        env_prefix = "MCP_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                config[config_key] = value

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def require(self, key: str) -> Any:
        """Get required configuration value."""
        if key not in self.config:
            raise ValueError(f"Required configuration missing: {key}")
        return self.config[key]

# Global config instance
config = Config()

# Use in tools
@mcp.tool()
def configured_operation() -> str:
    """Example using configuration."""
    api_key = config.require("api_key")
    timeout = config.get("timeout", 30)

    return f"Using API key: {api_key[:8]}... with timeout: {timeout}s"
```

### 4. Testing

```python
import pytest
import json
from unittest.mock import patch, MagicMock

# Test MCP tool directly
def test_echo_tool():
    """Test echo tool functionality."""
    result = echo_tool("test message")
    assert result == "test message"

# Test JSON-RPC interface
def test_mcp_protocol():
    """Test MCP protocol compliance."""
    # Test tools/list
    list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }

    response = process_mcp_request(list_request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert "tools" in response["result"]

# Mock external dependencies
@patch('requests.get')
def test_api_tool(mock_get):
    """Test tool that calls external API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    result = api_tool("test_endpoint")
    assert "test" in result

# Integration test
@pytest.mark.asyncio
async def test_server_integration():
    """Test full server integration."""
    # Start server in test mode
    server = create_test_server()

    # Test initialization
    init_response = await server.handle_request({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"}
        },
        "id": 1
    })

    assert init_response["result"]["protocolVersion"] == "2024-11-05"
```

---

## 2025 Updates & Ecosystem

### Current State

- **Adoption**: Block, Apollo, Zed, Replit, Codeium, Sourcegraph, and others
- **Ecosystem**: 1,000+ open-source connectors
- **Platforms**: Claude Desktop, Cursor, VS Code, Windsurf IDE

### Recent Updates

#### Protocol Enhancements
- **Well-known endpoints**: `/.well-known/mcp` for automatic discovery
- **Streaming improvements**: Real-time data flows and scalability
- **Authorization model**: Enhanced security and permission management

#### New Transport Types
- **WebSocket**: For real-time bidirectional communication
- **HTTP with streaming**: Enhanced SSE support
- **Serverless compatibility**: Better support for cloud functions

### Popular 2025 Server Examples

1. **Blender MCP Server**: 3D modeling integration
2. **Figma MCP Server**: Design tool automation
3. **Unity MCP Server**: Game development workflows
4. **GitHub MCP Server**: Repository management
5. **Database Servers**: PostgreSQL, MySQL, SQLite integration
6. **Analytics Servers**: Data visualization and reporting
7. **File System Servers**: Enhanced file operations
8. **Web Scraping Servers**: Content extraction
9. **API Integration Servers**: REST/GraphQL proxies
10. **Development Tools**: Linting, testing, deployment

### Future Roadmap

- **Multi-modal support**: Image, audio, video processing
- **Enhanced streaming**: Real-time collaborative editing
- **Edge computing**: Serverless and edge deployment
- **Mobile support**: Native mobile app integration
- **Enterprise features**: Advanced security and compliance

### Getting Involved

- **Official documentation**: https://modelcontextprotocol.io/
- **GitHub organization**: https://github.com/modelcontextprotocol/
- **Community Discord**: Active developer community
- **Examples repository**: Hundreds of ready-to-use servers

---

## Conclusion

The Model Context Protocol represents a paradigm shift in AI integration, providing a standardized, secure, and scalable way to connect AI models with external systems. As the ecosystem continues to grow rapidly in 2025, mastering MCP development opens up endless possibilities for creating powerful AI-enhanced applications.

Whether you're building simple file managers or complex enterprise systems, MCP provides the foundation for reliable, secure, and maintainable AI integrations. Start with the basic examples in this guide, then explore the rich ecosystem of existing servers and contribute your own innovations to the growing MCP community.

Remember: MCP is not just a protocol—it's a new way of thinking about AI system architecture that puts security, standardization, and developer experience at the forefront.
