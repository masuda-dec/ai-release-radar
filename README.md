# AI Release Radar

**日本語 / 個人向け AI リリースダッシュボード**。Codex / Claude Code / Google Antigravity / OpenBot / MCP / Blender MCP / 生成 AI の公式更新をまとめ、個人向けに5段階で優先順位をつけます。

## まず試す（GitHubやAPIキーは不要）

ファイルを展開し、`index.html` をChromeなどのブラウザで開いてください。18件の2026年10月30日時点の初期データが表示されます。検索・カテゴリ別表示・有用度順・保存・既読が使えます。保存/既読は利用ブラウザの `localStorage` のみに記録されます（他のPCや端末には同期されません）。

ローカルWebサーバーを使う場合：

```bash
cd ai-release-radar
python3 -m http.server 8000
# http://localhost:8000 を開く
```

## 毎朝7時（日本時間）に自動更新する

**初期状態では自動更新は開始されていません。** Github Pagesに配置し、以下の設定を有効化すると GitHub Actions が毎日 07:00 JST を目標に公式ソースを収集・再配置します。GitHub Actionsのスケジュールには実行遅延があり得るため、7時ちょうどの更新は保証されません。

1. GitHubで新しいリポジトリを作り、展開した `ai-release-radar` フォルダの**中身**をそのリポジトリ直下にアップロードします。`.github/workflows/daily.yml` を含めてください。公開リポジトリはコード・監視条件・データが誰からでも見えるので、公開設定は慎重に選択してください。
2. リポジトリの **Settings → Pages → Build and deployment → Source → GitHub Actions** を選択します。
3. **Actions → Daily AI Release Radar → Run workflow** で初回手動実行。以後、cron `0 22 * * *`（UTC 22:00 = 日本時間翌日07:00）で日次実行されます。
4. Actionsが成功すると、Pages画面にサイトURLが表示されます。機能の変更がなくても確認済み日時が更新されます。取得に失敗したソースは「監視ソース」に警告表示されます。
5. 保存・既読は端末ごとに保持され、データ更新では消えません。

GitHub Pages上のサイトは一般公開され得ます。**個人情報・認証情報・社内データをデータファイルやコードに追記しないでください。** サイトを個人だけに限定したい場合、公開Pagesではなくローカル運用・アクセス制限付きホスティングを推奨します。

## 収集・評価のしくみ

| ソース | 自動で何を取得するか | 制約 |
|---|---|---|
| GitHub Releases：Codex / Claude Code / Gemini CLI / MCP仕様 / 公式MCP Servers / OpenBot | 公式リリース・変更点 | stableのみ。短期間のリリースを数件取得。GitHub APIには取得上限あり |
| OpenAI News RSS / Google Blog RSS | AI関連の公式発表記事 | 記事タイトルから簡易フィルタ。すべての製品リリースを網羅しない |
| OpenAI製品リリースノート / ChatGPTリリースノート / Anthropic News / Blender MCP / Antigravity Changelog / OpenBot Changelog | ページ本文の変更を検知 | **変更検知 ≠ リリース確定**。要確認として2点・別表示 |
| Orca / Cue / Hermes Agent | 未監視 | 確かな公式URLを指定する必要あり |

毎日取得できる各項目は**自動収集・機械評価**としてマークし、実際に確認した編集済み項目と区別しています。有用度は既知のユーザー用途（Mac/Windows、Codex、Claude Code、Antigravity、MCP、Blender、生成画像、AIエージェント、Git運用）に基づくヒューリスティックです。`score=5` は「作業に直結する可能性が高い」であり、性能や安全性の実験結果を意味しません。

重要度と具体的な試し方は、コード内の `evaluate()` と `personal_description()` で更新できます。個々の詳細を日本語で自然に要約したい場合は任意のOpenAI APIを利用できます（次節）。

### 日本語AI要約（任意・追加費用）

Actionsの **Settings → Secrets and variables → Actions → New repository secret** に `OPENAI_API_KEY` を登録すると、**新規自動収集**の情報について API 経由で日本語の概要・使い方・利用条件を生成します。APIキーはサイトに配置しません。

`RADAR_MODEL` はリポジトリ変数として別の対応モデルに変更可能です（未設定時は `gpt-6-luna` を試します）。**ChatGPT Plus/Claude Pro/Google AI ProのサブスクリプションにはOpenAI API利用料金は含まれません。** 別途請求が生じ、選択モデルのAPI利用権限も必要です。モデルが使えない場合はAI要約のエラーを警告に記録し、標準の機械評価テキストで掲載を継続します。

キーレスの場合もGitHub ReleasesやRSSからの収集は実行されますが、英語の原文から抽出したテキストが残ります（自動翻訳は保証しません）。自動収集結果に「公式確認済み」とは表示しません。

## 動作に関する注意

- Github Pages への **デプロイは未実施**です。リポジトリの作成・Pagesの有効化・公開先の設定は利用者が行う必要があります。
- GitHub Actionsの実行がない状態では、表示されるのは同梱データです。サイトを開くだけでは新しい情報をネットワークから検索しません。
- 初回のページ監視は比較用の本文ハッシュを記録するだけで、架空の「リリース」を作りません。
- Webサイトのレイアウト変更などで誤検知が起きる可能性があります。これは要確認として低優先度表示します。
- 公式ChangelogはHTML形式が変更され得るため、詳細情報を全自動で確実に解析するわけではありません。公式ページの変化を検知して、人が確認する設計です。
- GitHub Releasesに登場しないアプリ固有機能は自動取得で見落とすことがあります。ウォッチリストの監視や手動での編集済み記事追加が必要です。
- `data/releases.json` は編集しやすい普通のJSONです。追加/修正後 `python3 scripts/update.py --offline` を実行すると `data/releases.js` を同期できます。
- `scripts/seed.py` は初期データを再生成するスクリプトです。**運用開始後に実行すると収集履歴が消えます。**
- 日付は日本時間に正規化し、UI表示と週次フィルタは同梱データの最新日付が基準です（アーカイブを開いても表示が空にならないため）。

## ファイル構成

```text
ai-release-radar/
├── index.html                # ブラウザUI
├── assets/
│   ├── styles.css            # デザイン・スマホ対応
│   └── app.js                # 検索・絞り込み・保存・既読
├── data/
│   ├── releases.json         # 永続的なニュース履歴
│   ├── releases.js           # ブラウザ表示用データ（自動生成）
│   └── page_hashes.json      # 初回のオンライン実行時に作成
├── scripts/
│   ├── update.py             # 日次収集・暫定評価・重複除去
│   └── seed.py               # 開発時の初期データ
└── .github/workflows/daily.yml # 07:00 JSTの取得・Pages再公開
```

## 開発・検証

```bash
python3 scripts/update.py --offline
python3 -m unittest discover -s tests -v
```

`--offline` はネットワーク接続なしでデータとJavaScriptを再生成するだけです。実際の各公式サイトへの接続成功やGitHub Pagesの公開成功は、この配布ファイルでは検証していません。必要なAPIキーや接続先は常に公式サイトで確認してください。

## 作業記録

- 2026-10-30: `AI_Release_Radar_Site.zip` の全11ファイルを展開し、`.github/workflows/daily.yml` を含む初回コミットを準備。既存テスト5件とJavaScript構文検査に合格。GitHubの新規publicリポジトリ `masuda-dec/ai-release-radar` への登録対象とした。
