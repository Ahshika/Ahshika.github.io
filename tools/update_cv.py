"""Add any new public GitHub repo to both CV sources (cv-src/*.html).

Prints what changed and writes changed=true/false to $GITHUB_OUTPUT.
"""
import html
import json
import os
import re
import urllib.request

USER = 'Ahshika'
# Portfolio sites and their QR intros are not CV projects; never auto-add them.
SKIP = {'ahshika.github.io', 'ahshika', 'games', 'developers-room', 'gamers-room'}
MARKER = '  <!-- AUTO-PROJECTS'
REPO_LINK = r'github\.com/' + USER + r'/([A-Za-z0-9._-]+)"'
# path -> (description fallback, link attributes, month names)
FILES = {
    'cv-src/Ahmed-Hassan-CV-EN.html': ('New project on GitHub.', '',
        'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()),
    'cv-src/Ahmed-Hassan-CV-AR.html': ('مشروع جديد على GitHub.', ' class="ltr"',
        'يناير فبراير مارس أبريل مايو يونيو يوليو أغسطس سبتمبر أكتوبر نوفمبر ديسمبر'.split()),
}

# Same one-column ATS markup as the hand-written projects in cv-src/.
CARD = '''  <article class="card">
    <h3><span>{name}</span><span class="when">{when}</span></h3>
    <p class="stack">{stack}</p>
    <ul><li>{desc}</li></ul>
    <p class="links"><a{attr} href="{url}">{short}</a></p>
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


def card(repo, fallback, attr, months):
    stack = [repo['language']] if repo.get('language') else []
    stack += [t for t in (repo.get('topics') or []) if t.lower() not in {s.lower() for s in stack}]
    year, month = repo['created_at'][:7].split('-')
    sep = '، ' if attr else ', '
    return CARD.format(
        name=html.escape(nice(repo['name'])),
        when=f'{months[int(month) - 1]} {year}',
        stack=html.escape(sep.join(stack[:5]) or 'Code'),
        desc=html.escape(repo.get('description') or fallback),
        attr=attr,
        url=html.escape(repo['html_url']),
        short=html.escape(repo['html_url'].replace('https://', '')),
    )


def main():
    repos = [r for r in fetch_repos()
             if not r['fork'] and not r['archived'] and not r['private'] and r['name'].lower() not in SKIP]
    changed = False
    for path, (fallback, attr, months) in FILES.items():
        with open(path, encoding='utf-8') as f:
            text = f.read()
        if MARKER not in text:
            raise SystemExit(f'{path}: AUTO-PROJECTS marker not found')
        known = {n.lower() for n in re.findall(REPO_LINK, text)}
        new = [r for r in repos if r['name'].lower() not in known]
        if not new:
            continue
        cards = ''.join(card(r, fallback, attr, months) for r in new)
        text = text.replace(MARKER, cards + MARKER, 1)
        # Projects = distinct repos linked (one card may cover two repos, e.g. V1 & V2).
        count = len({n.lower() for n in re.findall(REPO_LINK, text)})
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
