#!/usr/bin/env python3
"""
Pre-flight check script to verify backend setup is complete.

This script checks:
- Database tables exist
- Storage directories are created
- Configuration files are present
- Ollama is accessible (optional warning)

Usage:
    python scripts/check_setup.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect
from core.database import sync_engine
from core.config import settings
import requests


def check_database_tables():
    """Check if all required database tables exist."""
    print("🗄️  Checking database tables...")

    try:
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()

        required_tables = ['projects', 'documents', 'chats', 'messages', 'user_settings']
        missing_tables = []
        existing_tables = []

        for table in required_tables:
            if table in tables:
                existing_tables.append(table)
                print(f"  ✅ Table '{table}' exists")
            else:
                missing_tables.append(table)
                print(f"  ❌ Table '{table}' missing")

        if missing_tables:
            print(f"\n  ⚠️  Missing {len(missing_tables)} table(s). Run: alembic upgrade head")
            return False

        print(f"  ✓ All {len(existing_tables)} required tables exist")
        return True

    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        return False


def check_storage_directories():
    """Check if storage directories exist."""
    print("\n📁 Checking storage directories...")

    storage_dirs = [
        ('SQLite database', Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent),
        ('ChromaDB vectors', Path(settings.CHROMA_PERSIST_DIR)),
        ('Document uploads', Path(settings.UPLOAD_DIR)),
    ]

    all_exist = True
    for name, dir_path in storage_dirs:
        if dir_path.exists():
            print(f"  ✅ {name}: {dir_path}")
        else:
            print(f"  ⚠️  {name} missing: {dir_path} (will be auto-created)")
            all_exist = False

    return all_exist


def check_env_file():
    """Check if .env file exists."""
    print("\n⚙️  Checking configuration...")

    env_file = Path(".env")
    if env_file.exists():
        print(f"  ✅ .env file exists")
        return True
    else:
        print(f"  ⚠️  .env file missing (using default settings)")
        return False


def check_ollama():
    """Check if Ollama is accessible (non-critical)."""
    print("\n🤖 Checking Ollama connection...")

    try:
        response = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"  ✅ Ollama is running at {settings.OLLAMA_HOST}")
            if models:
                print(f"  ✓ Found {len(models)} model(s)")
                for model in models[:3]:  # Show first 3 models
                    print(f"    - {model.get('name', 'unknown')}")
            else:
                print(f"  ⚠️  No models found. Pull a model with: ollama pull llama3.2")
            return True
        else:
            print(f"  ⚠️  Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ⚠️  Cannot connect to Ollama at {settings.OLLAMA_HOST}")
        print(f"     Start Ollama with: ollama serve")
        return False
    except Exception as e:
        print(f"  ⚠️  Ollama check failed: {e}")
        return False


def main():
    """Run all setup checks."""
    print("🔍 DAA Chatbot Backend Setup Verification")
    print("=" * 50)
    print()

    checks = {
        'Database Tables': check_database_tables(),
        'Storage Directories': check_storage_directories(),
        'Configuration File': check_env_file(),
        'Ollama Connection': check_ollama(),
    }

    print()
    print("=" * 50)
    print("📊 Setup Summary")
    print()

    critical_failed = False
    for check_name, status in checks.items():
        icon = "✅" if status else "⚠️"
        print(f"  {icon} {check_name}")

        # Only database tables are critical
        if check_name == 'Database Tables' and not status:
            critical_failed = True

    print()

    if critical_failed:
        print("❌ Critical checks failed. Please run: alembic upgrade head")
        sys.exit(1)
    elif not all(checks.values()):
        print("⚠️  Some optional checks failed, but the system should still work.")
        print("   Review the warnings above for details.")
        sys.exit(0)
    else:
        print("✅ All checks passed! Backend is ready.")
        print()
        print("To start the server, run:")
        print("  uvicorn api.main:socket_app --reload")
        sys.exit(0)


if __name__ == "__main__":
    main()
