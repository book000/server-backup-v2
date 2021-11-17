from datetime import datetime

import pymysql
from pymysql import cursors


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
