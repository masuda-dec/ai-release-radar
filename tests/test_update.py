import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('radar_update',Path(__file__).resolve().parents[1]/'scripts'/'update.py')
update=importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)
class TestRadarUpdate(unittest.TestCase):
    def test_datetime_timezone(self):
        self.assertEqual(update.jst_date('2026-10-29T16:00:00Z'),'2026-10-30')
    def test_feed(self):
        rss='<rss><channel><item><title>Gemini 4 upgrade</title><link>https://example.com/a</link><pubDate>Fri, 30 Oct 2026 00:00:00 +0000</pubDate><description>New model.</description></item></channel></rss>'
        out=update.parse_feed(rss)
        self.assertEqual(out[0][0],'Gemini 4 upgrade')
        self.assertEqual(out[0][2],'2026-10-30')
    def test_html_strip(self):
        self.assertEqual(update.clean_html('<p>Hello <b>world</b></p><script>unsafe</script>'),'Hello world')
    def test_safety_priority(self):
        self.assertEqual(update.evaluate('Claude Code','開発・CLI',4,'Fixed macOS sandbox permissions'),5)
    def test_duplicate_seeded_releases(self):
        curr=[{'id':'claude-2-1-314','product':'Claude Code','date':'2026-10-30','title':'Claude Code 2.1.314：安全性'}]
        new={'id':'gh:anthropics/claude-code:v2.1.314','date':'2026-10-30','product':'Claude Code','title':'Claude Code v2.1.314：公式リリース'}
        self.assertTrue(update.same_release(new,curr))
if __name__=='__main__':unittest.main()
