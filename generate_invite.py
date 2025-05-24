#!/usr/bin/env python3
"""
Bot Invite Link Generator for UtilsBot+

This script generates Discord invite links for the bot with appropriate permissions.
It can be run standalone or imported as a module.

Usage:
    python generate_invite.py [--minimal] [--admin] [--custom]
    
Options:
    --minimal   Generate invite with minimal permissions
    --admin     Generate invite with administrator permissions
    --custom    Interactive mode to select custom permissions
    --help      Show this help message
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.settings import settings
except ImportError:
    print("❌ Error: Could not import settings. Make sure you're in the correct directory and have set up the environment.")
    sys.exit(1)


class InviteLinkGenerator:
    """Generate Discord bot invite links with various permission sets"""
    
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.base_url = "https://discord.com/api/oauth2/authorize"
    
    def generate_link(self, permissions: int = None, scopes: list = None) -> str:
        """Generate an invite link with specified permissions and scopes"""
        if scopes is None:
            scopes = ["bot", "applications.commands"]
        
        if permissions is None:
            permissions = self.get_recommended_permissions()
        
        scopes_str = "%20".join(scopes)
        return f"{self.base_url}?client_id={self.bot_id}&permissions={permissions}&scope={scopes_str}"
    
    def get_minimal_permissions(self) -> int:
        """Get minimal permissions required for basic functionality"""
        permissions = 0
        permissions |= 1 << 10   # View Channels
        permissions |= 1 << 11   # Send Messages
        permissions |= 1 << 14   # Embed Links
        permissions |= 1 << 15   # Attach Files
        permissions |= 1 << 16   # Read Message History
        permissions |= 1 << 18   # Use External Emojis
        permissions |= 1 << 24   # Use Slash Commands
        return permissions
    
    def get_recommended_permissions(self) -> int:
        """Get recommended permissions for full functionality"""
        permissions = self.get_minimal_permissions()
        permissions |= 1 << 13   # Manage Messages (for cleanup)
        permissions |= 1 << 17   # Add Reactions
        permissions |= 1 << 19   # Use External Stickers
        permissions |= 1 << 22   # Manage Threads
        permissions |= 1 << 34   # Use External Sounds
        permissions |= 1 << 35   # Send Voice Messages
        return permissions
    
    def get_admin_permissions(self) -> int:
        """Get administrator permissions (full access)"""
        return 1 << 3  # Administrator permission
    
    def get_network_permissions(self) -> int:
        """Get permissions needed for network/screenshot features"""
        permissions = self.get_recommended_permissions()
        # Network features don't need additional Discord permissions
        return permissions
    
    def get_moderation_permissions(self) -> int:
        """Get permissions for moderation features"""
        permissions = self.get_recommended_permissions()
        permissions |= 1 << 1    # Kick Members
        permissions |= 1 << 2    # Ban Members
        permissions |= 1 << 13   # Manage Messages
        permissions |= 1 << 28   # Manage Nicknames
        permissions |= 1 << 30   # Moderate Members
        return permissions
    
    def interactive_permissions(self) -> int:
        """Interactive permission selection"""
        print("\n🔧 Custom Permission Selection")
        print("=" * 40)
        
        permission_options = {
            "minimal": ("Minimal (View, Send Messages, Slash Commands)", self.get_minimal_permissions()),
            "recommended": ("Recommended (Full Bot Functionality)", self.get_recommended_permissions()),
            "network": ("Network Tools (Screenshots, IP lookup)", self.get_network_permissions()),
            "moderation": ("Moderation (Kick, Ban, Manage Messages)", self.get_moderation_permissions()),
            "admin": ("Administrator (Full Server Access)", self.get_admin_permissions())
        }
        
        print("Available permission sets:")
        for key, (description, _) in permission_options.items():
            print(f"  {key}: {description}")
        
        while True:
            choice = input("\nSelect permission set: ").strip().lower()
            if choice in permission_options:
                return permission_options[choice][1]
            print(f"Invalid choice. Please select from: {', '.join(permission_options.keys())}")
    
    def describe_permissions(self, permissions: int) -> list:
        """Describe what permissions are included"""
        permission_names = {
            1 << 0: "Create Instant Invite",
            1 << 1: "Kick Members",
            1 << 2: "Ban Members",
            1 << 3: "Administrator",
            1 << 4: "Manage Channels",
            1 << 5: "Manage Guild",
            1 << 6: "Add Reactions",
            1 << 10: "View Channels",
            1 << 11: "Send Messages",
            1 << 12: "Send TTS Messages",
            1 << 13: "Manage Messages",
            1 << 14: "Embed Links",
            1 << 15: "Attach Files",
            1 << 16: "Read Message History",
            1 << 17: "Mention Everyone",
            1 << 18: "Use External Emojis",
            1 << 20: "Connect",
            1 << 21: "Speak",
            1 << 22: "Mute Members",
            1 << 23: "Deafen Members",
            1 << 24: "Move Members",
            1 << 25: "Use Voice Activity",
            1 << 26: "Change Nickname",
            1 << 27: "Manage Nicknames",
            1 << 28: "Manage Roles",
            1 << 29: "Manage Webhooks",
            1 << 30: "Manage Emojis and Stickers",
            1 << 31: "Use Slash Commands",
            1 << 32: "Request to Speak",
            1 << 33: "Manage Events",
            1 << 34: "Manage Threads",
            1 << 35: "Create Public Threads",
            1 << 36: "Create Private Threads",
            1 << 37: "Use External Stickers",
            1 << 38: "Send Messages in Threads",
            1 << 39: "Use Embedded Activities",
            1 << 40: "Moderate Members"
        }
        
        granted_permissions = []
        for bit, name in permission_names.items():
            if permissions & bit:
                granted_permissions.append(name)
        
        return granted_permissions


def print_invite_info(generator: InviteLinkGenerator, permissions: int, link: str):
    """Print formatted invite link information"""

    
    print(f"\n📋 Bot ID: {generator.bot_id}")
    print(f"🔢 Permissions Value: {permissions}")
    
    print(f"\n🌐 Invite Link:")
    print(f"{link}")
    
    granted_perms = generator.describe_permissions(permissions)
    if len(granted_perms) <= 10:
        for perm in granted_perms:
            print(f"  ✅ {perm}")
    else:
        for perm in granted_perms[:8]:
            print(f"  ✅ {perm}")
        print(f"  ... and {len(granted_perms) - 8} more permissions")


def extract_bot_id_from_token(token: str) -> str:
    """Extract bot ID from Discord bot token"""
    try:
        import base64
        
        # Discord bot tokens have the format: base64(bot_id).random_chars.signature
        # The bot ID is encoded in the first part before the first dot
        if not token:
            return None
            
        # Split token by dots and get the first part (bot ID section)
        token_parts = token.split('.')
        if len(token_parts) < 2:
            return None
            
        # The first part contains the bot ID encoded in base64
        bot_id_encoded = token_parts[0]
        
        # Add padding if needed for base64 decoding
        missing_padding = len(bot_id_encoded) % 4
        if missing_padding:
            bot_id_encoded += '=' * (4 - missing_padding)
        
        # Decode base64 to get bot ID
        try:
            decoded = base64.b64decode(bot_id_encoded, validate=True)
            bot_id = decoded.decode('utf-8')
            
            # Validate that it's a numeric Discord ID
            if bot_id.isdigit() and len(bot_id) >= 17:  # Discord IDs are typically 18-19 digits
                return bot_id
            else:
                return None
                
        except Exception:
            return None
            
    except Exception:
        return None

def get_bot_id_automatically() -> str:
    """Try multiple methods to get bot ID automatically"""
    methods_tried = []
    
    # Method 1: Check if bot_id or application_id is set in settings
    try:
        if hasattr(settings, 'bot_id') and settings.bot_id:
            if str(settings.bot_id).isdigit():
                return str(settings.bot_id)
        methods_tried.append("settings.bot_id")
    except:
        pass
    
    try:
        if hasattr(settings, 'application_id') and settings.application_id:
            if str(settings.application_id).isdigit():
                return str(settings.application_id)
        methods_tried.append("settings.application_id")
    except:
        pass
    
    # Method 2: Extract from bot token
    try:
        if hasattr(settings, 'bot_token') and settings.bot_token:
            bot_id = extract_bot_id_from_token(settings.bot_token)
            if bot_id:
                return bot_id
        methods_tried.append("bot_token_extraction")
    except:
        pass
    
    # Method 3: Check environment variables directly
    import os
    try:
        for env_var in ['BOT_ID', 'APPLICATION_ID', 'CLIENT_ID', 'DISCORD_BOT_ID']:
            bot_id = os.getenv(env_var)
            if bot_id and bot_id.isdigit():
                return bot_id
        methods_tried.append("environment_variables")
    except:
        pass
    
    # Method 4: Try to extract from BOT_TOKEN environment variable
    try:
        bot_token = os.getenv('BOT_TOKEN')
        if bot_token:
            bot_id = extract_bot_id_from_token(bot_token)
            if bot_id:
                return bot_id
        methods_tried.append("env_bot_token_extraction")
    except:
        pass
    
    # If all methods failed, provide helpful error message
    print(f"❌ Could not automatically determine bot ID.")
    print(f"Methods tried: {', '.join(methods_tried)}")
    print("\n💡 Solutions:")
    print("1. Add BOT_ID to your .env file")
    print("2. Add APPLICATION_ID to your .env file") 
    print("3. Use --bot-id parameter")
    print("4. Ensure your BOT_TOKEN is valid")
    print("\nTo find your bot ID:")
    print("• Go to https://discord.com/developers/applications")
    print("• Select your application")
    print("• Copy the Application ID")
    
    return None

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(
        description="Generate Discord invite links for UtilsBot+",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_invite.py                    # Auto-detect bot ID, recommended permissions
  python generate_invite.py --minimal         # Auto-detect bot ID, minimal permissions
  python generate_invite.py --admin           # Auto-detect bot ID, administrator permissions
  python generate_invite.py --custom          # Auto-detect bot ID, interactive selection
  python generate_invite.py --bot-id 123456   # Manual bot ID override
  
The script will automatically try to detect your bot ID from:
1. BOT_ID in settings/environment
2. APPLICATION_ID in settings/environment  
3. Extraction from BOT_TOKEN
4. Environment variables (BOT_ID, APPLICATION_ID, CLIENT_ID, DISCORD_BOT_ID)

For more information, visit: https://github.com/ad1107/utils-bot-plus
        """
    )
    
    parser.add_argument(
        "--minimal", 
        action="store_true",
        help="Generate invite with minimal permissions"
    )
    
    parser.add_argument(
        "--admin", 
        action="store_true",
        help="Generate invite with administrator permissions"
    )
    
    parser.add_argument(
        "--custom", 
        action="store_true",
        help="Interactive mode to select custom permissions"
    )
    
    parser.add_argument(
        "--bot-id",
        type=str,
        help="Override bot ID (auto-detects from settings/token by default)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug information about bot ID detection"
    )
    
    args = parser.parse_args()
    
    # Get bot ID with automatic detection
    if args.bot_id:
        bot_id = args.bot_id
        if args.debug:
            print(f"🔧 Using manually specified bot ID: {bot_id}")
    else:
        if args.debug:
            print("🔍 Attempting automatic bot ID detection...")
        
        bot_id = get_bot_id_automatically()
        if not bot_id:
            sys.exit(1)
        
        if args.debug:
            print(f"✅ Automatically detected bot ID: {bot_id}")
    
    # Validate bot ID
    if not bot_id or not str(bot_id).isdigit():
        print("❌ Error: Invalid bot ID. Must be a numeric Discord application ID.")
        if args.debug:
            print(f"Received bot ID: '{bot_id}' (type: {type(bot_id)})")
        sys.exit(1)
    
    # Create generator
    generator = InviteLinkGenerator(str(bot_id))
    
    # Show detection success message
    if not args.bot_id:
        print(f"✅ Auto-detected Bot ID: {bot_id}")
    
    # Determine permissions based on arguments
    if args.admin:
        permissions = generator.get_admin_permissions()
        mode = "Administrator"
    elif args.minimal:
        permissions = generator.get_minimal_permissions()
        mode = "Minimal"
    elif args.custom:
        permissions = generator.interactive_permissions()
        mode = "Custom"
    else:
        permissions = generator.get_recommended_permissions()
        mode = "Recommended"
    
    # Generate link
    link = generator.generate_link(permissions)
    
    # Print results
    print(f"Mode: {mode} Permissions")
    print_invite_info(generator, permissions, link)


if __name__ == "__main__":
    main()
