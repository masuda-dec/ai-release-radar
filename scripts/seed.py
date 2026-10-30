import json
from pathlib import Path
from datetime import datetime, timezone
D=Path(__file__).resolve().parents[1]/'data'

def entry(id,date,product,category,title,score,summary,why,tryit,availability,url,**kwargs):
    return {'id':id,'date':date,'product':product,'category':category,'title':title,'score':score,'summary':summary,'why':why,'try':tryit,'availability':availability,'sourceUrl':url,'sourceName':kwargs.get('sourceName','公式リリースノート'),'status':'公式確認済み','reviewed':True,'channel':kwargs.get('channel','stable'),'tags':kwargs.get('tags',[]),'auto':False}

items=[
entry('claude-2-1-314','2026-10-30','Claude Code','開発・CLI','Claude Code 2.1.314：作業領域の外への書き込みを禁止',5,'permissions.blockWritesOutsideWorkingDirectories を追加。許可モードにかかわらず作業ディレクトリ外への書き込みを拒否できます。','AI専用Windows環境やMacでエージェントに広い権限を与える際、意図しないファイル変更を防ぐ設定として重要です。','まずテスト用リポジトリで設定を確認し、保護対象外の編集が本当に拒否されるか試してください。','Claude ProでのClaude Code利用を想定。実際の設定キーと対応バージョンを公式ノートで確認。','https://github.com/anthropics/claude-code/releases/tag/v2.1.314',tags=['安全性','Claude Pro','Windows','Mac']),
entry('codex-0-166','2026-10-29','Codex','開発・CLI','Codex 0.166.0：通信診断とセッション再開を改善',5,'codex doctor --network-only による接続診断、codex queue --resume、Terraモデル一覧への追加など。','Mac/Windowsでの認証・ネットワーク・MCP連携のトラブル切り分けと、長い開発セッションの再開に役立ちます。','CLIのバージョンを確認後、ネットワーク診断コマンドを使い、Codexの設定問題を切り分けてください。','Codex CLI。提供状況やモデル選択は使用中のChatGPTプラン・環境に依存。','https://github.com/openai/codex/releases/tag/rust-v0.166.0',tags=['診断','セッション','Mac','Windows']),
entry('claude-2-1-312','2026-10-28','Claude Code','開発・CLI','Claude Code 2.1.312：大きなCLAUDE.mdの破損リスクを低減',5,'途中までしか読み込んでいない大容量のCLAUDE.mdやルールファイルを上書きする問題を修正。','AIエージェントのルールを重視する運用で特に有用。リポジトリの指示ファイルを守る改善です。','CLAUDE.mdを管理するリポジトリのGit差分を確認し、更新版で編集の挙動を検証してください。','Claude Codeの更新が必要。Claude Pro契約でもCLIでの利用条件は確認。','https://github.com/anthropics/claude-code/releases/tag/v2.1.312',tags=['安全性','ルール','Claude Pro']),
entry('openai-terra','2026-10-26','OpenAI / Codex','モデル・エージェント','GPT-6.1 Terra がChatGPT WorkとCodexに登場',5,'視覚的推論・コンピューター操作・文章作成に対応。WorkとCodexで段階的に展開し、APIでも別途提供。','Codex DesktopやWorkでの実装、PC操作、自動調査といった現在の主要用途に直接関係します。','WorkまたはCodexのモデル一覧でTerraを確認し、同じ実装タスクを従来モデルと比較してください。','ChatGPT Plusは提供対象だが順次展開。Chatタブでは利用不可。API料金はサブスクと別。','https://openai.com/products/release-notes/',tags=['ChatGPT Plus','Codex','Work','モデル']),
entry('mcp-servers-2-1','2026-10-25','MCP','連携・自動化','公式MCP Servers 2.1.0：セキュリティ修正',4,'Model Context Protocol公式サーバーのリリースでセキュリティ修正が案内されています。','Blender MCPやその他の連携サーバーを安全に運用する際、バージョン固定・アップデート判断の参考になります。','利用しているMCPサーバーが該当パッケージかを確認し、変更点を読んでから段階的に更新してください。','対象となるサーバーを使っている場合のみ。全MCP実装への一律適用ではありません。','https://github.com/modelcontextprotocol/servers/releases/tag/v2.1.0',tags=['MCP','安全性']),
entry('anthropic-agent-skills','2026-10-22','Anthropic / Agent Skills','連携・自動化','Agent SkillsをAgentic AI Foundationへ寄贈',4,'AnthropicがAgent Skills仕様を財団に寄贈すると発表。複数のエージェント基盤で採用されています。','Claude CodeだけでなくCodexや他のAIでも再利用できるスキル設計を目指す際に重要です。','今あるスキルの構造・説明・権限前提を棚卸しし、特定のクライアントに依存する部分を分離してください。','仕様の進化に関する発表。新しいコマンドが直ちに使えることを意味しません。','https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation',tags=['Skills','標準化','Codex','Claude Code']),
entry('claude-2-1-309','2026-10-22','Claude Code','開発・CLI','Claude Code 2.1.309：macOSサンドボックス保護を修正',5,'macOS/Linuxでシェル起動ファイルがサンドボックス外で実行される問題や、MCP設定ファイルの変更を防ぐ修正を含みます。','以前検討した「安全に権限を任せる」エージェント実行環境に関係が深く、優先度の高い安全性修正です。','Mac側でClaude Codeのバージョンを確認し、実行権限・MCP設定の保護動作を検証してください。','Claude Codeの該当バージョン以降を利用する環境向け。','https://github.com/anthropics/claude-code/releases/tag/v2.1.309',tags=['安全性','MCP','Mac']),
entry('gemini-preview-0-67','2026-10-27','Gemini CLI','開発・CLI','Gemini CLI 0.67.0-preview：モデル一覧とコンテナ連携',3,'CLI内でのモデル探索コマンド、コンテナサンドボックスとIDEの連携、キャンセル処理の改善など。','WindowsのAI専用環境やCLI比較で役立つ可能性があります。ただしAntigravity CLIとは別製品として扱います。','本番利用はstableを優先し、Previewを別環境で試す場合はモデル一覧とIDE連携を確認してください。','プレビュー版。Google AI Proからの利用条件は認証方式・製品ごとに確認。','https://github.com/google-gemini/gemini-cli/releases/tag/v0.67.0-preview.0',channel='preview',tags=['Preview','CLI','Windows']),
entry('openai-slides','2026-10-16','ChatGPT Slides','制作・画像','ChatGPTでスライド作成・共同編集',2,'Web/Desktopでスライドの作成、編集、共同作業、PowerPointなどへのエクスポートが可能に。','電子工作部向けの発表資料作成には魅力的ですが、現時点のPlusプランでは利用対象に含まれていません。','今はHTMLスライドのワークフローを継続し、Plusへの対応拡大を監視してください。','公式案内の初期対象はSpaceにアクセス可能なPro・Business・Enterprise。Plusは対象外。','https://help.openai.com/en/articles/6825453-chatgpt-release-notes',tags=['スライド','Plus対象外']),
entry('gemini-argon','2026-10-14','Gemini / Antigravity','モデル・エージェント','Gemini 4 Argon：MacアプリからAntigravityを操作',5,'Gemini 4 Argonが提供開始。macOSのGeminiアプリからAntigravityのエージェント型コーディング機能へアクセス可能になりました。','普段のMacでGemini・Antigravityを使う導線が短くなり、調査から実装への切り替えに役立ちます。','MacのGeminiアプリで提供状況を確認し、小さな検証用プロジェクトからチャット→コーディングを試してください。','Google AI Pro・Ultraが対象。段階的な提供・環境差異の可能性があります。','https://blog.google/intl/ja-jp/company-news/technology/gemini-4-argon-gemini/',tags=['Google AI Pro','Antigravity','Mac']),
entry('chatgpt-gpt6','2026-10-07','ChatGPT','モデル・エージェント','GPT-6と操作可能なインターフェース',4,'ChatGPTでGPT-6を導入し、画像・比較・操作できるUIを組み合わせた回答形式へ。','ツール比較や設計判断をチャット内で見やすく扱えるため、情報整理・実装計画に有用です。','候補ツールの比較を頼み、機能・コスト・プラン制限を一画面で評価してみてください。','ChatGPT Plusは対象。Work/Codexのモデル更新とは別の発表です。','https://help.openai.com/en/articles/6825453-chatgpt-release-notes',tags=['ChatGPT Plus','比較','UI']),
entry('claude-haiku','2026-10-07','Claude','モデル・エージェント','Claude Haiku 5.5：高速な小型モデル',3,'AnthropicがHaiku 5.5を発表。高頻度の要約やサブエージェント、ブラウザー利用などを想定。','大量の記事の一次分類やエージェントの軽作業に使える可能性があります。','使うツールでモデル選択が可能か確認し、記事分類や簡単なコードレビューに試してください。','Claude ProのチャットとAPI、各ツールでの利用可否は個別確認が必要。','https://www.anthropic.com/news',tags=['軽量モデル','エージェント']),
]
sourcechecks=[
{'name':'Codex CLI','url':'https://github.com/openai/codex/releases','method':'GitHub Releases','automatic':True},
{'name':'Claude Code','url':'https://github.com/anthropics/claude-code/releases','method':'GitHub Releases','automatic':True},
{'name':'Gemini CLI（Antigravityとは別）','url':'https://github.com/google-gemini/gemini-cli/releases','method':'GitHub Releases','automatic':True},
{'name':'MCP 仕様','url':'https://github.com/modelcontextprotocol/modelcontextprotocol/releases','method':'GitHub Releases','automatic':True},
{'name':'公式MCP Servers','url':'https://github.com/modelcontextprotocol/servers/releases','method':'GitHub Releases','automatic':True},
{'name':'OpenAI ニュース','url':'https://openai.com/news/rss.xml','method':'公式RSS','automatic':True},
{'name':'Google 公式ブログ','url':'https://blog.google/rss/','method':'公式RSS（AI関連抽出）','automatic':True},
{'name':'OpenAI 製品リリースノート','url':'https://openai.com/products/release-notes/','method':'ページ変更の検知（個別更新は要確認）','automatic':True},
{'name':'ChatGPT リリースノート','url':'https://help.openai.com/en/articles/6825453-chatgpt-release-notes','method':'ページ変更の検知（個別更新は要確認）','automatic':True},
{'name':'Anthropic ニュース','url':'https://www.anthropic.com/news','method':'ページ変更の検知（個別更新は要確認）','automatic':True},
{'name':'Blender MCP','url':'https://www.blender.org/lab/mcp-server/','method':'ページ変更の検知（個別更新は要確認）','automatic':True},
{'name':'Orca / Cue・OpenBot・Hermes','url':'','method':'公式情報のURL登録待ち（未監視）','automatic':False},
]
base={'generatedAt':'2026-10-30T13:00:00Z','note':'初期掲載は2026-10-30時点の公式ソースに基づく編集済み情報。GitHub Actionsを有効化すると自動収集が始まります。','items':items,'checks':sourcechecks,'failures':[]}
(D/'releases.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'releases.js').write_text('window.RADAR_DATA = '+json.dumps(base,ensure_ascii=False, separators=(',',':'))+';\n',encoding='utf-8')
print('seeded',len(items))
