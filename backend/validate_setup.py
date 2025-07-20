"""Validation script to check FastAPI backend setup."""

import sys
import os
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()

def validate_backend_setup():
    """Validate the FastAPI backend setup."""
    print("🔍 Validating FastAPI Backend Setup...")
    
    # Check required files
    required_files = [
        "requirements.txt",
        "run.py",
        "pytest.ini",
        ".env",
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/services/__init__.py",
        "app/services/supabase_service.py",
        "app/routers/__init__.py",
        "app/routers/health.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_supabase_service.py",
        "tests/test_health_endpoint.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("\n🎉 All required files are present!")
    
    # Check imports
    try:
        print("\n🔍 Checking imports...")
        
        # Test config import
        sys.path.insert(0, os.getcwd())
        from app.config import settings
        print("✅ Configuration loaded successfully")
        
        # Test service import
        from app.services.supabase_service import SupabaseService
        print("✅ SupabaseService imported successfully")
        
        # Test main app import
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = validate_backend_setup()
    if success:
        print("\n✨ FastAPI backend setup is complete and valid!")
        print("\nNext steps:")
        print("1. Install Python dependencies: pip install -r requirements.txt")
        print("2. Update .env file with your actual environment variables")
        print("3. Start the server: python run.py")
        print("4. Test health endpoint: curl http://localhost:8000/api/health")
        sys.exit(0)
    else:
        print("\n💥 Setup validation failed!")
        sys.exit(1)