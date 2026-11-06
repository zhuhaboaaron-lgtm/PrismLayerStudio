"""Bundle the modular offline app into one HTML document for Gitee Pages/local opening."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
app = root / 'app'
html = (app / 'index.html').read_text(encoding='utf-8')
css = (app / 'style.css').read_text(encoding='utf-8') + '\n' + (app / 'hero.css').read_text(encoding='utf-8')
core_js = (app / 'core.js').read_text(encoding='utf-8')
app_js = (app / 'app.js').read_text(encoding='utf-8')
hero_js = (app / 'hero.js').read_text(encoding='utf-8')
assert '<link rel="stylesheet" href="style.css">' in html
assert '<script src="core.js"></script><script src="app.js"></script><script src="hero.js"></script>' in html
html = html.replace('<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="hero.css">','<style>\n'+css+'\n</style>')
html = html.replace('<script src="core.js"></script><script src="app.js"></script><script src="hero.js"></script>',
                    '<script>\n'+core_js+'\n</script><script>\n'+app_js+'\n</script><script>\n'+hero_js+'\n</script>')
assert 'src="core.js"' not in html and 'href="style.css"' not in html
folder = root / 'publish'
folder.mkdir(exist_ok=True)
(folder/'index.html').write_text(html, encoding='utf-8')
print('Single HTML written:',folder/'index.html',len(html),'chars')
