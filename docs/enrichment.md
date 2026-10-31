# 詳細解説と出典の仕様

概要は最大130字、本人への効果は最大100字を表示し、詳細はネイティブの`details/summary`で初期状態を閉じます。Enter/Space、フォーカス表示、`aria-controls`/`aria-expanded`、モバイルの1列表示に対応。保存・既読・検索は既存のまま利用でき、詳細本文も検索対象です。同一ページで保存・既読を操作した際は開閉状態と操作フォーカスを保ち、ページ再読込時は閉じます。

## 情報の境界と信頼度

| 区分 | 根拠 | 表示と制約 |
| --- | --- | --- |
| 公式リリース / ブログ / 公式PR | 提供元の一次資料 | 仕様の根拠。掲載日を記載。宣伝上の成果は本人の実績にしない |
| 編集済み詳細 `editorial` | 人手の資料照合 | 公式の事実と本人向けの提案を分離。本人環境の実測を意味しない |
| キーレス `rule` | 製品・タイトル・本文に対応する解説レシピ | 機械による使い方案。既知の製品/版の範囲に限定。性能・提供条件を推定しない |
| 任意AI `ai` | 取得した公式本文 | AI解説・未実測・要出典確認。AIが出典や投稿を作成することは禁止 |
| 利用者報告 `user_report` | 投稿日を確認できる公開投稿 | 個別環境の報告。公式仕様・修正後の再現・一般的効果を保証しない |
| 開発者検証 `developer_report` | Issue/PRのテスト記録 | OS・模擬環境・未検証箇所を明記 |
| 公式実演 `official_demo` | 製品のデモ | 独立した利用者の実例と混同しない |
| 自動検索候補 `verified: false` | 版が一致した投稿本文 | 関連機能・再現性は未確認。元のタイトル/短い抜粋で示す |

`verified: true`は公開投稿の本文・日付・関連性を編集時に確認したという意味です。その報告の正しさや本人環境での再現を実験した意味ではありません。

## スキーマと後方互換

`data/releases.json`のルートは`schemaVersion: 2`。既存の全IDと編集済み本文を保ち、`details`を追加します。正式な詳細スキーマは[details.schema.json](details.schema.json)。実行時にも必須項目・文字数・型を検査します。

- 既存項目: `id/date/product/title/summary/why/try/availability/sourceUrl/sourceName/status/reviewed/auto/channel/tags`。
- 取得情報: `sourceText`（公式本文、最大12,000文字）、`sourceExcerpt`（従来の短い原文）、GitHubは`sourcePublishedAt`（UTCの公開日時）も保持。本文は評価用データとして扱い、指示として実行しません。
- `details`: `schemaVersion/mode/inputHash/basis`と`change/before/after/workflow/benefit/environment/limitations/steps/commands/community`。
- `officialSources`は任意の追加公式出典リスト。各`url/title/publishedAt`。主出典は既存の`sourceUrl`と日付。
- `community`: `status/checkedAt/searches/sources`。各検索は`platform/status/query?/reason?`。投稿は`url/title/publishedAt/platform/kind/summary/relation/verified`、任意で`excerpt`。
- `enrichment`: その実行のAI試行数、コミュニティ検索対象数、それぞれの上限。

`config/detail-recipes.json`は機能ごとのキーレス解説。`productPattern`で別製品への誤適用を防ぎ、`titlePattern`で版指定やモデル発表をタイトルに限定します。本文末尾の旧版比較リンクを新しい版と混同しません。未知の更新は、取得原文と個別の検証タスクを表示し、旧版の挙動・プラン・コマンドが不明なことを明記します。

`data/editorial-details.json`は人手確認した差分とコミュニティ証拠の正本です。毎回適用するため、日次取得で消えません。既存のレビュー済み本文や保存IDは置き換えません。同じリリースの既存カードが複数ある場合も、保存IDを壊す削除はしません。

## 日次処理とフォールバック

1. 公式GitHub Releases/RSS/ページ監視を取得。既存IDの原文は更新するが、編集済み本文は保持。
2. 全履歴へキーレス詳細を付与し、編集済み差分を適用。
3. キーがあれば、最新の未AI化・自動取得分から上限件数だけ日本語AI解説を生成。キーなしは追加費用なし。AI出力は全検査完了後だけ反映し、失敗はルール詳細を維持して警告。投稿・出典・確認フラグはAIから受け取らない。
4. 最新の未調査または7日経過した項目から上限件数だけコミュニティを検索。編集済み調査は保護。
5. JSONと安全にエスケープしたJSを生成し、履歴をコミットしてPagesへ配置。

任意AIは1実行5件・最大20件、1件の出力上限3,500トークン、再試行なし。入力は公式本文最大12,000文字。`RADAR_AI_MAX_ITEMS=0`で無効。未処理の既存データも次回以降順次対象になります。件数・出力上限は費用の上限額ではなく、選択モデルと入力長により請求は変わります。旧本文のハッシュが変わったAI解説は再生成対象、安定したものはキャッシュを使用。

コミュニティは1実行5件・最大12件、1件あたりGitHub検索1回と任意X検索1回。GitHubは対応リポジトリと正確な版でIssueを検索し、取得本文の版一致を再確認します。関係のない古い不満を最新機能の反応へ流用しません。自動検索候補は手動確認済み投稿と分けます。Reddit/Hacker News/製品ブログは編集時に調査して採用し、日次の全自動巡回を保証しません。

Xは`X_BEARER_TOKEN`を設定した場合だけ公式APIのrecent searchを使用（APIのアクセス権・別料金が必要な場合あり）。未設定・403・レート制限は検索不可と表示します。検索成功で0件の場合と区別します。recent searchの期間外は網羅できません。認証の回避やログイン画面のスクレイピングは行いません。

`not_searched`=未検索、`unavailable`=検索不可、`not_found`=検索範囲で確認できた事例なし、`candidates`=未確認の投稿候補、`reviewed`=編集時に投稿を確認。いずれも投稿が存在しないという断定ではありません。

公式取得がすべて失敗した場合は終了コード1。一部成功は失敗元を表示して公開継続。AIやコミュニティの失敗だけで公式の成功まで失敗扱いにしません。`--offline`は通信も有料APIも呼ばず、ローカルデータから詳細・JSを再生成。`--no-ai`と`--no-community`で任意処理を個別停止できます。

## 設定と検証

Actions Secrets: `OPENAI_API_KEY`（任意）、`X_BEARER_TOKEN`（任意）。`GITHUB_TOKEN`はActionsが提供。キーをブラウザーや公開ファイルへ出力しません。
Actions Variables: `RADAR_MODEL`（既存の`gpt-6-luna`を維持）、`RADAR_AI_MAX_ITEMS`、`RADAR_COMMUNITY_MAX_ITEMS`。アプリの月額プランとAPI課金は別です。

```sh
python3 -B scripts/update.py --offline
python3 -B -m unittest discover -s tests -v
node --check assets/app.js
node --check data/releases.js
# 公開ソースの取得だけを実機確認する場合
python3 -B scripts/update.py --no-ai --no-community
```

本改修のAPI仕様は[OpenAI公式Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)で確認。`response_format`のJSONモード、出力上限、独自検証を使用。実キーを使うAI生成は本改修のローカル検証では未実施です。
