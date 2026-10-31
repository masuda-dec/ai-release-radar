"""Bounded public searches. Reports are evidence candidates, never official facts."""
import re
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta
from details import empty_community, safe_url, now

REPOS = {'Codex':'openai/codex','Claude Code':'anthropics/claude-code','Gemini CLI':'google-gemini/gemini-cli','OpenBot':'nightly-labs/openbot','MCP Servers':'modelcontextprotocol/servers'}

def collect(item, request, token=None, x_token=None):
    result=empty_community();result['checkedAt']=now()
    repo=REPOS.get(item.get('product'))
    version=re.search(r'(?<!\d)\d+\.\d+\.\d+(?!\d)',item.get('title',''))
    if repo and version:
        query=f'repo:{repo} is:issue "{version[0]}"'
        search={'platform':'GitHub','query':query,'status':'not_found'}
        try:
            import json
            obj=json.loads(request('https://api.github.com/search/issues?'+urlencode({'q':query,'per_page':5,'sort':'updated'}),token=token))
            if not isinstance(obj.get('items'),list):raise ValueError('GitHub検索形式が不正')
            for issue in obj['items']:
                body=issue.get('body') or ''
                # Search engines can match comments; only accept a version present in fetched text.
                if version[0] not in issue.get('title','')+' '+body:continue
                if not safe_url(issue.get('html_url','')) or not issue.get('created_at'):continue
                result['sources'].append({'url':issue['html_url'],'title':issue['title'][:200],
                    'publishedAt':issue['created_at'],'platform':'GitHub','kind':'user_report',
                    'relation':'同じバージョンへの言及。機能別の関連性・再現性は未確認。',
                    'summary':'利用者の投稿（原文タイトル）：'+issue['title'][:200],
                    'excerpt':re.sub(r'\s+',' ',body)[:240], 'verified':False})
            search['status']='found' if result['sources'] else 'not_found'
        except Exception as e:search.update(status='unavailable',reason=type(e).__name__)
        result['searches'].append(search)
    else:result['searches'].append({'platform':'GitHub','status':'not_applicable','reason':'対象リポジトリまたは正確な版が未特定'})
    if x_token and version:
        search={'platform':'X','status':'not_found','query':f'"{item.get("product","")}" "{version[0]}" -is:retweet'}
        try:
            import json
            obj=json.loads(request('https://api.x.com/2/tweets/search/recent?'+urlencode({'query':search['query'],'max_results':10,'tweet.fields':'created_at'}),token=x_token))
            if 'errors' in obj:raise ValueError('X検索エラー')
            for post in obj.get('data',[]):
                if not post.get('created_at') or version[0] not in post.get('text',''):continue
                result['sources'].append({'url':'https://x.com/i/web/status/'+post['id'],'title':'Xの投稿（原文）','publishedAt':post['created_at'],
                    'platform':'X','kind':'user_report','summary':post['text'][:240],'relation':'版の一致のみ。実利用・機能の関連性は未確認。','verified':False})
            search['status']='found' if any(s['platform']=='X' for s in result['sources']) else 'not_found'
        except Exception as e:search.update(status='unavailable',reason=type(e).__name__)
        result['searches'].append(search)
    else:result['searches'].append({'platform':'X','status':'unavailable','reason':'X API未設定。検索結果を取得していないため、確認できた事例なし。'})
    result['status']='candidates' if result['sources'] else 'none'
    return result

def due(item):
    c=item.get('details',{}).get('community',{})
    if c.get('editorial'):return False
    stamp=c.get('checkedAt')
    if not stamp:return True
    try:return datetime.now(timezone.utc)-datetime.fromisoformat(stamp.replace('Z','+00:00')) > timedelta(days=7)
    except ValueError:return True
