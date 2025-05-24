#!/bin/bash
# Quick setup test for UtilsBot+

echo "🤖 UtilsBot+ - Setup Verification"
echo "======================================"

echo ""
echo "📂 Checking project structure..."
if [ -f "main.py" ]; then
    echo "✅ main.py found"
else
    echo "❌ main.py missing"
fi

if [ -f "setup.py" ]; then
    echo "✅ setup.py found"
else
    echo "❌ setup.py missing"
fi

if [ -d "cogs" ]; then
    echo "✅ cogs directory found"
    echo "   📁 Available cogs:"
    ls cogs/*.py | sed 's/cogs\///g' | sed 's/\.py//g' | sed 's/^/     - /'
else
    echo "❌ cogs directory missing"
fi

echo ""
echo "🔍 Checking for prefix commands (should be 0)..."
prefix_commands=$(grep -r "@commands.command" cogs/ 2>/dev/null | wc -l)
echo "   Prefix commands found: $prefix_commands"

echo ""
echo "🔍 Checking for slash commands..."
slash_commands=$(grep -r "@app_commands.command" cogs/ 2>/dev/null | wc -l)
echo "   Slash commands found: $slash_commands"

echo ""
echo "📋 Commands available:"
echo "   🏃 For first-time setup: python setup.py"
echo "   🚀 To run the bot: python main.py"

echo ""
echo "✅ Project verification complete!"
