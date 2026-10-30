"""Create a portable (snapshot-only) single-file preview for immediate use."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text(encoding='utf-8')
html=html.replace('<link rel="stylesheet" href="assets/styles.css">','<style>\n'+(ROOT/'assets/styles.css').read_text(encoding='utf-8')+'\n</style>')
html=html.replace('<script src="data/releases.js"></script>','<script>\n'+(ROOT/'data/releases.js').read_text(encoding='utf-8')+'\n</script>')
html=html.replace('<script src="assets/app.js"></script>','<script>\n'+(ROOT/'assets/app.js').read_text(encoding='utf-8')+'\n</script>')
p=ROOT.parent/'AI_Release_Radar_Preview.html'
p.write_text(html,encoding='utf-8')
print(f'{p} ({p.stat().st_size:,} bytes)')
