#!/usr/bin/env python3
"""Build a single self-contained HTML file of the live demo that can be sent to anyone.

    python3 site/build-share.py [-o karov-demo-share.html] [--url https://where-the-demo-lives]

What it does to site/karov-live.html:
  - embeds the fonts (Karantina, Assistant, IBM Plex Mono: only the Hebrew and Latin subsets) as base64,
  - embeds the qrcode-generator library (MIT, https://github.com/kazuhikoarase/qrcode-generator),
  - wraps the page in a complete HTML document.
The result needs no network and no claude.ai: with no shared database it runs in local mode, keeps its data in the
browser (localStorage) and updates between open tabs. Needs curl and network access once, to fetch the assets.
--url sets the address the per-table NFC/QR links point to (default: the published Claude artifact).
"""
import argparse, base64, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
FAMILIES = {  # css2 query -> subsets to keep
    'Karantina:wght@400;700': {'hebrew', 'latin'},
    'Assistant:wght@400;600;700;800': {'hebrew', 'latin'},
    'IBM+Plex+Mono:wght@500;600': {'latin'},
}
QR_URL = 'https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js'


def fetch(url, binary=False):
    out = subprocess.run(['curl', '-fsSL', '-m', '60', '-A', UA, url], capture_output=True, check=True).stdout
    return out if binary else out.decode('utf-8')


def font_css():
    blocks = []
    for query, keep in FAMILIES.items():
        css = fetch('https://fonts.googleapis.com/css2?family=%s&display=swap' % query)
        groups = {}  # (family, subset, url) -> [weights, unicode-range]
        for m in re.finditer(r'/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}', css, re.S):
            subset, body = m.group(1), m.group(2)
            if subset not in keep:
                continue
            family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
            weight = int(re.search(r'font-weight:\s*(\d+)', body).group(1))
            url = re.search(r'url\((https://[^)]+\.woff2)\)', body).group(1)
            rng = re.search(r'unicode-range:\s*([^;]+);', body).group(1)
            g = groups.setdefault((family, subset, url), [[], rng])
            g[0].append(weight)
        for (family, subset, url), (weights, rng) in groups.items():
            data = base64.b64encode(fetch(url, binary=True)).decode('ascii')
            w = ('%d %d' % (min(weights), max(weights))) if len(set(weights)) > 1 else str(weights[0])
            blocks.append("@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
                          "src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (family, w, data, rng))
    return '\n'.join(blocks)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--out', default='karov-demo-share.html')
    ap.add_argument('--url', help='address the per-table links point to')
    a = ap.parse_args()

    src = (HERE / 'karov-live.html').read_text(encoding='utf-8')
    title = re.search(r'<title>(.*?)</title>', src, re.S).group(1)
    src = re.sub(r'<title>.*?</title>\s*', '', src, count=1, flags=re.S)
    src, n = re.subn(r'<link rel="preconnect"[^>]*>\s*', '', src)
    src, m = re.subn(r'<link href="https://fonts\.googleapis\.com[^>]*>\s*', '', src)
    qr = fetch(QR_URL)
    if '</script' in qr.lower():
        sys.exit('qrcode library contains a closing script tag; refusing to inline it')
    src, k = re.subn(r'<script src="https://cdnjs\.cloudflare\.com/ajax/libs/qrcode-generator/[^"]*"></script>',
                     lambda _: '<script>/* qrcode-generator 1.4.4, MIT license, Kazuhiko Arase */\n' + qr + '\n</script>', src)
    if (m, k) != (1, 1):
        sys.exit('expected one font link and one qrcode script in karov-live.html, found %d and %d' % (m, k))
    if a.url:
        src, c = re.subn(r"const ARTIFACT_URL = '[^']*';", lambda _: "const ARTIFACT_URL = '%s';" % a.url.rstrip('/'), src)
        if c != 1:
            sys.exit('ARTIFACT_URL constant not found')

    page = ('<!doctype html>\n<html lang="he" dir="rtl"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="color-scheme" content="light dark">'
            '<title>%s</title>\n<style>%s\n:root{box-sizing:border-box}body{margin:0;padding:0}img{max-width:100%%}[hidden]{display:none!important}</style>'
            '</head><body>\n%s\n</body></html>\n') % (title, font_css(), src)
    Path(a.out).write_text(page, encoding='utf-8')
    external = sorted(set(re.findall(r'(?:src|href)="(https?://[^"]+)"', page)))
    print('wrote %s (%d KB)' % (a.out, len(page) // 1024))
    print('links that still point out (clickable only, nothing is loaded from them):', *external, sep='\n  ')


if __name__ == '__main__':
    main()
