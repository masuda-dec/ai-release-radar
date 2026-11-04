import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('radar_update', Path(__file__).resolve().parents[1] / 'scripts' / 'update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class TestRadarUpdate(unittest.TestCase):
    def test_datetime_timezone(self):
        self.assertEqual(update.jst_date('2026-10-29T16:00:00Z'), '2026-10-30')

    def test_feed(self):
        rss = '<rss><channel><item><title>Gemini 4 upgrade</title><link>https://example.com/a</link><pubDate>Fri, 30 Oct 2026 00:00:00 +0000</pubDate><description>New model.</description></item></channel></rss>'
        out = update.parse_feed(rss)
        self.assertEqual(out[0][0], 'Gemini 4 upgrade')
        self.assertEqual(out[0][2], '2026-10-30')

    def test_html_strip(self):
        self.assertEqual(update.clean_html('<p>Hello <b>world</b></p><script>unsafe</script>'), 'Hello world')

    def test_rss_uses_full_content_instead_of_version_only_description(self):
        rss = '<rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><item><title>Codex CLI Release</title><link>https://example.com/codex</link><description>0.166.0</description><content:encoded><![CDATA[<p>Fixed sandbox permissions.</p>]]></content:encoded></item></channel></rss>'
        self.assertEqual(update.parse_feed(rss)[0][3], 'Fixed sandbox permissions.')

    def test_safety_priority(self):
        self.assertEqual(update.evaluate('Claude Code', '開発・CLI', 4, 'Fixed macOS sandbox permissions'), 5)

    def test_duplicate_seeded_releases(self):
        curr = [{'id': 'claude-2-1-314', 'product': 'Claude Code', 'date': '2026-10-30', 'title': 'Claude Code 2.1.314：安全性'}]
        new = {'id': 'gh:anthropics/claude-code:v2.1.314', 'date': '2026-10-30', 'product': 'Claude Code', 'title': 'Claude Code v2.1.314：公式リリース'}
        self.assertTrue(update.same_release(new, curr))

    def test_version_prefix_does_not_hide_new_release(self):
        older = {'id': 'seeded', 'product': 'Claude Code', 'date': '2026-11-03', 'title': 'Claude Code 2.1.3170'}
        new = {'id': 'gh:anthropics/claude-code:v2.1.317', 'product': 'Claude Code', 'date': older['date']}
        self.assertFalse(update.same_release(new, [older]))

    def test_publish_rejects_invalid_score_and_duplicate_ids(self):
        item = self.make_item()
        update.validate_public_items([item])
        with self.assertRaises(ValueError):
            update.validate_public_items([item, item])
        with self.assertRaises(ValueError):
            update.validate_public_items([dict(item, score=6)])

    def test_large_json_response_is_not_truncated(self):
        payload = json.dumps([{'body': 'x' * 2_100_000}]).encode()
        with patch.object(update, 'urlopen', return_value=io.BytesIO(payload)):
            self.assertEqual(json.loads(update.request('https://example.com'))[0]['body'], 'x' * 2_100_000)

    def test_oversize_response_is_explicit_error(self):
        with patch.object(update, 'MAX_RESPONSE_BYTES', 10), patch.object(update, 'urlopen', return_value=io.BytesIO(b'x' * 11)):
            with self.assertRaisesRegex(ValueError, '16MiB'):
                update.request('https://example.com')

    def release(self, tag, preview=False):
        return {'tag_name': tag, 'prerelease': preview, 'published_at': update.JST_NOW().isoformat(), 'body': 'Fixed sandbox permissions when resuming an agent session.'}

    def test_github_paginates_past_prereleases(self):
        first = [self.release('pre-' + str(n), True) for n in range(3)]
        with patch.object(update, 'request', side_effect=[json.dumps(first), json.dumps([self.release('v1')])]) as req:
            out = update.gather_github('Codex', 'openai/codex', '開発・CLI', 5)
        self.assertEqual(len(out), 1)
        self.assertIn('per_page=3&page=1', req.call_args_list[0].args[0])
        self.assertIn('per_page=3&page=2', req.call_args_list[1].args[0])
        self.assertIn('安全性', out[0]['summary'])
        self.assertIn('Fixed sandbox', out[0]['sourceExcerpt'])

    def test_github_bounds_pages_and_result_count(self):
        previews = json.dumps([self.release('pre', True)] * 3)
        with patch.object(update, 'request', return_value=previews) as req:
            self.assertEqual(update.gather_github('Codex', 'openai/codex', '開発・CLI', 5), [])
            self.assertEqual(req.call_count, 10)
        pages = [json.dumps([self.release('v' + str(n)) for n in range(start, start+3)]) for start in (0, 3)]
        with patch.object(update, 'request', side_effect=pages) as req:
            self.assertEqual(len(update.gather_github('Codex', 'openai/codex', '開発・CLI', 5)), 4)
            self.assertEqual(req.call_count, 2)

    def test_github_rejects_error_object(self):
        with patch.object(update, 'request', return_value='{"message":"rate limit"}'):
            with self.assertRaises(ValueError):
                update.gather_github('Codex', 'openai/codex', '開発・CLI', 5)

    def test_japanese_fallback_is_honest_and_handles_unknown_topic(self):
        self.assertIn('暫定分類', update.japanese_fallback('Fixed security permissions'))
        self.assertIn('公式原文', update.japanese_fallback('Unclassified announcement'))
        self.assertEqual(update.japanese_fallback('日本語の変更内容です。'), '日本語の変更内容です。')

    def test_localization_preserves_reviewed_items_and_original(self):
        reviewed = {'id': 'manual', 'auto': True, 'reviewed': True, 'summary': 'Keep reviewed text'}
        before = copy.deepcopy(reviewed)
        self.assertEqual(update.localize_item(reviewed), before)
        item = self.make_item()
        self.assertEqual(item['sourceExcerpt'], 'Fixed sandbox permissions for agents.')
        before = copy.deepcopy(item)
        self.assertEqual(update.localize_item(item), before)
        self.assertEqual(item['tags'].count('日本語暫定分類'), 1)

    def make_item(self):
        return update.make_item('new', update.JST_NOW().date().isoformat(), 'Codex', '開発・CLI', 'Codex v1', 'Fixed sandbox permissions for agents.', 'https://example.com/new', 5)

    def test_official_changelog_keeps_product_updates_without_keyword(self):
        rss = '<rss><channel><item><title>New calendar plugins</title><link>https://learn.chatgpt.com/update</link><pubDate>' + update.JST_NOW().isoformat() + '</pubDate><description>New integration for your workspace.</description></item></channel></rss>'
        with patch.object(update, 'request', return_value=rss):
            items = update.gather_rss('ChatGPT & Codex Changelog', 'https://learn.chatgpt.com/docs/changelog/rss.xml', 'モデル・エージェント', 4)
        self.assertEqual(len(items), 1)
        self.assertIn('暫定分類', items[0]['summary'])
        self.assertNotIn('https://help.openai.com/en/articles/6825453-chatgpt-release-notes', [u for _, u in update.WATCH_SOURCES])

    def test_no_key_keeps_fallback(self):
        item = self.make_item()
        before = copy.deepcopy(item)
        with patch.dict(update.os.environ, {}, clear=True), patch.object(update, 'urlopen') as request:
            self.assertEqual(update.ai_enrich(item), before)
            request.assert_not_called()

    def test_model_default_override_and_japanese_response(self):
        result = {'summary': '修正が公開されました。', 'why': '安全性に関わります。', 'try': 'テスト環境で確認してください。', 'availability': '利用条件は不明です。'}
        result['details'] = copy.deepcopy(self.make_item()['details'])
        response = json.dumps({'choices': [{'message': {'content': json.dumps(result)}}]}).encode()
        for override, expected in [('', update.DEFAULT_MODEL), ('  ', update.DEFAULT_MODEL), (' custom-model ', 'custom-model')]:
            with self.subTest(override=override), patch.dict(update.os.environ, {'OPENAI_API_KEY': 'test-only', 'RADAR_MODEL': override}, clear=True), patch.object(update, 'urlopen', return_value=io.BytesIO(response)) as req:
                item = update.ai_enrich(self.make_item())
                payload = json.loads(req.call_args.args[0].data)
                self.assertEqual(payload['model'], expected)
                self.assertIn('Fixed sandbox', payload['messages'][1]['content'])
                self.assertEqual(item['summary'], result['summary'])
                self.assertNotIn('日本語暫定分類', item['tags'])
                self.assertIn('AI要約', item['tags'])

    def test_invalid_ai_response_does_not_replace_fallback(self):
        for result in ({'summary': 'English only'}, {'summary': '更新です。'}, []):
            response = json.dumps({'choices': [{'message': {'content': json.dumps(result)}}]}).encode()
            item = self.make_item()
            before = copy.deepcopy(item)
            with self.subTest(result=result), patch.dict(update.os.environ, {'OPENAI_API_KEY': 'test-only'}, clear=True), patch.object(update, 'urlopen', return_value=io.BytesIO(response)):
                with self.assertRaises(ValueError):
                    update.ai_enrich(item)
                self.assertEqual(item, before)

    def test_online_update_preserves_history_and_is_idempotent(self):
        reviewed = {'id': 'reviewed', 'auto': False, 'reviewed': True, 'date': '2026-10-01', 'score': 5, 'summary': 'Reviewed original', 'sourceUrl': 'https://example.com/reviewed'}
        old_auto = dict(self.make_item(), id='old', summary='Fixed permissions.', sourceExcerpt='Fixed permissions.')
        new = self.make_item()
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            checks = [{'url': 'https://openai.com/products/release-notes/'}, {'url': 'https://example.com/keep'}]
            (data / 'releases.json').write_text(json.dumps({'items': [reviewed, old_auto], 'checks': checks}))
            (data / 'page_hashes.json').write_text('{"existing-url":"existing-hash"}')
            with patch.object(update, 'DATA', data), patch.object(update.sys, 'argv', ['update.py','--no-community']), patch.object(update, 'GITHUB_SOURCES', [('Codex', 'openai/codex', '開発・CLI', 5)]), patch.object(update, 'RSS_SOURCES', []), patch.object(update, 'WATCH_SOURCES', []), patch.object(update, 'gather_github', return_value=[new]), patch.object(update, 'ai_enrich', side_effect=lambda item: item):
                self.assertEqual(update.main(), 0)
                first = json.loads((data / 'releases.json').read_text())
                self.assertEqual(update.main(), 0)
                final = json.loads((data / 'releases.json').read_text())
            self.assertEqual(first['items'], final['items'])
            self.assertEqual(len(final['items']), 3)
            self.assertEqual(first['checks'], final['checks'])
            self.assertIn({'url': 'https://example.com/keep'}, final['checks'])
            self.assertNotIn({'url': 'https://openai.com/products/release-notes/'}, final['checks'])
            self.assertEqual(sum(c.get('url') == update.OPENAI_CHANGELOG_URL for c in final['checks']), 1)
            self.assertEqual({k:v for k,v in next(i for i in final['items'] if i['id'] == 'reviewed').items() if k!='details'}, reviewed)
            self.assertIn('暫定分類', next(i for i in final['items'] if i['id'] == 'old')['summary'])
            self.assertEqual(json.loads((data / 'page_hashes.json').read_text()), {'existing-url': 'existing-hash'})
            self.assertEqual((data / 'releases.js').read_text(), 'window.RADAR_DATA = ' + json.dumps(final, ensure_ascii=False, separators=(',', ':')) + ';\n')


if __name__ == '__main__':
    unittest.main()
