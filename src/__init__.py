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
    DBへのコネクションを取得します。

    Returns:
        Connection: コネクション
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
    数値をバイト数のフォーマットにします。

    Args:
        size (int): フォーマットする数値
        dec (int, optional): 小数点以下の桁数. Defaults to -1.
        separate (bool, optional): 単位を分けるかどうか. Defaults to False.

    Returns:
        str: フォーマットされた文字列
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

    if separate:
        return f"{result}{unit[unit_index]}"
    else:
        return f"{result}"


def log(file_path: str,
        message: str):
    """
    ログをファイルに書き込みます。

    Args:
        file_path (str): ファイルパス
        message (str): 書き込むメッセージ
    """

    print(f"[{datetime.now()}] {message}")
    with open(file_path, "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")


def send_discord_message(token: str, channelId: str, message: str = "", embed: dict = None):
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
