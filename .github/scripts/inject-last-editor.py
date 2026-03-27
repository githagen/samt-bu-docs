#!/usr/bin/env python3
"""
Inject last_editor into frontmatter for .md files changed in the triggering push.
Run in CI after checkout, before hugo build.

Env vars required:
  GITHUB_ACTOR      – login-navn på personen som trigget workflow
  GITHUB_TOKEN      – for GitHub API-kall (tilgjengelig automatisk i Actions)
  TRIGGERING_SHA    – SHA for commit som trigget workflow (${{ github.sha }})
"""
import os
import re
import subprocess
import urllib.request
import json


def get_display_name(actor, token):
    """Hent display-navn fra GitHub API. Returnerer 'login (navn)' eller 'login'."""
    try:
        req = urllib.request.Request(
            f'https://api.github.com/users/{actor}',
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        name = (data.get('name') or '').strip()
        return f'{actor} ({name})' if name else actor
    except Exception as e:
        print(f'Advarsel: klarte ikke hente display-navn for {actor}: {e}')
        return actor


def get_changed_md_files(sha):
    """Finn .md-filer endret i den angitte commit-en (sammenlignet med foreldrecommit)."""
    result = subprocess.run(
        ['git', 'diff', '--name-only', f'{sha}^1', sha],
        capture_output=True, text=True
    )
    files = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line.endswith('.md') and os.path.isfile(line):
            files.append(line)
    return files


def inject_last_editor(filepath, author):
    """Sett last_editor i frontmatter hvis mangler eller er bot-verdi. Returnerer True ved endring."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        return False
    end = content.find('\n---', 3)
    if end == -1:
        return False

    frontmatter = content[3:end]
    rest = content[end:]

    existing = re.search(r'^last_editor:\s*(.*)$', frontmatter, re.MULTILINE)
    if existing:
        current_val = existing.group(1).strip()
        if current_val and '[bot]' not in current_val:
            return False  # menneskelig verdi – behold
        frontmatter = re.sub(
            r'^last_editor:.*$', f'last_editor: {author}',
            frontmatter, flags=re.MULTILINE
        )
    else:
        frontmatter = frontmatter.rstrip('\n') + f'\nlast_editor: {author}\n'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('---' + frontmatter + rest)
    return True


actor = os.environ.get('GITHUB_ACTOR', '')
token = os.environ.get('GITHUB_TOKEN', '')
sha = os.environ.get('TRIGGERING_SHA', 'HEAD')

if not actor:
    print('Feil: GITHUB_ACTOR ikke satt')
    raise SystemExit(1)

author = get_display_name(actor, token)
print(f'Actor: {actor} → last_editor: "{author}"')

changed = get_changed_md_files(sha)
if not changed:
    print('Ingen .md-filer endret i denne pushen')
    raise SystemExit(0)

updated = 0
for filepath in changed:
    if inject_last_editor(filepath, author):
        print(f'  Oppdatert: {filepath}')
        updated += 1
    else:
        print(f'  Uendret (menneskelig verdi finnes): {filepath}')

print(f'\n{updated} fil(er) oppdatert')
