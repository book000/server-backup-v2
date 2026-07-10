# GitHub Copilot レビュー指示

このリポジトリのプルリクエストをレビューする際のガイドラインです。server-backup-v2 は Linux サーバのバックアップ（MySQL/MariaDB の DB バックアップと rsync による逆差分フルバックアップ）を自動実行する Python 製ツールです。

レビューコメントは日本語で記載してください。

## 重点的に確認する点

- **サブプロセス実行**: `subprocess.run(..., shell=True)` を多用している。ユーザー設定値（`config.json` 由来のホスト名・パス・認証情報など）をシェルコマンド文字列に埋め込む箇所では、シェルインジェクションの余地がないか確認する。特に `src/__main__.py` の `mysqldump` / `tar` / `rsync.sh` 呼び出しと、`src/__init__.py` の `du` 呼び出し。
- **戻り値チェック**: `subprocess.run` の `returncode` を確認しているか。失敗時に `log()` へ記録し `notify()` で Discord 通知したうえで `exit(1)` する既存パターンに沿っているか。
- **リソース解放**: DB 接続（`get_connection`）を `finally` で `close()` しているか。ファイルハンドルは `with` で開いているか。
- **例外の握りつぶし**: 例外を無視せず、ログ出力と Discord 通知を伴っているか。
- **保持期間削除ロジック**: 期限切れバックアップの削除（`shutil.rmtree` / `os.remove`）で、日付パースやディレクトリ判定の条件が正しいか。誤って有効なバックアップを削除しないか。

## セキュリティ

- `config.json`（Discord Bot トークン、DB パスワード、SSH 認証情報を含む）や生成される `conf` ファイルがコミットに含まれていないか。
- 認証情報がログ出力や Discord 通知に漏れていないか（`log()` / `notify()` / `print` に機密値を渡していないか）。
- DB バックアップ時に一時生成する `conf` ファイル（パスワードを含む）が、処理後に確実に削除されているか。

## コーディング規約（レビュー時に指摘してよい範囲）

- コード内コメントと docstring は日本語。エラーメッセージ（`log`/`notify` に渡す英語メッセージ）は英語。
- PEP 8 準拠: クラス名 PascalCase、関数・変数名 snake_case、定数 UPPER_SNAKE_CASE。インデントはスペース 4 つ。
- 関数・クラスには日本語 docstring を付与・更新する。
- 日本語と英数字の間には半角スペースを挿入する。

## フラグしなくてよい既知パターン

- `shell=True` そのものは既存の設計方針であり、インジェクション上の具体的な懸念がない箇所を一律に指摘する必要はない。
- テストコードの不在: 専用テストフレームワークは未使用で、CI は Docker ビルドと Hadolint のみ。テスト追加の欠如自体を毎回指摘しなくてよい。
- 最大行長 79 文字は「推奨」であり、既存コードにも超過箇所がある。軽微な超過を機械的に指摘しない。

## コミットメッセージ

- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 形式（`<type>(<scope>): <description>`）。`<description>` は日本語。
