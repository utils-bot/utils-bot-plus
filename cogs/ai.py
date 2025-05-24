"""AI commands cog for UtilsBot+ using Google Gemini"""

import asyncio
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai

from config.settings import settings, assets
from core.logger import get_logger
from utils.checks import requires_whitelist, cooldown
from utils.embeds import create_embed, create_error_embed, create_loading_embed


class AICog(commands.Cog, name="AI"):
    """AI-powered commands using Google Gemini"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
        
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            self.vision_model = genai.GenerativeModel('models/gemini-1.5-flash')
        else:
            self.model = None
            self.vision_model = None
    

    
    @app_commands.command(name="ask", description="Ask Gemini AI a question")
    @app_commands.describe(
        question="Your question for Gemini",
        ephemeral="Whether to show the response only to you (default: public)"
    )
    @requires_whitelist()
    @cooldown(rate=3, per=60)  # 3 questions per minute
    async def ask_gemini(
        self, 
        interaction: discord.Interaction,
        question: str,
        ephemeral: bool = False
    ):
        """Ask Gemini AI a question"""
        if not self.model:
            embed = create_error_embed(
                "Service Unavailable",
                "Gemini AI is not configured on this bot"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Show loading message
        loading_embed = create_loading_embed(
            "Asking Gemini...",
            "Please wait while I process your question"
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=ephemeral)
        
        try:
            if self.bot.db:
                await self.bot.db.track_api_usage(interaction.user.id, "gemini")
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                question
            )
            
            answer = response.text
            
            if len(answer) > 3800:
                answer = answer[:3800] + "\n\n... (truncated)"
            
            formatted_response = f"**Question:** {question}\n\n**Answer:**\n{answer}"
            
            embed = create_embed(
                "🤖 Gemini AI Response",
                formatted_response,
                thumbnail=assets.GEMINI_ICON_URL
            )
            embed.set_footer(text=f"Asked by {interaction.user.display_name}")
            
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            embed = create_error_embed(
                "AI Error",
                "Sorry, I encountered an error while processing your question. Please try again later."
            )
            await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="chat", description="Chat with Gemini AI")
    @app_commands.describe(
        message="Your message to Gemini",
        ephemeral="Whether to show the response only to you (default: public)"
    )
    @requires_whitelist()
    @cooldown(rate=3, per=60)  # 3 messages per minute
    async def chat_with_gemini(
        self, 
        interaction: discord.Interaction, 
        message: str,
        ephemeral: bool = False
    ):
        """Chat with Gemini AI"""
        if not self.model:
            embed = create_error_embed(
                "Service Unavailable",
                "Gemini AI is not configured on this bot"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Show loading message
        loading_embed = create_loading_embed(
            "Generating Response...",
            "Gemini is thinking..."
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=ephemeral)
        
        try:
            if self.bot.db:
                await self.bot.db.track_api_usage(interaction.user.id, "gemini")
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                message
            )
            
            answer = response.text
            
            if len(answer) > 4000:
                answer = answer[:4000] + "\n\n... (truncated)"
            
            embed = create_embed(
                "🤖 Gemini Chat Response",
                answer,
                thumbnail=assets.GEMINI_ICON_URL
            )
            embed.add_field(
                name="💭 Your Message",
                value=message if len(message) <= 1024 else message[:1021] + "...",
                inline=False
            )
            embed.set_footer(text=f"Chat by {interaction.user.display_name}")
            
            view = ContinueChatView(self.model, self.bot, interaction.user)
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            self.logger.error(f"Gemini chat error: {e}")
            embed = create_error_embed(
                "Chat Error",
                "Sorry, I encountered an error while processing your message. Please try again later."
            )
            await interaction.edit_original_response(embed=embed)


class ChatModal(discord.ui.Modal, title="Chat with Gemini AI"):
    """Modal for chatting with Gemini"""
    
    def __init__(self, model, bot, user):
        super().__init__(timeout=300)
        self.model = model
        self.bot = bot
        self.user = user
    
    message = discord.ui.TextInput(
        label="Your Message",
        placeholder="Type your message to Gemini...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle chat submission"""
        loading_embed = create_loading_embed(
            "Generating Response...",
            "Gemini is thinking..."
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=False)
        
        try:
            if self.bot.db:
                await self.bot.db.track_api_usage(self.user.id, "gemini")
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                self.message.value
            )
            
            answer = response.text
            
            if len(answer) > 4000:
                answer = answer[:4000] + "\n\n... (truncated)"
            
            embed = create_embed(
                "🤖 Gemini Chat Response",
                answer,
                thumbnail=assets.GEMINI_ICON_URL
            )
            embed.add_field(
                name="💭 Your Message",
                value=self.message.value if len(self.message.value) <= 1024 else self.message.value[:1021] + "...",
                inline=False
            )
            embed.set_footer(text=f"Chat started by {self.user.display_name}")
            
            view = ContinueChatView(self.model, self.bot, self.user)
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            embed = create_error_embed(
                "Chat Error",
                "Sorry, I encountered an error. Please try again."
            )
            await interaction.edit_original_response(embed=embed)


class ContinueChatView(discord.ui.View):
    """View for continuing chat with Gemini"""
    
    def __init__(self, model, bot, user):
        super().__init__(timeout=300)
        self.model = model
        self.bot = bot
        self.user = user
    
    @discord.ui.button(label="Continue Chat", style=discord.ButtonStyle.primary, emoji="💬")
    async def continue_chat(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Continue the chat"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "Only the original user can continue this chat.",
                ephemeral=True
            )
            return
        
        modal = ChatModal(self.model, self.bot, self.user)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="End Chat", style=discord.ButtonStyle.secondary, emoji="🔚")
    async def end_chat(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End the chat"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "Only the original user can end this chat.",
                ephemeral=True
            )
            return
        
        embed = create_embed(
            "Chat Ended",
            "Thanks for chatting with Gemini! Use `/ask` or `/chat` for more conversations.",
            color=assets.SUCCESS_COLOR
        )
        
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    if settings.enable_ai_commands:
        await bot.add_cog(AICog(bot))
