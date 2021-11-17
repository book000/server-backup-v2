import json
import os


class Config:
    """
    設定
    """
    def __init__(self, filename: str = "config.json"):
        self.filename = filename

        # 通知用 Discord Bot 設定
        self.DISCORD_TOKEN = self.getValue("discord.token")
        self.DISCORD_CHANNEL = self.getValue("discord.channel")
        self.DISCORD_FOOTER = self.getValue("discord.footer", None)

        # バックアップ用とログ用のディレクトリ
        self.BACKUP_DIR = self.getValue("dir.backup", "backup/")
        if not self.BACKUP_DIR.endswith("/"):
            self.BACKUP_DIR += "/"
        if not os.path.isabs(self.BACKUP_DIR):
            self.BACKUP_DIR = os.path.abspath(self.BACKUP_DIR)
        if not os.path.exists(self.BACKUP_DIR):
            os.makedirs(self.BACKUP_DIR)

        self.LOG_DIR = self.getValue("dir.logs", "logs/")
        if not self.LOG_DIR.endswith("/"):
            self.LOG_DIR += "/"
        if not os.path.isabs(self.LOG_DIR):
            self.LOG_DIR = os.path.abspath(self.LOG_DIR)
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)

        # データベースバックアップ設定
        self.DB_ENABLE: bool = bool(self.getValue("db.enable", False))
        self.DB_KEEP_DAYS: int = int(self.getValue("db.keep_days", 30)) if self.DB_ENABLE else None
        self.DB_HOSTNAME = self.getValue("db.hostname") if self.DB_ENABLE else None
        self.DB_PORT: int = int(self.getValue("db.port")) if self.DB_ENABLE else None
        self.DB_USERNAME = self.getValue("db.username") if self.DB_ENABLE else None
        self.DB_PASSWORD = self.getValue("db.password") if self.DB_ENABLE else None

        # 全体ディレクトリ/ファイルバックアップ (SSH)
        self.FULL_ENABLE: bool = bool(self.getValue("full.enable", False))
        self.FULL_KEEP_DAYS: int = int(self.getValue("full.keep_days", 30)) if self.FULL_ENABLE else None
        self.FULL_HOSTNAME = self.getValue("full.hostname") if self.FULL_ENABLE else None
        self.FULL_PORT: int = int(self.getValue("full.port")) if self.FULL_ENABLE else None
        self.FULL_USERNAME = self.getValue("full.username") if self.FULL_ENABLE else None
        self.FULL_PASSWORD = self.getValue("full.password") if self.FULL_ENABLE else None
        self.FULL_IDENTITY = self.getValue("full.identity") if self.FULL_ENABLE else None
        self.FULL_PASSPHRASE = self.getValue("full.passphrase") if self.FULL_ENABLE else None
        self.FULL_FROM = self.getValue("full.from", "/") if self.FULL_ENABLE else None
        self.IGNORES: list[str] = self.getValue("full.ignores", []) if self.FULL_ENABLE else None

    def getValue(self,
                 _key: str,
                 default_value=None):
        with open(self.filename) as f:
            config = json.load(f)
        if "." in _key:
            keys = _key.split(".")
        else:
            keys = [_key]
        value = config
        try:
            for key in keys:
                value = value[key]
        except KeyError:
            value = default_value
        if default_value is None and value is None:
            print("[ERROR] {} is not defined.".format(_key))
            exit(1)
        return default_value if value == config else value
