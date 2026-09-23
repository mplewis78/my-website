#!/usr/bin/env python3
"""
Fetches both Substack RSS feeds and updates writing.html.

Mike & Ned's Links  → https://startupthoughts.substack.com/feed
Advisor posts       → https://advisormike.substack.com/feed

Runs weekly via GitHub Actions (.github/workflows/update-writing.yml).
Can also be run manually:  python3 scripts/update_writing.py
"""

import html as html_mod
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

# Path to writing.html relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WRITING_HTML = os.path.join(SCRIPT_DIR, '..', 'writing.html')

MNL_FEED = 'https://startupthoughts.substack.com/feed'
ADVISOR_FEED = 'https://advisormike.substack.com/feed'

MNL_N = 4          # how many Mike & Ned issues to show
ADVISOR_N = 5        # how many advisor posts to show
DESC_MAX = 220      # characters for preview text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BROWSER_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'),
    'Accept': 'application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5',
    'Accept-Language': 'en-US,en;q=0.9',
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def items_from_relay(feed_url: str, n: int) -> list[dict]:
    """Fallback: Substack often blocks GitHub's servers (HTTP 403), so fetch the
    feed through rss2json.com, which reads it from its own servers."""
    api = 'https://api.rss2json.com/v1/api.json?rss_url=' + urllib.parse.quote(feed_url, safe='')
    data = json.loads(fetch(api))
    if data.get('status') != 'ok':
        raise RuntimeError(f"relay status {data.get('status')}: {data.get('message')}")
    items = []
    for it in data.get('items', [])[:n]:
        try:
            dt = datetime.strptime(it.get('pubDate', ''), '%Y-%m-%d %H:%M:%S')
            date_fmt = dt.strftime('%b %-d, %Y')
        except Exception:
            date_fmt = ''
        items.append({
            'title': html_mod.unescape((it.get('title') or '').strip()),
            'link': (it.get('link') or '').strip(),
            'desc': clean_html(it.get('description') or ''),
            'date': date_fmt,
            'preview': extract_link_titles(it.get('content') or ''),
        })
    return items


def get_items(feed_url: str, n: int) -> list[dict]:
    """Try Substack directly, then the relay. Raises if both fail."""
    try:
        return parse_items(fetch(feed_url), n=n)
    except Exception as e:
        print(f'  Direct fetch failed ({e}); trying relay…')
    return items_from_relay(feed_url, n)


