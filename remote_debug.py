#!/usr/bin/env python3
"""
Remote Server Debugging Script for VentureBots
Run this on the remote server to diagnose issues
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path

def print_section(title):
    print(f"\n{'='*50}")
    print(f"{title}")
    print('='*50)

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("🔍 VentureBots Remote Server Diagnostic")
    print_section("1. Environment Information")
    
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    
    print_section("2. File System Check")
    
    # Check if we're in the right directory structure
    paths_to_check = [
        "manager/agent.py",
        "manager/sub_agents/",
        "manager/tools/",
        "manager/config.yaml",
        "requirements.txt",
        ".env"
    ]
    
    for path in paths_to_check:
        exists = Path(path).exists()
        print(f"{'✅' if exists else '❌'} {path}: {'exists' if exists else 'missing'}")
    
    print_section("3. Git Status")
    stdout, stderr, code = run_command("git rev-parse HEAD")
    if code == 0:
        print(f"Current commit: {stdout.strip()}")
        print("Expected commit: bb68cdc3 (latest merge)")
    else:
        print(f"❌ Git check failed: {stderr}")
    
    print_section("4. Environment Variables")
    
    env_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "SERPAPI_API_KEY"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Only show first/last 4 chars for security
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: not set")
    
    print_section("5. Python Module Imports")
    
    # Test critical imports
    imports_to_test = [
        "google.adk.agents",
        "google.adk.models.lite_llm", 
        "anthropic",
        "yaml",
        "dotenv"
    ]
    
    for module in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: imported successfully")
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    print_section("6. Agent Import Test")
    
    try:
        # Change to manager directory for import test
        original_cwd = os.getcwd()
        
        # Try different import strategies
        strategies = [
            ("Direct import", lambda: __import__("agent").root_agent),
            ("Sys path manipulation", lambda: (
                sys.path.insert(0, "manager"),
                __import__("agent").root_agent
            )[1])
        ]
        
        for strategy_name, import_func in strategies:
            try:
                os.chdir("manager") if "manager" in os.listdir() else None
                agent = import_func()
                print(f"✅ {strategy_name}: Success")
                print(f"   Agent name: {agent.name}")
                print(f"   Sub-agents: {len(agent.sub_agents) if agent.sub_agents else 0}")
                if agent.sub_agents:
                    for i, sub in enumerate(agent.sub_agents, 1):
                        print(f"     {i}. {sub.name}")
                break
            except Exception as e:
                print(f"❌ {strategy_name}: {e}")
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Agent import test failed: {e}")
        traceback.print_exc()
    
    print_section("7. ADK Server Test")
    
    # Test if ADK is available
    try:
        stdout, stderr, code = run_command("which adk")
        if code == 0:
            print(f"✅ ADK command found: {stdout.strip()}")
        else:
            print(f"❌ ADK command not found")
            
        # Test ADK import
        from google.adk.cli.fast_api import get_fast_api_app
        print("✅ ADK FastAPI import successful")
        
    except Exception as e:
        print(f"❌ ADK test failed: {e}")
    
    print_section("8. Network & Port Check")
    
    # Check if ports are available
    ports_to_check = [8000, 8080, 80]
    for port in ports_to_check:
        stdout, stderr, code = run_command(f"netstat -ln | grep :{port} || echo 'Not in use'")
        print(f"Port {port}: {stdout.strip()}")
    
    print_section("9. Resource Check")
    
    # Check available resources
    stdout, stderr, code = run_command("free -h")
    if code == 0:
        print(f"Memory usage:\n{stdout}")
    
    stdout, stderr, code = run_command("df -h .")
    if code == 0:
        print(f"Disk usage:\n{stdout}")
    
    print_section("10. Recommendations")
    
    print("""
Next steps based on findings above:

1. If imports are failing → Check working directory and Python path
2. If environment variables missing → Verify .env file or container env vars  
3. If file system issues → Verify deployment copied all files correctly
4. If ADK issues → Check if Google ADK installed correctly
5. If port conflicts → Check what's running on ports 8000/8080
6. If resource issues → Check memory/disk limits

To test agent directly:
cd manager && python3 -c "from agent import root_agent; print('Success!')"

To start server manually:
cd manager && adk api_server --port 8000
    """)

if __name__ == "__main__":
    main()