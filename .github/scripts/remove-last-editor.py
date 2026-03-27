#!/usr/bin/env python3
"""
Fjern last_editor-feltet fra frontmatter i alle .md-filer.

Kjøres én gang som del av omleggingen til build-time-injeksjon.
last_editor skrives nå utelukkende av inject-lastmod.py i CI
(ikke committing) og skal ikke lagres i frontmatter.

Kjør fra rot av samt-bu-docs:
  python .github/scripts/remove-last-editor.py
"""
import os
import re

REPOS = [
    'S:/app-data/github/samt-x-repos/samt-bu-docs/content',
    'S:/app-data/github/samt-x-repos/team-architecture/content',
    'S:/app-data/github/samt-x-repos/team-semantics/content',
    'S:/app-data/github/samt-x-repos/samt-bu-drafts/content',
    'S:/app-data/github/samt-x-repos/solution-samt-bu-docs/content',
    'S:/app-data/github/samt-x-repos/team-pilot-1/content',
]

_LAST_EDITOR_RE = re.compile(r'^last_editor:.*\n?', re.MULTILINE)


def remove_last_editor(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        return False
    end = content.find('\n---', 3)
    if end == -1:
        return False

    frontmatter = content[3:end]
    if not re.search(r'^last_editor:', frontmatter, re.MULTILINE):
        return False

    new_fm = _LAST_EDITOR_RE.sub('', frontmatter)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('---' + new_fm + content[end:])
    return True


total = 0
for content_path in REPOS:
    if not os.path.isdir(content_path):
        print(f'Hopper over {content_path} (ikke funnet)')
        continue
    repo_count = 0
    for root, _, files in os.walk(content_path):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            if remove_last_editor(os.path.join(root, filename)):
                repo_count += 1
    print(f'{content_path}: {repo_count} filer oppdatert')
    total += repo_count

print(f'\nTotalt: {total} filer')
