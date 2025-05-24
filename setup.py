#!/usr/bin/env python3
"""
Interactive setup script for Utils Bot v2.0
"""

import secrets
import shutil
import sys
import asyncio
import subprocess
from pathlib import Path


def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run manually: pip install -r requirements.txt")
        return False


async def run_migrations():
    """Run database migrations"""
    print("\n🗃️ Setting up database...")
    
    # Add project root to path for imports
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # Import and run database initialization
        from models.database import Database
        from config.settings import settings
        
        # Initialize database
        db = Database(settings.database_url)
        await db.initialize()
        await db.close()
        
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("You may need to run migrations manually:")
        print("  python migrations/init_db.py")
        return False


def create_directories():
    """Create necessary directories"""
    directories = ["data", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_hex(32)


def setup_env_file():
    """Setup environment file with user input"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        backup_name = f".env.backup.{int(Path('.env').stat().st_mtime)}"
        shutil.copy(env_file, backup_name)
        print(f"⚠️  Backed up existing .env file to {backup_name}")
    
    # Copy template
    shutil.copy(env_example, env_file)
    print("📋 Created .env file from template")
    
    # Read current content
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Interactive Configuration")
    print("=" * 40)
    
    # Get bot token
    print("\n1. Discord Bot Token")
    print("   Get from: https://discord.com/developers/applications")
    bot_token = input("   Enter your bot token (or press Enter to skip): ").strip()
    if bot_token:
        content = content.replace("BOT_TOKEN=your_discord_bot_token_here", f"BOT_TOKEN={bot_token}")
        print("   ✅ Bot token configured")
    
    # Get dev IDs
    print("\n2. Developer Discord User ID(s)")
    print("   Enable Developer Mode in Discord, right-click your profile")
    dev_ids = input("   Enter your Discord User ID (or press Enter to skip): ").strip()
    if dev_ids:
        # Replace the example with the actual ID
        content = content.replace("DEV_IDS=123456789012345678,987654321098765432", f"DEV_IDS={dev_ids}")
        print("   ✅ Developer ID configured")
    
    # Get Gemini API key
    print("\n3. Google Gemini API Key")
    print("   Get from: https://aistudio.google.com/app/apikey")
    gemini_key = input("   Enter your Gemini API key (or press Enter to skip): ").strip()
    if gemini_key:
        content = content.replace("GEMINI_API_KEY=your_gemini_api_key_here", f"GEMINI_API_KEY={gemini_key}")
        print("   ✅ Gemini API key configured")
    
    # Generate secret key
    secret_key = generate_secret_key()
    content = content.replace("SECRET_KEY=your_secret_key_for_encryption_here", f"SECRET_KEY={secret_key}")
    print("\n4. ✅ Secret key automatically generated")
    
    # Write updated content
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return bot_token and dev_ids and gemini_key


def main():
    """Main setup function"""
    print("🤖 Utils Bot v2.0 Interactive Setup")
    print("=" * 40)
    
    # Create directories
    print("\n📂 Creating required directories...")
    create_directories()
    
    # Setup environment
    print("\n📝 Setting up environment configuration...")
    configured = setup_env_file()
    
    # Install dependencies
    deps_installed = install_dependencies()
    
    # Run database migrations if dependencies are installed
    if deps_installed:
        print("\n🗃️ Initializing database...")
        try:
            asyncio.run(run_migrations())
            db_initialized = True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            db_initialized = False
    else:
        db_initialized = False
    
    print("\n" + "=" * 40)
    
    if configured and deps_installed and db_initialized:
        print("🎉 Setup complete! Your bot is ready to run.")
        print("\nNext steps:")
        print("1. Run the bot: python main.py")
        print("2. Invite the bot to your server with appropriate permissions")
    elif configured and deps_installed:
        print("⚠️  Setup mostly complete, but database initialization failed.")
        print("Please run manually: python migrations/init_db.py")
        print("Then run: python main.py")
    elif configured:
        print("⚠️  Configuration complete, but dependencies failed to install.")
        print("Please run manually:")
        print("1. pip install -r requirements.txt")
        print("2. python migrations/init_db.py")
        print("3. python main.py")
    else:
        print("⚠️  Partial setup completed.")
        print("Please edit .env file and fill in the required values:")
        print("- BOT_TOKEN")
        print("- DEV_IDS") 
        print("- GEMINI_API_KEY")
        print("\nThen run:")
        print("1. pip install -r requirements.txt")
        print("2. python migrations/init_db.py") 
        print("3. python main.py")
    
    print("\n📖 For more information, see README.md")


if __name__ == "__main__":
    main()