def clean_html(text: str, maxlen: int = DESC_MAX) -> str:
    """Strip HTML tags, unescape entities, and truncate."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > maxlen:
        text = text[:maxlen].rsplit(' ', 1)[0].rstrip('.,;:') + '…'
    return text


def parse_items(xml_text: str, n: int = None) -> list[dict]:
    """Parse RSS feed into a list of dicts."""
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall('.//item'):
        title = html_mod.unescape((item.findtext('title') or '').strip())
        link  = (item.findtext('link') or '').strip()
        desc  = clean_html(item.findtext('description') or '')
        pub   = (item.findtext('pubDate') or '').strip()
        try:
            dt = parsedate_to_datetime(pub)
            date_fmt = dt.strftime('%b %-d, %Y')
        except Exception:
            date_fmt = ''
        content = item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or ''
        items.append({'title': title, 'link': link, 'desc': desc, 'date': date_fmt,
                      'preview': extract_link_titles(content)})
        if n and len(items) >= n:
            break
    return items


LINK_SKIP = re.compile(
    r'^(subscribe|share|read more|view in browser|leave a comment|comment|'
    r'enjoy the work|open in app|listen now|get the app)|placeholder', re.I)

def extract_link_titles(content_html: str, n: int = 4) -> str:
    """First few anchor texts from a post body — used as the MNL issue preview."""
    titles, seen = [], set()
    for m in re.finditer(r'<a[^>]*>(.*?)</a>', content_html, re.S):
        t = clean_html(m.group(1), maxlen=90)
        if len(t) < 10 or LINK_SKIP.search(t) or t.lower() in seen:
            continue
        seen.add(t.lower())
        titles.append(t.rstrip('.'))
        if len(titles) >= n:
            break
    return ', '.join(titles)


def replace_zone(html: str, start_marker: str, end_marker: str, new_content: str) -> str:
    """Replace everything between start_marker and end_marker."""
    pattern = re.compile(
        re.escape(start_marker) + r'.*?' + re.escape(end_marker),
        re.DOTALL
    )
    replacement = f'{start_marker}\n{new_content}\n            {end_marker}'
    result, n = pattern.subn(replacement, html)
    if n == 0:
        raise ValueError(f'Marker not found: {start_marker!r}')
    return result



# ---------------------------------------------------------------------------
# HTML generators
# ---------------------------------------------------------------------------

def make_mnl_items(items: list[dict]) -> str:
    parts = []
    for item in items:
        m = re.search(r'No\.?\s*(\d+)', item['title'])
        num = m.group(1) if m else '?'
        e_link = html_mod.escape(item['link'])
        e_date = html_mod.escape(item['date'])
        e_desc = html_mod.escape(item['preview'] or item['desc'])
        parts.append(
            f'            <a class="mnl-item" href="{e_link}" target="_blank" rel="noopener">\n'
            f'              <span class="nday">Issue<span class="num">{num}</span></span>\n'
            f'              <div>\n'
            f'                <h3><em>{e_date}</em></h3>\n'
            f'                <p class="preview">\n'
            f'                  <strong>This week →</strong> {e_desc}\n'
            f'                </p>\n'
            f'              </div>\n'
            f'              <span class="arrow">↗</span>\n'
            f'            </a>'
        )
    return '\n\n'.join(parts)


# Simple keyword → tag mapping for advisor posts
TAG_MAP = [
    (['fundrais', 'investor', 'vc ', 'raise', 'pitch', 'seed', 'series'],  'strategy'),
    (['network', 'cold email', 'community'],                                 'strategy'),
    (['team', 'hiring', 'culture', 'people'],                                'org'),
    (['leader', 'manage', 'execut'],                                         'leadership'),
    (['psycholog', 'mindset', 'emotion', 'founder'],                         'founder-psychology'),
    (['decision', 'choice', 'tradeoff'],                                     'decisions'),
]

def tag_for(title: str, desc: str) -> tuple[str, str]:
    """Return (data-tag, display-tag) for an advisor post."""
    text = (title + ' ' + desc).lower()
    for keywords, tag in TAG_MAP:
        if any(kw in text for kw in keywords):
            display = tag.replace('-', ' ').title()
            return tag, display
    return 'strategy', 'Strategy'


def make_advisor_posts(items: list[dict]) -> str:
    parts = []
    for item in items:
        _, tag_label = tag_for(item['title'], item['desc'])
        e_link  = html_mod.escape(item['link'])
        e_date  = html_mod.escape(item['date'])
        e_title = html_mod.escape(item['title'])
        e_desc  = html_mod.escape(item['desc'])
        e_tag   = html_mod.escape(tag_label)
        parts.append(
            f'            <a class="mnl-item" href="{e_link}" target="_blank" rel="noopener">\n'
            f'              <span class="ndate">{e_date}<span class="tag">{e_tag}</span></span>\n'
            f'              <div>\n'
            f'                <h3>{e_title}</h3>\n'
            f'                <p class="preview">{e_desc}</p>\n'
            f'              </div>\n'
            f'              <span class="arrow">↗</span>\n'
            f'            </a>'
        )
    return '\n\n'.join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with open(WRITING_HTML, encoding='utf-8') as f:
        html = f.read()

    changed = False
    failures = 0

    # --- Mike & Ned's Links ---
    try:
        print('Fetching Mike & Ned RSS…')
        mnl_items = get_items(MNL_FEED, MNL_N)
        if not mnl_items:
            print('  No MNL items found, skipping.')
        else:
            html = replace_zone(
                html,
                '<!-- MNL-AUTO-START -->',
                '<!-- MNL-AUTO-END -->',
                make_mnl_items(mnl_items)
            )
            # Update issue count in stats and archive line
            m = re.search(r'No\.?\s*(\d+)', mnl_items[0]['title'])
            if m:
                n = m.group(1)
                html = re.sub(
                    r'(<span class="num" id="mnl-count">)\d+(</span>)',
                    rf'\g<1>{n}\2',
                    html
                )
                html = re.sub(r'\d+ issues in the archive', f'{n} issues in the archive', html)
            print(f'  Updated {len(mnl_items)} MNL items (latest: {mnl_items[0]["title"]})')
            changed = True
    except Exception as e:
        print(f'  ERROR fetching MNL feed: {e}', file=sys.stderr)
        failures += 1

    # --- Advisor posts ---
    try:
        print('Fetching advisor RSS…')
        advisor_items = get_items(ADVISOR_FEED, ADVISOR_N)
        if not advisor_items:
            print('  No advisor items found, skipping.')
        else:
            html = replace_zone(
                html,
                '<!-- ADVISORMIKE-AUTO-START -->',
                '<!-- ADVISORMIKE-AUTO-END -->',
                make_advisor_posts(advisor_items)
            )
            html = re.sub(
                r'(<span class="num" id="essay-count">)\d+(</span>)',
                rf'\g<1>{len(advisor_items)}\2',
                html
            )
            print(f'  Updated {len(advisor_items)} advisor posts (latest: {advisor_items[0]["title"]})')
            changed = True
    except Exception as e:
        print(f'  ERROR fetching advisor feed: {e}', file=sys.stderr)
        failures += 1

    if changed:
        with open(WRITING_HTML, 'w', encoding='utf-8') as f:
            f.write(html)
        print('writing.html saved.')
    else:
        print('No changes made.')

    # Fail the run (red X + GitHub email) if any feed couldn't be read,
    # instead of silently reporting success.
    if failures:
        sys.exit(f'{failures} feed(s) failed to load — see errors above.')


if __name__ == '__main__':
    main()
