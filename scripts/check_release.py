"""Check the release tree (or exact Git index) for private material before sharing."""
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
allowed_roots = {'agents', 'assets', 'references', 'scripts', 'tests'}
allowed_top = {'SKILL.md', 'README.md', '.gitignore', 'requirements.txt'}
allowed_suffixes = {'.md', '.py', '.js', '.cjs', '.css', '.html', '.swift', '.yaml', '.yml', '.txt'}
patterns = [
    r'https?://(?:docs|drive)\.google\.com/[^\s]+',
    r'codex://threads/[0-9a-f-]{20,}',
    r'/Users/[A-Za-z0-9_.-]+/',
    r'(?i)(?:ghp|gho)_[A-Za-z0-9]{20,}',
    r'(?i)sk-[A-Za-z0-9_-]{20,}',
    r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
]
if (root / '.git').exists():
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    files = [n for n in names if n]
    def contents(name):
        return subprocess.check_output(['git', 'show', ':' + name], cwd=root)
else:
    files = [str(p.relative_to(root)) for p in root.rglob('*')
             if p.is_file() and not any(x in p.relative_to(root).parts for x in ('.venv', '__pycache__', '.git'))]
    def contents(name):
        return (root / name).read_bytes()
errors = []
for name in files:
    p = Path(name)
    if (len(p.parts) == 1 and name not in allowed_top) or (len(p.parts) > 1 and p.parts[0] not in allowed_roots):
        errors.append(name + ': outside release allowlist')
        continue
    if p.name != '.gitignore' and p.suffix not in allowed_suffixes:
        errors.append(name + ': unsupported file type')
        continue
    try:
        text = contents(name).decode('utf-8')
    except UnicodeError:
        errors.append(name + ': binary or non-UTF8 content')
        continue
    for pattern in patterns:
        if re.search(pattern, text):
            errors.append(name + ': possible private identifier (inspect locally)')
            break
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'Release check passed: {len(files)} text source files; no material files or matched private identifiers.')
