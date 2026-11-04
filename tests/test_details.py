# -*- coding: utf-8 -*-
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update
import details
import community

class DetailTests(unittest.TestCase):
    def item(self, product='Codex',title='Codex v0.166.0',body='Added codex doctor --network-only for network diagnostics.'):
        return update.make_item('new',update.JST_NOW().date().isoformat(),product,'開発・CLI',title,body,'https://github.com/openai/codex/releases/tag/rust-v0.166.0',5)

    def test_cross_product_words_never_select_wrong_recipe(self):
        for version,expected in [('0.163.0','config-steering'),('0.164.0','presets'),('0.165.0','codex-session-picker')]:
            item=self.item(title='Codex CLI Release: '+version,body='Fixed shell startup sandbox. Fixed Windows ConPTY IME cursor. GPT-6.1 Terra.')
            self.assertEqual(item['details']['recipe'],expected)
            self.assertNotIn('Gemini CLI',item['details']['change'])

    def test_unknown_release_is_explicit_about_missing_facts(self):
        item=self.item(product='Unknown tool',title='Unknown tool v9.3',body='A completely new feature without known semantics.')
        d=item['details']
        self.assertIn('確認できません',d['before'])
        self.assertEqual(d['commands'],[])
        self.assertEqual(d['community']['status'],'not_searched')

    def test_editorial_survives_rebuild(self):
        i=self.item();i['details'].update(mode='editorial',workflow='人が確かめた個別の作業手順です。')
        before=copy.deepcopy(i['details'])
        self.assertEqual(details.build_details(i),before)

    def test_ai_cannot_write_community_or_evidence(self):
        i=self.item();r={k:'日本語の具体的な説明を返します。' for k in ('summary','why','try','availability')}
        r['details']=copy.deepcopy(i['details']);r['details'].update(community={'sources':[{'url':'https://fake.example'}]},officialSources=[{'url':'https://fake.example'}],mode='editorial')
        response=io.BytesIO(json.dumps({'choices':[{'message':{'content':json.dumps(r)}}]}).encode())
        with patch.dict(update.os.environ,{'OPENAI_API_KEY':'test'},clear=True),patch.object(update,'urlopen',return_value=response) as req:
            update.ai_enrich(i)
        self.assertEqual(i['details']['mode'],'ai')
        self.assertEqual(i['details']['community']['sources'],[])
        self.assertNotIn('officialSources',i['details'])
        self.assertEqual(json.loads(req.call_args.args[0].data)['max_completion_tokens'],3500)

    def test_invalid_ai_is_atomic(self):
        i=self.item();before=copy.deepcopy(i)
        r={k:'日本語の具体的な説明です。' for k in ('summary','why','try','availability')};r['details']={'steps':'bad'}
        response=io.BytesIO(json.dumps({'choices':[{'message':{'content':json.dumps(r)}}]}).encode())
        with patch.dict(update.os.environ,{'OPENAI_API_KEY':'test'},clear=True),patch.object(update,'urlopen',return_value=response):
            with self.assertRaises(ValueError):update.ai_enrich(i)
        self.assertEqual(i,before)

    def test_search_failure_is_not_no_results(self):
        def failed(*a,**kw):raise RuntimeError('network unavailable')
        c=community.collect(self.item(),failed)
        self.assertEqual(c['searches'][0]['status'],'unavailable')
        self.assertEqual(c['sources'],[])
        self.assertEqual(c['searches'][1]['status'],'unavailable')
        self.assertEqual(c['searches'][2]['platform'],'Reddit')
        self.assertEqual(c['searches'][2]['status'],'not_searched')

    def test_search_candidates_require_version_date_and_safe_url(self):
        issues=[dict(title='0.166.0 failure',body='version 0.166.0',html_url='https://github.com/openai/codex/issues/1',created_at='2026-10-30T00:00:00Z'),dict(title='unrelated',body='old',html_url='https://github.com/openai/codex/issues/2',created_at='2026-10-30T00:00:00Z'),dict(title='0.166.0',body='0.166.0',html_url='javascript:alert(1)',created_at='2026-10-30T00:00:00Z')]
        c=community.collect(self.item(),lambda *a,**kw:json.dumps({'items':issues}))
        self.assertEqual(len(c['sources']),1)
        self.assertFalse(c['sources'][0]['verified'])
        self.assertIn('未確認',c['sources'][0]['relation'])

    def test_budget_clamps_and_bad_input(self):
        for value,expect in [('500',20),('-10',0),('bad',5)]:
            with patch.dict(update.os.environ,{'TEST_BUDGET':value}):self.assertEqual(update.bounded_env('TEST_BUDGET',5,20),expect)

    def test_backlog_respects_daily_budget(self):
        items=[dict(self.item(),id=str(i)) for i in range(4)]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'releases.json').write_text(json.dumps({'items':items,'checks':[]}))
            with patch.object(update,'DATA',path),patch.object(update.sys,'argv',['update.py','--no-community']),patch.object(update,'GITHUB_SOURCES',[]),patch.object(update,'RSS_SOURCES',[]),patch.object(update,'WATCH_SOURCES',[]),patch.dict(update.os.environ,{'OPENAI_API_KEY':'test','RADAR_AI_MAX_ITEMS':'2'},clear=True),patch.object(update,'ai_enrich',side_effect=ValueError('malformed')) as enrich:
                self.assertEqual(update.main(),0)
                self.assertEqual(enrich.call_count,2)
                out=json.loads((path/'releases.json').read_text())
                self.assertEqual(len(out['items']),4)
                self.assertEqual(out['enrichment']['aiCalls'],2)

    def test_js_payload_does_not_end_inline_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'releases.json').write_text(json.dumps({'items':[],'note':'</script><script>alert(1)</script>'}))
            with patch.object(update,'DATA',path),patch.object(update.sys,'argv',['update.py','--offline']):update.main()
            self.assertNotIn('</script>',(path/'releases.js').read_text())

if __name__=='__main__':unittest.main()
