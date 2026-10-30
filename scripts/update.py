#!/usr/bin/env python3
"""AI Release Radar: collect official sources, rate for a known workflow, publish JSON/JS.
Requires only Python's standard library. OPENAI_API_KEY is optional and costs API credits.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
TOKYO=ZoneInfo('Asia/Tokyo')
GITHUB_SOURCES=[
    ('Codex', 'openai/codex', '開発・CLI',5),
    ('Claude Code','anthropics/claude-code','開発・CLI',5),
    ('Gemini CLI','google-gemini/gemini-cli','開発・CLI',3),
    ('MCP 仕様','modelcontextprotocol/modelcontextprotocol','連携・自動化',4),
    ('MCP Servers','modelcontextprotocol/servers','連携・自動化',4),
    ('OpenBot','nightly-labs/openbot','連携・自動化',5),
]
RSS_SOURCES=[
    ('OpenAI ニュース','https://openai.com/news/rss.xml','モデル・エージェント',4),
    ('Google 公式ブログ','https://blog.google/rss/','モデル・エージェント',4),
]
WATCH_SOURCES=[
    ('OpenAI 製品リリースノート','https://openai.com/products/release-notes/'),
    ('ChatGPT リリースノート','https://help.openai.com/en/articles/6825453-chatgpt-release-notes'),
    ('Anthropic ニュース','https://www.anthropic.com/news'),
    ('Blender MCP','https://www.blender.org/lab/mcp-server/'),
    ('Antigravity 公式 Changelog','https://antigravity.google/docs/changelog'),
    ('OpenBot Changelog','https://openbot.run/changelog'),
]
RELEASE_WORDS=('gemini','antigravity','nano banana','claude','codex','gpt-','gpt ','openai','imagegen','images','agent','mcp','ai pro','model','blender','sora','workspace','computer use','image generation','生成ai','生成 ai')
BOOST_WORDS=('security','sandbox','permission','safe','protect','fix','fixes','mcp','agent','model','windows','macos','cli','computer','integration','skills','session','resume','auth')
JST_NOW=lambda: datetime.now(TOKYO)

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.out=[];self.block=0;self.in_main=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript','svg'):
            self.block+=1
        if not self.block and tag in ('p','li','h1','h2','h3','h4','div','article','br'):
            self.out.append(' ')
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript','svg'):
            self.block=max(0,self.block-1)
    def handle_data(self,data):
        if not self.block:self.out.append(data)

def clean_html(text):
    p=TextParser();p.feed(str(text or ''));return re.sub(r'\s+',' ',' '.join(p.out)).strip()

def request(url, accept='application/json', token=None):
    headers={'User-Agent':'AI-Release-Radar/1.0 (daily changelog monitor)','Accept':accept}
    if token:headers['Authorization']='Bearer '+token
    req=Request(url,headers=headers)
    with urlopen(req,timeout=25) as r:
        return r.read(2_000_000).decode('utf-8','replace')

def jst_date(d):
    if not d:return JST_NOW().date().isoformat()
    try:
        if isinstance(d,datetime): parsed=d
        else: parsed=datetime.fromisoformat(str(d).replace('Z','+00:00'))
        if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(TOKYO).date().isoformat()
    except Exception:
        try:return parsedate_to_datetime(str(d)).astimezone(TOKYO).date().isoformat()
        except Exception:return JST_NOW().date().isoformat()

def markdown_bullets(body):
    lines=[]
    for raw in (body or '').splitlines():
        s=re.sub(r'^\s*[-*+]\s+','',raw).strip()
        s=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',s)
        s=re.sub(r'`([^`]+)`',r'\1',s)
        s=re.sub(r'\s+',' ',s).strip(' #*-')
        if not s or len(s)<28 or s.lower().startswith(('full changelog','changelog','compare','contributors','what\'s changed','assets','release v')):continue
        if re.search(r'\(#\d+\)',s) and len(s)<35:continue
        lines.append(s)
    priority=sorted(enumerate(lines),key=lambda x:(-sum(w in x[1].lower() for w in BOOST_WORDS),x[0]))
    selected=[s for _,s in priority[:2]]
    return ' / '.join(selected)[:440] or 'リリースが公開されました。具体的な変更内容は公式リリースノートで確認してください。'

def evaluate(product,category,base,content,channel='stable'):
    t=content.lower()
    score=base
    if any(w in t for w in ('sandbox','permission','security','protect','vulnerability','unsafe','credential','authentication')):score+=1
    if any(w in t for w in ('agent','mcp','model','computer use','workflow','integration','remote','windows','macos')):score+=1
    if re.search(r'\b(docs?|typo|chore|minor)\b',t) and not any(w in t for w in ('fix','feature','security')):score-=2
    if channel!='stable':score-=1
    return max(1,min(5,score))

def personal_description(product,summary,channel='stable'):
    s=summary.lower()
    if 'sandbox' in s or 'permission' in s or 'security' in s or 'protect' in s:
        return ('MacとWindowsのAIエージェントに作業を委任する際の安全性に関わるため、優先して確認する価値があります。',
                '検証用リポジトリで現在の設定をバックアップし、権限・サンドボックス動作を更新前後で比較してください。')
    if product in ('Codex','Claude Code'):
        return ('現在使っているコーディングエージェントの操作性・信頼性に関わる更新です。MCPやCLIと組み合わせた作業への影響を確認できます。',
                '更新版のCLIを検証環境で試し、既存のスキル・設定・MCP接続に影響がないか確認してください。')
    if product=='Gemini CLI':
        return ('Google系CLIの進化を比較できます。ただしGemini CLIとAntigravityは同じ製品ではありません。',
                '安定版かプレビュー版かを確かめ、別のテスト環境で既存のCLIと機能差を比較してください。')
    if product=='OpenBot':
        return ('WindowsのAI専用PCでOpenBotとCodex/Claude/Geminiを動かす構成に影響する可能性が高い更新です。',
                '必ず重要な作業フォルダをバックアップし、公式ノートで更新手順と互換性を確認してください。')
    if product.startswith('MCP'):
        return ('Blender MCPやAIツール連携の基盤に関わる可能性があります。利用中のサーバーへの影響確認が必要です。',
                '利用中のMCPサーバーと仕様バージョンを確認し、互換性・認証・安全性を検証してください。')
    return ('AIエージェント・画像生成・開発・制作への応用が考えられますが、環境とプランで利用可否が異なります。',
            '公式ページで利用プランと提供地域を確認し、現在の作業から小さな検証タスクを一つ選んでください。')

def make_item(key,date,product,category,title,content,url,score,channel='stable',status='自動収集',source='公式ソース'):
    why,how=personal_description(product,content,channel)
    available='プラン・地域・アプリ/CLIの対応条件は公式ページで確認が必要です。'
    if channel!='stable':available='プレリリースです。安定版とは異なり不具合が含まれる可能性があります。'
    return {'id':key,'date':date,'product':product,'category':category,'title':title,'score':score,'summary':content[:480],
      'why':why,'try':how,'availability':available,'sourceUrl':url,'sourceName':source,
      'status':status,'reviewed':False,'channel':channel,'tags':[product,'自動収集'],'auto':True}

def gather_github(name,repo,category,score):
    raw=request('https://api.github.com/repos/'+repo+'/releases?per_page=30', token=os.environ.get('GITHUB_TOKEN'))
    releases=json.loads(raw)
    if not isinstance(releases,list):raise ValueError('GitHubのレスポンスが想定外です')
    out=[]
    for r in releases:
        if r.get('draft') or r.get('prerelease'):continue
        tag=r.get('tag_name') or ''
        if not tag:continue
        when=jst_date(r.get('published_at') or r.get('created_at'))
        if when<(JST_NOW()-timedelta(days=21)).date().isoformat():continue
        summary=markdown_bullets(r.get('body',''))
        score_now=evaluate(name,category,score,summary)
        out.append(make_item('gh:'+repo+':'+tag,when,name,category,
            f'{name} {tag}：公式リリース',summary,r.get('html_url') or 'https://github.com/'+repo+'/releases',score_now,source='GitHub Releases'))
        if len(out)>=4:break
    return out

def parse_feed(xml):
    root=ET.fromstring(xml)
    found=[]
    for entry in root.findall('.//item'):
        title=clean_html(entry.findtext('title',''))
        url=entry.findtext('link','')
        date=entry.findtext('pubDate') or entry.findtext('date') or ''
        desc=clean_html(entry.findtext('description') or '')
        found.append((title,url,jst_date(date),desc))
    if found:return found
    ns='{http://www.w3.org/2005/Atom}'
    for entry in root.findall('.//'+ns+'entry'):
        title=clean_html(entry.findtext(ns+'title',''))
        url=next((el.attrib.get('href') for el in entry.findall(ns+'link') if el.attrib.get('rel','alternate')=='alternate'),'')
        date=entry.findtext(ns+'published') or entry.findtext(ns+'updated')
        desc=clean_html(entry.findtext(ns+'summary',''))
        found.append((title,url,jst_date(date),desc))
    return found

def gather_rss(name,url,category,base):
    entries=parse_feed(request(url,'application/rss+xml, application/atom+xml, application/xml, text/xml'))
    out=[]
    for title,link,date,desc in entries:
        if not link.startswith('https://'):continue
        # Prefer actual AI product launches to unrelated company announcements.
        specific=('gemini','antigravity','nano banana','claude','codex','gpt-','gpt ','image generation','mcp','blender','sora','agents','agentic','ai model','ai studio')
        if not any(k in title.lower() for k in specific):continue
        if date<(JST_NOW()-timedelta(days=21)).date().isoformat():continue
        content=desc[:410] if desc else '公式の発表記事です。具体的な変更点と提供条件は出典で確認してください。'
        score=evaluate(name,category,base,title+' '+content)
        uid='rss:'+hashlib.sha256(link.encode()).hexdigest()[:18]
        out.append(make_item(uid,date,name,category,title,content,link,score,source=name+' RSS'))
        if len(out)>=7:break
    return out

def monitor_page(name,url,oldhashes,newhashes):
    body=request(url,'text/html,application/xhtml+xml')
    plain=clean_html(body)
    if len(plain)<300:raise ValueError('本文が短く、ページ解析に失敗した可能性があります')
    sig=hashlib.sha256(plain[:20000].encode('utf-8')).hexdigest()
    previous=oldhashes.get(url)
    newhashes[url]=sig
    if not previous or previous==sig:return []
    today=JST_NOW().date().isoformat()
    item=make_item('watch:'+hashlib.sha256((url+sig).encode()).hexdigest()[:18],today,name,'連携・自動化',
        f'公式ページに変更を検知：{name}', '公開ページの本文が前回取得時と変わりました。新しいリリースとは限りません。内容の確認が必要です。',url,2,status='要確認',source='公式ページ監視')
    item['why']='普段使っているツールに変更があった可能性があります。ただし内容は未確認なので導入判断は保留してください。'
    item['try']='リンク先で新着日付と変更点を確認してください。重要な場合は手動で編集済みの情報に更新します。'
    item['availability']='更新検知のみ。新機能やプラン対応は確認できていません。'
    item['tags']=['要確認','変更監視']
    return [item]

def ai_enrich(item):
    """Optional. Never treat model-generated text as official verification."""
    key=os.environ.get('OPENAI_API_KEY')
    if not key:return item
    payload={'model':os.environ.get('RADAR_MODEL','gpt-6-luna'),'messages':[
      {'role':'system','content':('あなたはAI開発ツールの日本語リリース解説編集者。次の事実にない機能やプラン対応を断定しない。'
       'ユーザーはMac M2,Windows11,ChatGPT Plus,Claude Pro,Google AI Proを利用し、Codex,Claude Code,Antigravity,MCP,Blender,画像生成に興味がある。'
       '以下のキーを持つJSONだけ返す: summary,why,try,availability。各キー日本語で1〜2文。提供条件が不明なら不明と明記。')},
      {'role':'user','content':json.dumps({k:item[k] for k in ('product','title','summary','sourceUrl','channel')},ensure_ascii=False)}
    ],'response_format':{'type':'json_object'}}
    req=Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),
      headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'AI-Release-Radar/1.0'},method='POST')
    with urlopen(req,timeout=45) as r: obj=json.load(r)
    result=json.loads(obj['choices'][0]['message']['content'])
    for k in ('summary','why','try','availability'):
        if isinstance(result.get(k),str) and len(result[k])>=5:item[k]=result[k][:520]
    item['tags']=['AI要約','要出典確認']+item.get('tags',[])[:2]
    return item

def same_release(new,existing):
    if new['id'] in {i.get('id') for i in existing}:return True
    if new['id'].startswith('gh:'):
        # Initial curated entries have independent ids; avoid duplicating the exact version.
        tag=new['title'].split(' ',1)[-1].split('：',1)[0].strip().replace('rust-v','').replace('v','',1)
        for item in existing:
            if item.get('date')==new['date'] and (item.get('product')==new['product'] or (new['product']=='Codex' and 'Codex' in item.get('product',''))) and tag in item.get('title',''):
                return True
    return False

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true',help='validate and rebuild JS from local data without fetching')
    args=parser.parse_args()
    old=json.loads((DATA/'releases.json').read_text(encoding='utf-8'))
    items=old.get('items',[])
    failures=[]
    added=0
    if not args.offline:
        sources=[(f'GitHub: {name}',lambda n=name,r=repo,c=category,s=score:gather_github(n,r,c,s)) for name,repo,category,score in GITHUB_SOURCES]
        sources += [(f'RSS: {name}',lambda n=name,u=url,c=category,s=score:gather_rss(n,u,c,s)) for name,url,category,score in RSS_SOURCES]
        hashes_path=DATA/'page_hashes.json'
        old_hashes=json.loads(hashes_path.read_text()) if hashes_path.exists() else {}
        new_hashes=dict(old_hashes)
        sources += [(f'監視: {name}',lambda n=name,u=url:monitor_page(n,u,old_hashes,new_hashes)) for name,url in WATCH_SOURCES]
        for source,call in sources:
            try:
                updates=call()
                for item in updates:
                    if same_release(item,items):continue
                    if item['status']!='要確認':
                        try:ai_enrich(item)
                        except Exception as e:
                            failures.append({'source':'AI要約 '+source,'message':str(e)[:130]})
                    items.append(item);added+=1
                print(f'{source}: {len(updates)} 件検知',flush=True)
            except Exception as e:
                failures.append({'source':source,'message':str(e)[:160]})
                print(f'ERROR {source}: {e}',file=sys.stderr,flush=True)
        hashes_path.write_text(json.dumps(new_hashes,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Preserve all manually reviewed items, cap automatically collected history to 300 entries.
    curated=[i for i in items if not i.get('auto')]
    auto=sorted((i for i in items if i.get('auto')),key=lambda x:x.get('date',''),reverse=True)[:300]
    items=sorted(curated+auto,key=lambda x:(x.get('date',''),x.get('score',0)),reverse=True)
    old['items']=items
    old['failures']=failures if not args.offline else old.get('failures',[])
    if not args.offline:
        old['generatedAt']=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
        old['note']='公式ソースを毎日確認。自動取得・機械評価と編集済み情報は明確に区別しています。プラン/利用条件は必ず出典を確認してください。'
    (DATA/'releases.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DATA/'releases.js').write_text('window.RADAR_DATA = '+json.dumps(old,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    print(f'added={added} total={len(items)} errors={len(failures)}')
    return 0 if args.offline or len(failures)<len(GITHUB_SOURCES)+len(RSS_SOURCES)+len(WATCH_SOURCES) else 1

if __name__=='__main__':sys.exit(main())
