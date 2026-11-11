import os
import subprocess
from datetime import datetime

import pymysql
import requests as requests
from pymysql import cursors

from src.config import Config


def get_connection(hostname: str,
                   port: int,
                   username: str,
                   password: str):
    """
    Open a connection to the database server.

    Args:
        hostname (str): Database host name
        port (int): Database port
        username (str): Database user name
        password (str): Database password

    Returns:
        Connection: PyMySQL connection using ``DictCursor``. The caller must close it.
    """

    return pymysql.connect(
        host=hostname,
        port=port,
        user=username,
        password=password,
        cursorclass=cursors.DictCursor
    )


def byte_format(size: int,
                dec=-1,
                separate=False):
    """
    Format a byte count as a human-readable string using 1024-based units.

    Args:
        size (int): Number of bytes
        dec (int, optional): Number of decimal places. -1 truncates to an integer. Defaults to -1.
        separate (bool, optional): Unused. Defaults to False.

    Returns:
        str: Formatted string such as ``1.5MB`` (no space between value and unit)
    """

    unit = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    result = size
    unit_index = 0

    while result >= 1024:
        result /= 1024
        unit_index += 1

    if dec == -1:
        result = int(result)
    else:
        result = round(result, dec)

    return f"{result}{unit[unit_index]}"


def log(file_path: str,
        message: str):
    """
    Print a timestamped message to stdout and append it to the log file.

    Args:
        file_path (str): Log file path
        message (str): Message to write
    """

    print(f"[{datetime.now()}] {message}")
    with open(file_path, "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")


def get_directory_size(dir_path: str):
    """
    Get the size of a directory in bytes using ``du -sb``.

    Args:
        dir_path (str): Directory path

    Returns:
        int: Size in bytes, or -1 if the directory does not exist
    """
    if not os.path.exists(dir_path):
        return -1

    command = "du -sb '%s' | awk '{ print $1 }'" % dir_path
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    print("get_directory_size: %s -> %s" % (command, result.stdout.strip()))
    return int(result.stdout.strip())


def send_discord_message(token: str, channelId: str, message: str = "", embed: dict = None):
    """
    Post a message to a Discord channel with the Bot token. The response is only printed.

    Args:
        token (str): Discord Bot token
        channelId (str): Target channel ID
        message (str, optional): Message text. Defaults to "".
        embed (dict, optional): Embed object. Defaults to None.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bot {token}".format(token=token),
        "User-Agent": "Bot"
    }
    params = {
        "content": message,
        "embed": embed
    }
    response = requests.post(
        "https://discord.com/api/channels/{channelId}/messages".format(channelId=channelId), headers=headers,
        json=params)
    print("[DEBUG] response: {code}".format(code=response.status_code))
    print("[DEBUG] response: {message}".format(message=response.text))


def notify(_config: Config, title: str, color: int, message: str = None):
    """
    Send an embed notification to the configured Discord channel.

    Args:
        _config (Config): Loaded configuration
        title (str): Embed title
        color (int): Embed color (for example ``0x008000`` for success, ``0xFF0000`` for failure)
        message (str, optional): Embed description. Defaults to None.
    """
    embed = {
        "title": title,
        "color": color,
    }
    if message is not None:
        embed["description"] = message
    if _config.DISCORD_FOOTER is not None:
        embed["footer"] = {
            "text": _config.DISCORD_FOOTER
        }
    send_discord_message(_config.DISCORD_TOKEN, _config.DISCORD_CHANNEL, "", embed)
