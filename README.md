# Web Tech Daily → Discord

Web系チーム向けに、公式RSS/Atomの当日（JST）アップデートを集め、重要な変更を日本語で短くまとめてDiscordへ送るPythonジョブです。AWS、React、Next.js、Cloudflare、Google Cloud、Viteに加え、Chrome/Web Platform/CSS、Node.js、TypeScript、OpenAIを初期監視対象にしています。

外部Pythonパッケージは不要です。Python 3.11以上の標準ライブラリだけで、RSS/Atom・HTTP・XML・Discord Webhook・OpenAI APIを扱います。OpenAI APIキーがある場合はResponses APIで「実務に重要な最大10件」へ選別・日本語要約します。キーを設定しない場合も、一次ソースの新着をそのまま通知できます。

## 仕組み

```text
公式 RSS / Atom
  → JSTの対象日で絞り込み
  → 送信済みURLを除外
  → OpenAIで優先順位付け・要約（任意）
  → Discord Incoming Webhook
  → data/state.json にURLを記録
```

監視先は [app/sources.py](app/sources.py) にまとまっています。追加したい技術・ベンダーは、公式RSS/Atom URLを1件追加するだけです。記事本文を巡回せず、フィードに含まれる説明だけをAPIへ渡します。

## 初回セットアップ

1. Discordの対象チャンネルで「チャンネル設定 → 連携サービス → ウェブフック」からIncoming Webhookを作成します。
2. `.env.example` を参考に、環境変数を設定します。キーは絶対にGitへ追加しません。

```sh
export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'
export OPENAI_API_KEY='...' # OpenAI要約を使う場合のみ
export OPENAI_MODEL='gpt-5.6-luna' # 任意
```

3. まず投稿せず内容を確認します。

```sh
python -m app.main --dry-run
```

4. 問題なければ実際に送信します。

```sh
python -m app.main
```

任意の日を再集計するには `python -m app.main --dry-run --date 2026-08-11` のように指定します。通常運用時、同じURLは `data/state.json` により二重投稿されません。再投稿を確認したい場合のみ `INCLUDE_PREVIOUSLY_SENT=true` を設定してください。

## GitHub Actionsで毎朝配信する

このリポジトリをGitHubへpush後、リポジトリの **Settings → Secrets and variables → Actions** で次を登録します。

| Secret | 必須 | 内容 |
| --- | --- | --- |
| `DISCORD_WEBHOOK_URL` | はい | Discord Incoming Webhook URL |
| `OPENAI_API_KEY` | いいえ | OpenAI API key |

`.github/workflows/daily.yml` は毎日08:00 JST（23:00 UTC）に実行します。手動実行（`workflow_dispatch`）にも対応します。送信済みURLをGitへ記録するため、Actionsには `contents: write` 権限が必要です。

## 保守の方針

- 情報源の追加・削除は `app/sources.py` のみを変更します。一次情報を優先してください。
- RSS/Atomの解析・API要約・Discord投稿は関数を分離し、`tests/` で標準の `unittest` により検証します。
- すべてのフィード取得に失敗した場合、空の「更新なし」通知は送らず、ジョブを失敗として終了します。OpenAI APIが失敗した場合も同様です。一部フィードが失敗しても、残りの情報源で配信し、実行ログに失敗元を残します。
- OpenAIのモデルは `OPENAI_MODEL` で変更できます。標準はコスト重視の `gpt-5.6-luna` です。

OpenAI APIは公式のResponses APIを使用しています。キー管理とAPIの基本は[公式OpenAIドキュメント](https://developers.openai.com/api/docs/models)を確認してください。

検証コマンドは次のとおりです。

```sh
python -m unittest discover -s tests -v
```
