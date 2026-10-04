"""Add any new public GitHub repo to both CV sources (cv-src/*.html).

Prints what changed and writes changed=true/false to $GITHUB_OUTPUT.
"""
import html
import json
import os
import re
import urllib.request

USER = 'Ahshika'
SKIP = {'ahshika.github.io', 'ahshika'}
MARKER = '    <!-- AUTO-PROJECTS'
FILES = {
    'cv-src/Ahmed-Hassan-CV-EN.html': 'New project on GitHub.',
    'cv-src/Ahmed-Hassan-CV-AR.html': 'مشروع جديد على GitHub.',
}

CARD = '''    <article class="card">
      <h3>{name}</h3>
      <ul><li>{desc}</li></ul>
      <div class="tags">{tags}</div>
      <div class="links"><a href="{url}">{short}</a></div>
    </article>
'''


def fetch_repos():
    headers = {'Accept': 'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    req = urllib.request.Request(f'https://api.github.com/users/{USER}/repos?per_page=100&sort=created&direction=asc', headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def nice(name):
    return ' '.join(w if w.isupper() else w[:1].upper() + w[1:] for w in re.split(r'[-_]+', name))


def card(repo, fallback):
    tags = (repo.get('topics') or [])[:5] or [repo.get('language') or 'Code']
    return CARD.format(
        name=html.escape(nice(repo['name'])),
        desc=html.escape(repo.get('description') or fallback),
        tags=''.join(f'<span class="tag">{html.escape(t)}</span>' for t in tags),
        url=html.escape(repo['html_url']),
        short=html.escape(repo['html_url'].replace('https://', '')),
    )


def main():
    repos = [r for r in fetch_repos()
             if not r['fork'] and not r['archived'] and not r['private'] and r['name'].lower() not in SKIP]
    changed = False
    for path, fallback in FILES.items():
        with open(path, encoding='utf-8') as f:
            text = f.read()
        known = {n.lower() for n in re.findall(r'github\.com/' + USER + r'/([A-Za-z0-9._-]+)"', text)}
        new = [r for r in repos if r['name'].lower() not in known]
        if not new:
            continue
        cards = ''.join(card(r, fallback) for r in new)
        text = text.replace(MARKER, cards + MARKER, 1)
        count = text.count('<article class="card">')
        text = re.sub(r'<span class="pcount">\d+</span>', f'<span class="pcount">{count}</span>', text)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        changed = True
        print(f'{path}: added {", ".join(r["name"] for r in new)} (now {count} projects)')
    if not changed:
        print('No new repositories.')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'changed={"true" if changed else "false"}\n')


if __name__ == '__main__':
    main()
