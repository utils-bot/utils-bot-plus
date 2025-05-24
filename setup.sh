#!/bin/bash
# Setup script for Utils Bot v2.0

echo "🤖 Utils Bot v2.0 Setup Script"
echo "================================"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Creating backup..."
    cp .env .env.backup.$(date +%s)
fi

# Copy example file
echo "📋 Creating .env file from template..."
cp .env.example .env

echo ""
echo "📝 Please configure the following REQUIRED environment variables in .env:"
echo ""
echo "1. BOT_TOKEN - Get from https://discord.com/developers/applications"
echo "   - Create a new application"
echo "   - Go to 'Bot' section"
echo "   - Copy the token"
echo ""
echo "2. DEV_IDS - Your Discord User ID"
echo "   - Enable Developer Mode in Discord settings"
echo "   - Right-click your profile and 'Copy User ID'"
echo ""
echo "3. GEMINI_API_KEY - Get from https://aistudio.google.com/app/apikey"
echo "   - Create a new API key (free tier available)"
echo ""
echo "4. SECRET_KEY - Generate a random string for encryption"
echo "   - You can use: python3 -c 'import secrets; print(secrets.token_hex(32))'"
echo ""

# Generate a secret key suggestion
if command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null)
    if [ ! -z "$SECRET_KEY" ]; then
        echo "💡 Suggested SECRET_KEY: $SECRET_KEY"
        echo ""
        # Automatically fill in the secret key
        sed -i "s/SECRET_KEY=your_secret_key_for_encryption_here/SECRET_KEY=$SECRET_KEY/" .env
        echo "✅ SECRET_KEY automatically generated and set!"
        echo ""
    fi
fi

echo "📂 Creating required directories..."
mkdir -p data logs

echo ""
echo "🔧 Next steps:"
echo "1. Edit .env file and fill in the required values"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Run the bot: python main.py"
echo ""
echo "📖 For detailed setup instructions, see README.md"
