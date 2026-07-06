"""
JEBAT Discord Channel Integration

Discord bot integration for JEBAT AI Assistant.

Features:
- Slash commands
- Direct messages
- Server-specific settings
- Rich embeds
- Thread support

Usage:
    from jebat.integrations.channels.discord import DiscordChannel

    channel = DiscordChannel(
        bot_token="YOUR_BOT_TOKEN",
        ultra_loop=loop,
    )
    await channel.start()
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class DiscordChannel:
    """
    Discord bot channel integration.

    Supports:
    - Slash commands (/think, /status, /help)
    - Direct messages
    - Server configuration
    - Rich embeds
    - Message reactions
    """

    def __init__(
        self,
        bot_token: str,
        ultra_loop=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Discord channel.

        Args:
            bot_token: Discord bot token
            ultra_loop: Ultra-Loop instance for message processing
            config: Additional configuration
        """
        self.bot_token = bot_token
        self.ultra_loop = ultra_loop
        self.config = config or {}

        # Bot state
        self._client = None
        self._running = False

        # Server configurations
        self.server_configs: Dict[str, Dict] = {}

        # Message handlers
        self.message_handlers: List[Callable] = []

        # Slash command handlers
        self.command_handlers: Dict[str, Callable] = {}

        logger.info("DiscordChannel initialized")

    async def start(self):
        """Start Discord bot"""
        if self._running:
            logger.warning("Discord bot already running")
            return

        try:
            # Import discord.py
            import discord
            from discord import app_commands
            from discord.ext import commands

            # Create bot
            intents = discord.Intents.default()
            intents.message_content = True
            intents.dm_typing = True

            self._client = commands.Bot(command_prefix="!", intents=intents)

            # Setup event handlers
            @self._client.event
            async def on_ready():
                logger.info(f"Discord bot logged in as {self._client.user}")

                # Sync slash commands
                try:
                    synced = await self._client.tree.sync()
                    logger.info(f"Synced {len(synced)} slash commands")
                except Exception as e:
                    logger.error(f"Failed to sync commands: {e}")

                self._running = True

            @self._client.event
            async def on_message(message):
                # Ignore bot's own messages
                if message.author == self._client.user:
                    return

                # Process message
                await self._process_message(message)

            # Register slash commands
            self._register_slash_commands()

            # Start bot
            await self._client.start(self.bot_token)

        except ImportError:
            logger.error("discord.py not installed. Run: pip install discord.py")
            raise
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            raise

    async def stop(self):
        """Stop Discord bot"""
        self._running = False

        if self._client:
            await self._client.close()
            self._client = None

        logger.info("Discord bot stopped")

    def _register_slash_commands(self):
        """Register slash commands with Discord"""

        @self._client.tree.command(
            name="think", description="Ask JEBAT to think about something"
        )
        @app_commands.describe(question="Your question for JEBAT")
        @app_commands.describe(mode="Thinking mode (fast, deliberate, deep)")
        async def think(
            interaction: discord.Interaction, question: str, mode: str = "deliberate"
        ):
            """Think about a question"""
            await interaction.response.defer()

            if not self.ultra_loop or not self.ultra_loop.ultra_think:
                await interaction.followup.send("❌ Ultra-Think not initialized")
                return

            try:
                from jebat.features.ultra_think import ThinkingMode

                thinking_mode = ThinkingMode(mode.lower())
                result = await self.ultra_loop.ultra_think.think(
                    problem=question,
                    mode=thinking_mode,
                    timeout=30,
                )

                embed = discord.Embed(
                    title="🗡️ JEBAT Thinking Result",
                    description=result.conclusion[:1024],
                    color=discord.Color.blue(),
                )
                embed.add_field(
                    name="Confidence", value=f"{result.confidence:.1%}", inline=True
                )
                embed.add_field(
                    name="Thinking Steps",
                    value=len(result.reasoning_steps),
                    inline=True,
                )
                embed.add_field(name="Mode", value=mode, inline=True)
                embed.set_footer(text=f"User: {interaction.user.name}")

                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"Think command error: {e}")
                await interaction.followup.send(f"❌ Error: {str(e)}")

        @self._client.tree.command(
            name="status", description="Check JEBAT system status"
        )
        async def status(interaction: discord.Interaction):
            """Show system status"""
            await interaction.response.defer()

            if not self.ultra_loop:
                await interaction.followup.send("❌ Ultra-Loop not initialized")
                return

            metrics = self.ultra_loop.get_metrics()

            embed = discord.Embed(
                title="🗡️ JEBAT System Status",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Ultra-Loop",
                value=f"Cycles: {metrics.get('total_cycles', 0)}\n"
                f"Success: {metrics.get('successful_cycles', 0)}\n"
                f"Failed: {metrics.get('failed_cycles', 0)}",
                inline=True,
            )
            embed.add_field(
                name="Performance",
                value=f"Avg Cycle: {metrics.get('avg_cycle_time', 0):.3f}s\n"
                f"Last Cycle: {metrics.get('last_cycle_time', 0):.3f}s",
                inline=True,
            )
            embed.set_footer(text=f"Requested by {interaction.user.name}")

            await interaction.followup.send(embed=embed)

        @self._client.tree.command(
            name="help", description="Show JEBAT help information"
        )
        async def help_cmd(interaction: discord.Interaction):
            """Show help information"""
            await interaction.response.defer()

            embed = discord.Embed(
                title="🗡️ JEBAT AI Assistant",
                description="Your personal AI assistant with eternal memory",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Commands",
                value="/think <question> [mode] - Ask JEBAT to think\n"
                "/status - Check system status\n"
                "/help - Show this help",
                inline=False,
            )
            embed.add_field(
                name="Thinking Modes",
                value="fast - Quick responses\n"
                "deliberate - Careful reasoning\n"
                "deep - Comprehensive analysis",
                inline=False,
            )
            embed.add_field(
                name="Features",
                value="✅ Eternal Memory\n✅ Deep Reasoning\n✅ Multi-Agent Support",
                inline=False,
            )
            embed.set_footer(text="JEBAT v1.0.0")

            await interaction.followup.send(embed=embed)

        logger.info("Slash commands registered")

    async def _process_message(self, message):
        """Process incoming message"""
        content = message.content
        channel = message.channel
        author = message.author
        guild = message.guild

        logger.info(
            f"Discord message from {author} in {guild or 'DM'}: {content[:50]}..."
        )

        # Handle direct messages
        if isinstance(channel, discord.DMChannel):
            await self._handle_dm(channel, author, content)
            return

        # Handle mentions
        if self._client.user in message.mentions:
            # Remove mention from content
            clean_content = content.replace(f"<@{self._client.user.id}>", "").strip()
            await self._handle_mention(channel, author, clean_content)

    async def _handle_dm(self, channel, author, content):
        """Handle direct message"""
        logger.info(f"DM from {author}: {content}")

        # Process through Ultra-Loop if connected
        if self.ultra_loop:
            try:
                from jebat.features.ultra_think import ThinkingMode

                result = await self.ultra_loop.ultra_think.think(
                    problem=content,
                    mode=ThinkingMode.DELIBERATE,
                    user_id=str(author.id),
                    timeout=30,
                )

                # Send response
                await channel.send(result.conclusion[:2000])  # Discord limit

            except Exception as e:
                logger.error(f"DM processing error: {e}")
                await channel.send(f"Error processing message: {e}")

    async def _handle_mention(self, channel, author, content):
        """Handle bot mention"""
        logger.info(f"Mention from {author}: {content}")

        if not content:
            await channel.send(
                "Hi! Use `/think <question>` to ask me something, or just mention me with your question!"
            )
            return

        # Process question
        await self._handle_dm(channel, author, content)

    async def send_message(
        self,
        channel_id: int,
        message: str,
        embed: Optional[Dict] = None,
        **kwargs,
    ):
        """
        Send message to Discord channel.

        Args:
            channel_id: Discord channel ID
            message: Message text
            embed: Optional embed dict
            **kwargs: Additional arguments
        """
        if not self._client:
            raise Exception("Discord bot not running")

        channel = self._client.get_channel(channel_id)
        if not channel:
            raise Exception(f"Channel not found: {channel_id}")

        # Create embed if provided
        discord_embed = None
        if embed:
            discord_embed = discord.Embed.from_dict(embed)

        await channel.send(content=message, embed=discord_embed)
        logger.debug(f"Sent Discord message to channel {channel_id}")

    def add_message_handler(self, handler: Callable):
        """
        Add message handler.

        Args:
            handler: Async callable that receives (channel, author, content)
        """
        self.message_handlers.append(handler)
        logger.info(f"Added Discord message handler: {handler.__name__}")

    def get_server_config(self, guild_id: str) -> Dict:
        """Get server-specific configuration"""
        return self.server_configs.get(guild_id, {})

    def set_server_config(self, guild_id: str, config: Dict):
        """Set server-specific configuration"""
        self.server_configs[guild_id] = config
        logger.info(f"Updated config for server {guild_id}")


async def create_discord_channel(
    bot_token: str,
    ultra_loop=None,
    config: Optional[Dict[str, Any]] = None,
) -> DiscordChannel:
    """
    Factory function to create Discord channel.

    Args:
        bot_token: Discord bot token
        ultra_loop: Ultra-Loop instance
        config: Configuration

    Returns:
        DiscordChannel instance
    """
    channel = DiscordChannel(
        bot_token=bot_token,
        ultra_loop=ultra_loop,
        config=config,
    )
    return channel
