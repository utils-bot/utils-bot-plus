"""
Games cog for Utils Bot v2.0
"""

import random
from pathlib import Path
from typing import List, Optional, Dict, Union

import discord
from discord import app_commands
from discord.ext import commands

try:
    from config.settings import settings
except ImportError:
    class Settings:
        enable_games = True
    settings = Settings()

try:
    from core.logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

try:
    from utils.checks import requires_whitelist, cooldown
except ImportError:
    def requires_whitelist():
        def decorator(func):
            return func
        return decorator
    
    def cooldown(rate, per):
        def decorator(func):
            _ = rate  # Suppress unused argument warning
            _ = per   # Suppress unused argument warning
            return func
        return decorator

try:
    from utils.embeds import create_embed, create_error_embed, create_success_embed
except ImportError:
    def create_embed(title, description, color=0x00ff00):
        embed = discord.Embed(title=title, description=description, color=color)
        return embed
    
    def create_error_embed(title, description):
        embed = discord.Embed(title=title, description=description, color=0xff0000)
        return embed
    
    def create_success_embed(title, description):
        embed = discord.Embed(title=title, description=description, color=0x00ff00)
        return embed


class GamesCog(commands.Cog, name="Games"):
    """Interactive games and entertainment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
        self.wordle_words: List[str] = []
        self.active_games: Dict[int, 'WordleGame'] = {}
    
    
    
    
    async def cog_load(self):
        """Load game data"""
        await self.load_wordle_words()
    
    async def load_wordle_words(self):
        """Load Wordle word list"""
        try:
            # Use the existing text file
            words_file = Path("assets/games/wordle_words.txt")
            
            if words_file.exists():
                with open(words_file, 'r', encoding='utf-8') as f:
                    self.wordle_words = [word.strip().upper() for word in f.readlines() if word.strip()]
            else:
                # Fallback word list
                self.wordle_words = [
                    "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT", "AFTER", "AGAIN",
                    "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIEN", "ALIGN", "ALIKE", "ALIVE",
                    "ALLOW", "ALONE", "ALONG", "ALTER", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY",
                    "ARENA", "ARGUE", "ARISE", "ARRAY", "ARROW", "ASIDE", "ASSET", "AUDIO", "AUDIT", "AVOID",
                    "AWAKE", "AWARD", "AWARE", "BADLY", "BAKER", "BASES", "BASIC", "BEACH", "BEGAN", "BEGIN",
                    "BEING", "BELOW", "BENCH", "BILLY", "BIRTH", "BLACK", "BLAME", "BLANK", "BLIND", "BLOCK",
                    "BLOOD", "BOARD", "BOOST", "BOOTH", "BOUND", "BRAIN", "BRAND", "BREAD", "BREAK", "BREED",
                    "BRIEF", "BRING", "BROAD", "BROKE", "BROWN", "BUILD", "BUILT", "BUYER", "CABLE", "CALIF",
                    "CARRY", "CATCH", "CAUSE", "CHAIN", "CHAIR", "CHAOS", "CHARM", "CHART", "CHASE", "CHEAP",
                    "CHECK", "CHEST", "CHIEF", "CHILD", "CHINA", "CHOSE", "CIVIL", "CLAIM", "CLASS", "CLEAN",
                    "CLEAR", "CLICK", "CLIMB", "CLOCK", "CLOSE", "CLOUD", "COACH", "COAST", "COULD", "COUNT",
                    "COURT", "COVER", "CRAFT", "CRASH", "CRAZY", "CREAM", "CRIME", "CROSS", "CROWD", "CROWN",
                    "CRUDE", "CURVE", "CYCLE", "DAILY", "DANCE", "DATED", "DEALT", "DEATH", "DEBUT", "DELAY"
                ]
            
            self.logger.info("Loaded %d Wordle words", len(self.wordle_words))
            
        except Exception as e:
            self.logger.error("Error loading Wordle words: %s", e)
            # Fallback to a minimal word list
            self.wordle_words = ["HELLO", "WORLD", "GAMES", "WORDS", "GUESS"]
    
    @app_commands.command(name="wordle", description="Start a game of Wordle")
    @requires_whitelist()
    @cooldown(rate=1, per=30)
    async def wordle(self, interaction: discord.Interaction):
        """Start a new Wordle game"""
        user_id = interaction.user.id
        
        # Check if user already has an active game
        if user_id in self.active_games:
            embed = create_error_embed(
                "Game Already Active",
                "You already have an active Wordle game! Use the buttons to make your guess or end the current game."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not self.wordle_words:
            embed = create_error_embed(
                "Game Unavailable",
                "Wordle word list is not available. Please try again later."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create new game
        word = random.choice(self.wordle_words)
        game = WordleGame(word, interaction.user)
        self.active_games[user_id] = game
        
        embed = create_embed(
            "🎮 Wordle Game Started!",
            "Guess the 5-letter word! You have 6 attempts.\n\n"
            "🟩 = Correct letter in correct position\n"
            "🟨 = Correct letter in wrong position\n"
            "⬛ = Letter not in word\n\n"
            "Click the button below to make your guess!",
            color=0x00ff00
        )
        
        view = WordleView(game, self)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Store the message for updates
        game.message = await interaction.original_response()


class WordleGame:
    """Represents a Wordle game instance"""
    
    def __init__(self, word: str, player: Union[discord.User, discord.Member]):
        self.word = word.upper()
        self.player = player
        self.guesses = []
        self.attempts = 0
        self.max_attempts = 6
        self.is_finished = False
        self.is_won = False
        self.message: Optional[discord.Message] = None
    
    def make_guess(self, guess: str) -> str:
        """Make a guess and return the result"""
        guess = guess.upper()
        self.guesses.append(guess)
        self.attempts += 1
        
        # Check if won
        if guess == self.word:
            self.is_won = True
            self.is_finished = True
        elif self.attempts >= self.max_attempts:
            self.is_finished = True
        
        return self.format_guess(guess)
    
    def format_guess(self, guess: str) -> str:
        """Format a guess with color indicators"""
        result = []
        word_letters = list(self.word)
        guess_letters = list(guess)
        
        # First pass: mark correct positions
        for i in range(5):
            if guess_letters[i] == word_letters[i]:
                result.append("🟩")
                word_letters[i] = ""
                guess_letters[i] = ""
            else:
                result.append(None)
        
        # Second pass: mark wrong positions
        for i in range(5):
            if result[i] is None:
                if guess_letters[i] and guess_letters[i] in word_letters:
                    result[i] = "🟨"
                    # Remove the letter to avoid double counting
                    word_letters[word_letters.index(guess_letters[i])] = ""
                else:
                    result[i] = "⬛"
        
        return "".join(result)
    
    def get_board(self) -> str:
        """Get the current game board"""
        board = []
        
        for guess in self.guesses:
            formatted = self.format_guess(guess)
            board.append(f"`{guess}` {formatted}")
        
        # Add empty rows
        for _ in range(len(self.guesses), self.max_attempts):
            board.append("`_____` ⬜⬜⬜⬜⬜")
        
        return "\n".join(board)


class WordleView(discord.ui.View):
    """View for Wordle game interactions"""
    
    def __init__(self, game: WordleGame, cog):
        super().__init__(timeout=300)
        self.game = game
        self.cog = cog
    
    @discord.ui.button(label="Make Guess", style=discord.ButtonStyle.primary, emoji="✏️")
    async def make_guess(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle guess input"""
        _ = button  # Suppress unused argument warning
        
        if interaction.user.id != self.game.player.id:
            await interaction.response.send_message(
                "Only the player can make guesses in this game!",
                ephemeral=True
            )
            return
        
        if self.game.is_finished:
            await interaction.response.send_message(
                "This game has already finished!",
                ephemeral=True
            )
            return
        
        modal = WordleGuessModal(self.game, self.cog, self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="End Game", style=discord.ButtonStyle.danger, emoji="🔚")
    async def end_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End the current game"""
        _ = button  # Suppress unused argument warning
        
        if interaction.user.id != self.game.player.id:
            await interaction.response.send_message(
                "Only the player can end this game!",
                ephemeral=True
            )
            return
        
        self.game.is_finished = True
        
        # Remove from active games
        if self.game.player.id in self.cog.active_games:
            del self.cog.active_games[self.game.player.id]
        
        embed = create_embed(
            "🎮 Wordle Game Ended",
            f"Game ended by player.\nThe word was: **{self.game.word}**\n\n{self.game.get_board()}",
            color=0xff0000
        )
        
        # Disable all buttons
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


class WordleGuessModal(discord.ui.Modal, title="Make Your Guess"):
    """Modal for Wordle guess input"""
    
    def __init__(self, game: WordleGame, cog, view: WordleView):
        super().__init__()
        self.game = game
        self.cog = cog
        self.view = view
    
    guess = discord.ui.TextInput(
        label="Your 5-letter guess",
        placeholder="Enter a 5-letter word...",
        min_length=5,
        max_length=5,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle guess submission"""
        guess_word = self.guess.value.upper()
        
        # Validate guess
        if len(guess_word) != 5 or not guess_word.isalpha():
            await interaction.response.send_message(
                "Please enter a valid 5-letter word!",
                ephemeral=True
            )
            return
        
        # Check if word is in word list (optional validation)
        if guess_word not in self.cog.wordle_words:
            # For now, allow any 5-letter word
            pass
        
        # Make the guess
        self.game.make_guess(guess_word)
        
        # Update embed
        if self.game.is_won:
            embed = create_success_embed(
                "🎉 Congratulations!",
                f"You guessed the word **{self.game.word}** in {self.game.attempts} attempts!\n\n{self.game.get_board()}"
            )
            
            # Update game stats
            if hasattr(self.cog.bot, 'db') and self.cog.bot.db:
                await self.cog.bot.db.update_game_stats(
                    self.game.player.id, 
                    "wordle", 
                    won=True, 
                    score=7 - self.game.attempts  # Higher score for fewer attempts
                )
            
            # Remove from active games
            if self.game.player.id in self.cog.active_games:
                del self.cog.active_games[self.game.player.id]
            
            # Disable buttons
            for item in self.view.children:
                if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                    item.disabled = True
            
        elif self.game.is_finished:
            embed = create_error_embed(
                "💔 Game Over",
                f"You've used all 6 attempts!\nThe word was: **{self.game.word}**\n\n{self.game.get_board()}"
            )
            
            # Update game stats
            if hasattr(self.cog.bot, 'db') and self.cog.bot.db:
                await self.cog.bot.db.update_game_stats(
                    self.game.player.id,
                    "wordle",
                    won=False
                )
            
            # Remove from active games
            if self.game.player.id in self.cog.active_games:
                del self.cog.active_games[self.game.player.id]
            
            # Disable buttons
            for item in self.view.children:
                if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                    item.disabled = True
        
        else:
            embed = create_embed(
                f"🎮 Wordle - Attempt {self.game.attempts}/{self.game.max_attempts}",
                f"Keep guessing!\n\n{self.game.get_board()}",
                color=0x00ff00
            )
        
        await interaction.response.edit_message(embed=embed, view=self.view)


async def setup(bot):
    if settings.enable_games:
        await bot.add_cog(GamesCog(bot))
