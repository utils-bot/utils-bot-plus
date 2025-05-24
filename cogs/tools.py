"""
Tools and utilities cog for Utils Bot v2.0
"""

import base64
import io
import qrcode

import discord
from discord import app_commands
from discord.ext import commands
import pyotp

from utils.checks import cooldown
from utils.embeds import create_error_embed, create_success_embed

class ToolsCog(commands.Cog, name="Tools"):
    """Various utility tools and functions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @app_commands.command(name="totp", description="Generate TOTP (Time-based One-Time Password) code")
    @app_commands.describe(
        secret="Your TOTP secret key",
        ephemeral="Whether to show the response only to you (recommended: True)"
    )
    @requires_whitelist()
    @cooldown(rate=5, per=60)
    async def generate_totp(
        self,
        interaction: discord.Interaction,
        secret: str,
        ephemeral: bool = True
    ):
        """Generate a TOTP code from a secret key"""
        try:
            # Clean up the secret (remove spaces and convert to uppercase)
            cleaned_secret = secret.replace(" ", "").upper()
            
            # Validate base32 format
            try:
                base64.b32decode(cleaned_secret)
            except Exception:
                embed = create_error_embed(
                    "Invalid Secret",
                    "The provided secret is not a valid base32 string. Please check your secret key."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Generate TOTP
            totp = pyotp.TOTP(cleaned_secret)
            current_code = totp.now()
            
            # Calculate time remaining
            import time
            current_time = int(time.time())
            time_remaining = 30 - (current_time % 30)
            
            embed = create_success_embed(
                "🔐 TOTP Code Generated",
                f"**Current Code:** `{current_code}`\n**Time Remaining:** {time_remaining} seconds"
            )
            embed.add_field(
                name="⚠️ Security Notice",
                value="This code will expire in 30 seconds. Never share your TOTP secret with others!",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
            
            # Track API usage
            if self.bot.db:
                await self.bot.db.track_api_usage(interaction.user.id, "totp")
            
        except Exception as e:
            self.logger.error(f"TOTP generation error: {e}")
            embed = create_error_embed(
                "Generation Error",
                "An error occurred while generating the TOTP code. Please check your secret key."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="qr", description="Generate a QR code from text")
    @app_commands.describe(
        text="Text to encode in the QR code",
        size="QR code size (small, medium, large)",
        ephemeral="Whether to show the response only to you"
    )
    @app_commands.choices(size=[
        app_commands.Choice(name="Small", value="small"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Large", value="large")
    ])
    @requires_whitelist()
    @cooldown(rate=3, per=60)
    async def generate_qr(
        self,
        interaction: discord.Interaction,
        text: str,
        size: str = "medium",
        ephemeral: bool = False
    ):
        """Generate a QR code from text"""
        # Validate text length
        if len(text) > 2000:
            embed = create_error_embed(
                "Text Too Long",
                "QR code text must be 2000 characters or less."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=ephemeral)
        
        try:
            # Set QR code parameters based on size
            size_config = {
                "small": {"box_size": 5, "border": 2},
                "medium": {"box_size": 8, "border": 3},
                "large": {"box_size": 12, "border": 4}
            }
            
            config = size_config.get(size, size_config["medium"])
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_L,
                box_size=config["box_size"],
                border=config["border"]
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, "PNG") 
            img_bytes.seek(0)
            
            # Create Discord file
            file = discord.File(img_bytes, filename="qrcode.png")
            
            embed = create_success_embed(
                "QR Code Generated",
                f"**Size:** {size.title()}\n**Content:** {text[:100]}{'...' if len(text) > 100 else ''}"
            )
            embed.set_image(url="attachment://qrcode.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
            # Track API usage
            if self.bot.db:
                await self.bot.db.track_api_usage(interaction.user.id, "qr_code")
            
        except Exception as e:
            self.logger.error(f"QR code generation error: {e}")
            embed = create_error_embed(
                "Generation Error",
                "An error occurred while generating the QR code."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="base64", description="Encode or decode base64 text")
    @app_commands.describe(
        text="Text to encode/decode",
        operation="Whether to encode or decode",
        ephemeral="Whether to show the response only to you"
    )
    @app_commands.choices(operation=[
        app_commands.Choice(name="Encode", value="encode"),
        app_commands.Choice(name="Decode", value="decode")
    ])
    @requires_whitelist()
    @cooldown(rate=5, per=60)
    async def base64_convert(
        self,
        interaction: discord.Interaction,
        text: str,
        operation: str,
        ephemeral: bool = False
    ):
        """Encode or decode base64 text"""
        if len(text) > 1900:
            embed = create_error_embed(
                "Text Too Long",
                "Text must be 1900 characters or less."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            if operation == "encode":
                # Encode to base64
                encoded_bytes = base64.b64encode(text.encode('utf-8'))
                result = encoded_bytes.decode('utf-8')
                title = "Base64 Encoded"
                
            else:  # decode
                # Decode from base64
                try:
                    decoded_bytes = base64.b64decode(text)
                    result = decoded_bytes.decode('utf-8')
                    title = "Base64 Decoded"
                except Exception:
                    embed = create_error_embed(
                        "Invalid Base64",
                        "The provided text is not valid base64."
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            # Truncate if result is too long
            if len(result) > 1900:
                result = result[:1900] + "\n... (truncated)"
            
            embed = create_success_embed(
                title,
                f"**Input:** `{text[:500]}{'...' if len(text) > 500 else ''}`\n**Result:** `{result}`"
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
            
        except Exception as e:
            self.logger.error(f"Base64 conversion error: {e}")
            embed = create_error_embed(
                "Conversion Error",
                "An error occurred during the conversion."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="hash", description="Generate hash of text")
    @app_commands.describe(
        text="Text to hash",
        algorithm="Hash algorithm to use",
        ephemeral="Whether to show the response only to you"
    )
    @app_commands.choices(algorithm=[
        app_commands.Choice(name="MD5", value="md5"),
        app_commands.Choice(name="SHA1", value="sha1"),
        app_commands.Choice(name="SHA256", value="sha256"),
        app_commands.Choice(name="SHA512", value="sha512")
    ])
    @requires_whitelist()
    @cooldown(rate=5, per=60)
    async def generate_hash(
        self,
        interaction: discord.Interaction,
        text: str,
        algorithm: str = "sha256",
        ephemeral: bool = False
    ):
        """Generate hash of the provided text"""
        import hashlib
        
        if len(text) > 10000:
            embed = create_error_embed(
                "Text Too Long",
                "Text must be 10,000 characters or less."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Get hash function
            hash_func = getattr(hashlib, algorithm)
            
            # Generate hash
            hash_object = hash_func(text.encode('utf-8'))
            result = hash_object.hexdigest()
            
            embed = create_success_embed(
                f"{algorithm.upper()} Hash Generated",
                f"**Input:** `{text[:200]}{'...' if len(text) > 200 else ''}`\n**Hash:** `{result}`"
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
            
        except Exception as e:
            self.logger.error(f"Hash generation error: {e}")
            embed = create_error_embed(
                "Hash Error",
                "An error occurred while generating the hash."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="password", description="Generate a secure password")
    @app_commands.describe(
        length="Password length (8-128 characters)",
        include_symbols="Include special symbols",
        exclude_ambiguous="Exclude ambiguous characters (0, O, l, I, etc.)"
    )
    @requires_whitelist()
    @cooldown(rate=3, per=60)
    async def generate_password(
        self,
        interaction: discord.Interaction,
        length: int = 16,
        include_symbols: bool = True,
        exclude_ambiguous: bool = True
    ):
        """Generate a secure random password"""
        import secrets
        import string
        
        # Validate length
        if not 8 <= length <= 128:
            embed = create_error_embed(
                "Invalid Length",
                "Password length must be between 8 and 128 characters."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Build character set
            chars = string.ascii_letters + string.digits
            
            if include_symbols:
                chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            if exclude_ambiguous:
                # Remove ambiguous characters
                ambiguous = "0O1lI"
                chars = ''.join(c for c in chars if c not in ambiguous)
            
            # Generate password
            password = ''.join(secrets.choice(chars) for _ in range(length))
            
            embed = create_success_embed(
                "🔐 Secure Password Generated",
                f"**Password:** `{password}`\n**Length:** {length} characters"
            )
            embed.add_field(
                name="⚠️ Security Notice",
                value="Store this password securely and never share it in public channels!",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Password generation error: {e}")
            embed = create_error_embed(
                "Generation Error",
                "An error occurred while generating the password."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ToolsCog(bot))
