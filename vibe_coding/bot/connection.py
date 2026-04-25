"""Twitch IRC connection handler using asyncio."""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Callable

import aiohttp

from vibe_coding.config import get_config, get_twitch_nick, get_twitch_oauth

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a message from Twitch chat."""

    username: str
    message: str
    channel: str


class TwitchBot:
    """Twitch IRC bot for VibeTCoder."""

    def __init__(self) -> None:
        """Initialize the bot."""
        self._config = get_config()
        self._reader: asyncio.StreamReader = None  # type: ignore[assignment]
        self._writer: asyncio.StreamWriter = None  # type: ignore[assignment]
        self._running = False
        self._message_queue: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self._handlers: list[Callable[[ChatMessage], None]] = []

    async def connect(self) -> None:
        """Connect to Twitch IRC server."""
        nick = get_twitch_nick()
        oauth = get_twitch_oauth()
        channel = self._config["twitch"]["channel"]
        server = self._config["twitch"]["irc_server"]
        port = self._config["twitch"]["irc_port"]

        logger.info(f"Connecting to {server}:{port} as {nick}...")

        self._reader, self._writer = await asyncio.open_connection(server, port)

        self._writer.write(f"PASS {oauth}\r\n".encode())
        self._writer.write(f"NICK {nick}\r\n".encode())
        self._writer.write(f"JOIN #{channel}\r\n".encode())
        await self._writer.drain()

        self._running = True
        logger.info(f"Connected to #{channel}")

        asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        """Read messages from Twitch IRC server."""
        ping_pattern = re.compile(rb"PING (:.*)?\r\n")

        while self._running:
            try:
                line = await self._reader.readline()
                if not line:
                    break

                decoded = line.decode("utf-8", errors="ignore").strip()
                logger.debug(f"← {decoded}")

                if ping_pattern.match(line):
                    self._writer.write(b"PONG :tmi.twitch.tv\r\n")
                    await self._writer.drain()
                    continue

                if decoded.startswith(":"):
                    await self._handle_message(decoded)

            except Exception as e:
                logger.error(f"Error reading: {e}")
                break

        await self.disconnect()

    async def _handle_message(self, line: str) -> None:
        """Parse and handle IRC message.

        Args:
            line: Raw IRC message line.
        """
        parts = line.split(" ", 4)
        if len(parts) < 5:
            return

        prefix = parts[0][1:]
        command = parts[1]
        channel = parts[2][1:]
        message = parts[4][1:]

        username = prefix.split("!")[0] if "!" in prefix else prefix

        if command == "PRIVMSG":
            chat_msg = ChatMessage(username=username, message=message, channel=channel)
            await self._message_queue.put(chat_msg)

            for handler in self._handlers:
                try:
                    handler(chat_msg)
                except Exception as e:
                    logger.error(f"Handler error: {e}")

    def add_handler(self, handler: Callable[[ChatMessage], None]) -> None:
        """Add a message handler.

        Args:
            handler: Callback function to handle messages.
        """
        self._handlers.append(handler)

    async def get_message(self, timeout: float | None = None) -> ChatMessage:
        """Get the next message from the queue.

        Args:
            timeout: Timeout in seconds.

        Returns:
            Chat message.

        Raises:
            asyncio.TimeoutError: If timeout is reached.
        """
        return await asyncio.wait_for(self._message_queue.get(), timeout=timeout)

    async def disconnect(self) -> None:
        """Disconnect from Twitch."""
        logger.info("Disconnecting...")
        self._running = False

        if self._writer:
            self._writer.write(b"QUIT\r\n")
            await self._writer.drain()
            self._writer.close()
            await self._writer.wait_closed()

        logger.info("Disconnected")

    async def send_message(self, message: str) -> None:
        """Send a message to the channel.

        Args:
            message: Message to send.
        """
        if not self._writer:
            raise RuntimeError("Not connected")

        channel = self._config["twitch"]["channel"]
        self._writer.write(f"PRIVMSG #{channel} :{message}\r\n".encode())
        await self._writer.drain()
        logger.debug(f"→ {message}")