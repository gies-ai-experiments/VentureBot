#!/usr/bin/env python3
"""
VentureBots Import Test - Quick Diagnostic Tool
Run this before starting services to catch import issues early.
"""
import sys
import os

def test_imports():
    """Test all critical imports for VentureBots"""
    print("🔍 VentureBots Import Diagnostic Tool")
    print("=" * 50)
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    print(f"Project root: {project_root}")
    
    # Test 1: Basic environment
    print("\n1. Testing environment...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"   ✅ ANTHROPIC_API_KEY found (starts with: {api_key[:10]}...)")
    else:
        print("   ❌ ANTHROPIC_API_KEY not found")
        print("   💡 Create .env file with ANTHROPIC_API_KEY=your_key")
        return False
    
    # Test 2: Manager directory structure
    print("\n2. Testing project structure...")
    manager_path = os.path.join(project_root, "manager")
    if os.path.exists(manager_path):
        print(f"   ✅ Manager directory found: {manager_path}")
    else:
        print(f"   ❌ Manager directory not found: {manager_path}")
        return False
    
    tools_path = os.path.join(manager_path, "tools", "tools.py")
    if os.path.exists(tools_path):
        print(f"   ✅ Tools module found: {tools_path}")
    else:
        print(f"   ❌ Tools module not found: {tools_path}")
        return False
    
    # Test 3: Root agent import
    print("\n3. Testing root agent import...")
    try:
        from manager.agent import root_agent
        print("   ✅ Root agent import successful")
        print(f"   Agent name: {root_agent.name}")
        print(f"   Sub-agents count: {len(root_agent.sub_agents)}")
    except Exception as e:
        print(f"   ❌ Root agent import failed: {e}")
        print("\n   💡 Common fixes:")
        print("   - Check import paths in sub-agent files")
        print("   - Ensure all imports use 'from manager.tools.tools import'")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Individual sub-agent imports
    print("\n4. Testing individual sub-agent imports...")
    sub_agents = [
        "onboarding_agent",
        "product_manager", 
        "validator_agent",
        "prompt_engineer",
        "idea_generator"
    ]
    
    for agent_name in sub_agents:
        try:
            module_path = f"manager.sub_agents.{agent_name}.agent"
            agent_module = __import__(module_path, fromlist=[agent_name])
            print(f"   ✅ {agent_name} import successful")
        except Exception as e:
            print(f"   ❌ {agent_name} import failed: {e}")
            print(f"   💡 Check imports in manager/sub_agents/{agent_name}/agent.py")
            return False
    
    # Test 5: FastAPI dependencies
    print("\n5. Testing FastAPI dependencies...")
    try:
        from google.adk.cli.fast_api import get_fast_api_app
        print("   ✅ ADK FastAPI import successful")
    except Exception as e:
        print(f"   ❌ ADK import failed: {e}")
        print("   💡 Ensure 'pip install google-adk' in virtual environment")
        return False
    
    try:
        import uvicorn
        print("   ✅ Uvicorn import successful")
    except Exception as e:
        print(f"   ❌ Uvicorn import failed: {e}")
        return False
    
    # Test 6: Create test FastAPI app
    print("\n6. Testing FastAPI app creation...")
    try:
        app = get_fast_api_app(
            agent_dir=project_root,
            session_db_url="sqlite:///./test_sessions.db",
            allow_origins=["*"],
            web=True,
        )
        print("   ✅ FastAPI app creation successful")
        
        # Clean up test database
        test_db = os.path.join(project_root, "test_sessions.db")
        if os.path.exists(test_db):
            os.remove(test_db)
            
    except Exception as e:
        print(f"   ❌ FastAPI app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 All import tests passed!")
    print("\n✅ Ready to start VentureBots:")
    print("   Backend:  PORT=8000 python main.py")
    print("   Frontend: agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501")
    return True

if __name__ == "__main__":
    success = test_imports()
    if not success:
        print("\n❌ Import tests failed!")
        print("📖 See DEVELOPMENT_GUIDE.md for troubleshooting steps")
        sys.exit(1)
    else:
        print("\n🚀 All systems ready for VentureBots!")
        sys.exit(0)