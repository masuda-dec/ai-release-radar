"""Evidence-separated, keyless explanations. No network or model needed to render."""
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

VERSION = 1
ROOT = Path(__file__).resolve().parents[1]
TEXT_FIELDS = ('change', 'before', 'after', 'workflow', 'benefit', 'environment', 'limitations')
FEATURE_CHECKS = (
    (r'\bsandbox\b|\bpermissions?\b|onFailure|\bcredentials?\b|\bauthentication\b',
     '空の検証フォルダで、許可した操作と確認・拒否されるべき操作を一つずつ実行し、ダイアログと実行結果を比較する'),
    (r'\bmcp\b|\bconnectors?\b',
     '読み取り専用のテスト用コネクターを一つ接続し、最初のターンと再接続後に同じツールが使えるかを確認する'),
    (r'\bsession\b|\bresume\b|\bworktree\b',
     '検証用リポジトリで作業を中断・再開し、作業フォルダと直前の依頼が保持されるかを確認する'),
)

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

def fingerprint(item):
    return hashlib.sha256((item.get('title','')+'\n'+item.get('sourceText',item.get('sourceExcerpt',item.get('summary','')))).encode()).hexdigest()[:20]

def safe_url(url):
    p = urlparse(str(url))
    return p.scheme == 'https' and bool(p.hostname) and not p.username and not p.password

def validate_details(d):
    if not isinstance(d,dict) or d.get('schemaVersion') != VERSION:
        raise ValueError('詳細スキーマのバージョンが不正です')
    for k in TEXT_FIELDS:
        if not isinstance(d.get(k),str) or not 5 <= len(d[k]) <= 1400:
            raise ValueError('詳細の必須文字列が不正: '+k)
    if not isinstance(d.get('steps'),list) or not 1 <= len(d['steps']) <= 8 or any(not isinstance(x,str) or not 5 <= len(x) <= 900 for x in d['steps']):
        raise ValueError('手順が不正です')
    if not isinstance(d.get('commands'),list) or len(d['commands']) > 5:
        raise ValueError('コマンドが不正です')
    for c in d['commands']:
        if not isinstance(c,dict) or any(not isinstance(c.get(k),str) or not 1 <= len(c[k]) <= 1800 for k in ('label','platform','command')):
            raise ValueError('コマンドの形式が不正です')
    return d

def empty_community():
    return {'status':'not_searched','checkedAt':None,'searches':[], 'sources':[]}

def build_details(item):
    old = item.get('details',{})
    if old.get('schemaVersion') == VERSION and old.get('mode') in ('editorial','ai') and old.get('inputHash') == fingerprint(item):
        return old
    product = item.get('product','この製品')
    title = item.get('title','この更新')
    text = item.get('sourceText') or item.get('sourceExcerpt') or item.get('summary','')
    recipes = json.loads((ROOT/'config/detail-recipes.json').read_text())
    match = next((r for r in recipes if re.search(r.get('productPattern','.'), product+' '+title, re.I) and re.search(r.get('titlePattern','.'),title,re.I) and re.search(r['pattern'], title+' '+text, re.I)),None)
    task = next((task for pattern,task in [
        (r'Codex|Claude Code|Gemini CLI','このサイトの更新スクリプトを複製し、1件のデータ追加と差分レビューを依頼する'),
        (r'Blender|MCP','Blenderのテストシーンに接続し、オブジェクト一覧の取得だけを依頼する'),
        (r'OpenBot|Antigravity','AI作業用PCのテストフォルダで、画像素材一覧の作成からSNS投稿下書きの保存までを依頼する'),
        (r'画像|image|Sora|banana','同じキャラクター参照からLINEスタンプ候補を3枚作り、顔・文字・透過処理を比較する'),
        (r'スライド|presentation|document|PDF','公開情報だけで5枚の発表資料を作り、日本語の改行と書き出し後の編集可否を確かめる'),
    ] if re.search(pattern,product+' '+title,re.I)), '公開記事3件からSNS投稿の下書きと出典表を作り、事実と提案が混ざらないか確かめる')
    if item.get('auto'):
        task = next((check for pattern, check in FEATURE_CHECKS
                     if re.search(pattern, item.get('sourceExcerpt') or text, re.I)), task)
    d = {
        'schemaVersion':VERSION,'mode':'rule','inputHash':fingerprint(item),
        'basis':'公式原文からの抽出とルールによる試し方案。実測結果ではありません。',
        'change':item.get('summary') or '公式本文の取得情報が不足しています。',
        'before':'旧版の具体的な挙動は取得した本文だけでは確認できません。比較結果は未確認です。',
        'after':'「'+title+'」で案内された範囲が対象です。機能・提供条件は下の公式出典で照合してください。',
        'workflow':task+'。対象は「'+title+'」。この更新が必要な操作に影響するかを切り分けるための提案です。',
        'steps':['現在の製品名・バージョン・ログイン方法を控え、公開データを使うテスト用フォルダを用意する。',
                 task+'。同じ入力・同じ依頼を保存する。',
                 '公式ノートの対象バージョンに切り替え、同じ依頼を再実行する。成功可否・手直し回数・出力差分を記録する。'],
        'commands':[],
        'benefit':'この作業で再現した場合に限り、やり直しや手動確認が減る可能性があります。速度・品質の改善率は測定していません。',
        'environment':item.get('availability') or '対応プラン・OSは本文から確認できません。Mac M2とWindows 11 Homeそれぞれで利用可否を確認してください。',
        'limitations':'ChatGPT Plus / Claude Pro / Google AI Proの契約からAPI利用権や他製品の機能を推定しません。CLI・アプリ・Webの提供差に注意してください。',
        'community':copy.deepcopy(old.get('community',empty_community()))
    }
    if match:
        d.update({k:copy.deepcopy(v) for k,v in match.items() if k not in ('pattern','titlePattern','productPattern','name','commands')})
        d['recipe'] = match['name']
        d['commands'] = copy.deepcopy(match.get('commands',[]))
        d['basis']='公式本文のキーワードに対応する解説・試し方案。改善量は未実測です。'
    if item.get('status') == '要確認':
        d.update(change='公式ページの本文ハッシュが変化しました。リリースを確認したものではありません。',before='以前の本文ハッシュを保存していました。',after='本文の差分内容・公開日・新機能は未確認です。',workflow='Antigravity等の公式Changelogを開き、記載された日付とバージョンを確認する。リリースが確認できるまでは導入判断を保留します。',steps=['公式出典の最新日付とバージョンを読む。','新機能・不具合修正・レイアウト変更のどれかを見分け、リリース本文があれば編集済み情報を追加する。'],commands=[],benefit='ページの変更を見落としにくくします。新機能が使えることの証明にはなりません。')
    return validate_details(d)

def ensure_details(item):
    item['details'] = build_details(item)
    d=item['details']
    if item.get('auto') and not item.get('reviewed') and d.get('recipe') and d.get('mode')=='rule':
        item['summary']=d['change'][:130]
        item['why']=d['benefit']
        item['try']=d['workflow']
    return item
