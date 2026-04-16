#!/usr/bin/env python
"""Quick verification script for the AI Assistant project"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def check_imports():
    """Check if all modules can be imported"""
    print("Checking imports...")
    
    try:
        from src.config import get_settings
        print("✓ Config module")
    except Exception as e:
        print(f"✗ Config module: {e}")
        return False
    
    try:
        from src.memory import JSONMemory
        print("✓ Memory module")
    except Exception as e:
        print(f"✗ Memory module: {e}")
        return False
    
    try:
        from src.tools import WebSearchTool, FileTools, BrowserAutomation
        print("✓ Tools module")
    except Exception as e:
        print(f"✗ Tools module: {e}")
        return False
    
    try:
        from src.models import ModelRouter
        print("✓ Models module")
    except Exception as e:
        print(f"✗ Models module: {e}")
        return False
    
    try:
        from src.backend import create_app
        print("✓ Backend module")
    except Exception as e:
        print(f"✗ Backend module: {e}")
        return False
    
    return True

def check_config():
    """Check configuration loading"""
    print("\nChecking configuration...")
    
    try:
        from src.config import get_settings
        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  - Default model: {settings.default_model}")
        print(f"  - API host: {settings.api_host}")
        print(f"  - API port: {settings.api_port}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    return True

def check_app():
    """Check if FastAPI app can be created"""
    print("\nChecking FastAPI app...")
    
    try:
        from src.backend import create_app
        app = create_app()
        print(f"✓ FastAPI app created")
        print(f"  - Routes: {len(app.routes)}")
    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("Private AI Assistant - Project Verification")
    print("=" * 50)
    
    all_good = True
    all_good &= check_imports()
    all_good &= check_config()
    all_good &= check_app()
    
    print("\n" + "=" * 50)
    if all_good:
        print("✓ All checks passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure API keys in .env")
        print("3. Run the server: python main.py")
        sys.exit(0)
    else:
        print("✗ Some checks failed. Please review the errors above.")
        sys.exit(1)
