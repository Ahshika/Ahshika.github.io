"""Write the latest test counts from stats.json into both CV sources.

Every test count in the CV is wrapped like
    <span data-tests="Repo-Name">85 tests</span>
and is rewritten from stats.json (unit tests, plus k6 load tests when the repo
has any). Prints what changed and writes changed=true/false to $GITHUB_OUTPUT,
so the workflow only re-renders the PDFs when a number actually moved.
"""
import json
import os
import re
import sys

STATS = 'stats.json'
SPAN = re.compile(r'(<span data-tests="([^"]+)">)(.*?)(</span>)')


def phrase(lang, unit, load):
    if lang == 'AR':
        text = f'{unit} اختبار'
        return text + (f' و{load} اختبار ضغط k6' if load else '')
    text = f'{unit} tests'
    return text + (f' + {load} k6 load tests' if load else '')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # Arabic output on any console
    with open(STATS, encoding='utf-8') as f:
        repos = {k.lower(): v for k, v in json.load(f)['repos'].items()}
    changed = False
    for lang in ('EN', 'AR'):
        path = f'cv-src/Ahmed-Hassan-CV-{lang}.html'
        with open(path, encoding='utf-8') as f:
            text = f.read()

        def repl(m):
            r = repos.get(m.group(2).lower())
            if not r or not r['total']:
                return m.group(0)
            return m.group(1) + phrase(lang, r['unit'], r['load']) + m.group(4)

        new = SPAN.sub(repl, text)
        if new != text:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            changed = True
            for old, upd in zip(SPAN.findall(text), SPAN.findall(new)):
                if old[2] != upd[2]:
                    print(f'{path}: {old[1]}: "{old[2]}" -> "{upd[2]}"')
    if not changed:
        print('CV test counts are up to date.')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'cv_changed={"true" if changed else "false"}\n')


if __name__ == '__main__':
    main()
