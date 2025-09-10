"""
Setup script for the Financial Advisor Life Insurance Assistant.
Based on patterns from AIE7 course materials.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 12):
        print("❌ Python 3.12 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_uv_installation():
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        print("✅ uv package manager detected")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv package manager not found")
        print("Please install uv: https://docs.astral.sh/uv/getting-started/installation/")
        return False


def install_dependencies():
    """Install project dependencies using uv."""
    try:
        print("📦 Installing dependencies...")
        subprocess.run(["uv", "sync"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def create_env_file():
    """Create .env file from template."""
    env_template = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# External Search (Optional)
TAVILY_API_KEY=your_tavily_api_key_here

# Reranking (Optional)
COHERE_API_KEY=your_cohere_api_key_here

# LangSmith Monitoring (Optional)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=financial-advisor-assistant

# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Application Settings
CONFIDENCE_THRESHOLD=0.7
MAX_TOKENS=4000
TEMPERATURE=0.1
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_template)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys")
    else:
        print("✅ .env file already exists")


def check_qdrant():
    """Check if Qdrant is running."""
    try:
        import qdrant_client
        client = qdrant_client.QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print("✅ Qdrant is running and accessible")
        return True
    except Exception as e:
        print("❌ Qdrant is not running or not accessible")
        print("Please start Qdrant:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        print("  or install and run locally: https://qdrant.tech/documentation/guides/installation/")
        return False


def setup_project():
    """Main setup function."""
    print("🏦 Financial Advisor Life Insurance Assistant - Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check uv installation
    if not check_uv_installation():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create .env file
    create_env_file()
    
    # Check Qdrant
    qdrant_ok = check_qdrant()
    
    print("\n📋 Setup Summary:")
    print("✅ Python environment ready")
    print("✅ Dependencies installed")
    print("✅ .env file created")
    
    if qdrant_ok:
        print("✅ Qdrant is running")
    else:
        print("⚠️  Qdrant needs to be started")
    
    print("\n🚀 Next Steps:")
    print("1. Edit .env file with your API keys")
    print("2. Start Qdrant if not running")
    print("3. Run: python load_data.py")
    print("4. Run: chainlit run app.py")
    
    return True


if __name__ == "__main__":
    success = setup_project()
    if success:
        print("\n🎉 Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1) 