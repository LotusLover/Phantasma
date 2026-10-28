"""Check public documents without dependencies, credentials or network access."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def validate(root):
    root = Path(root).resolve()
    errors = []
    drive_path = re.compile(r'[A-Za-z]' + chr(58) + r'[\\/]')
    secret = re.compile(r'(?i)(?:gh[pousr]_[A-Za-z0-9]{15,}|github_pat_[A-Za-z0-9_]{15,}|sk-[A-Za-z0-9_-]{16,})')
    forbidden = {'.env','hosts.yml','inventory.json','projects.json','verification.key'}
    text_types = {'.md','.json','.yml','.yaml','.py','.txt','.ts','.tsx','.html','.css'}
    checked = 0
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if '.git' in relative.parts or '__pycache__' in relative.parts:
            continue
        if path.is_symlink():
            errors.append(str(relative) + ': symlinks are not permitted')
            continue
        if not path.is_file():
            continue
        if path.name in forbidden or path.name.startswith('.env.'):
            errors.append(str(relative) + ': private filename')
        if path.suffix not in text_types:
            continue
        checked += 1
        body = path.read_text(encoding='utf-8')
        if drive_path.search(body) or secret.search(body) or ('-----BEGIN ' + 'PRIVATE KEY-----') in body:
            errors.append(str(relative) + ': private path or credential pattern')
        if path.suffix == '.md':
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', body):
                target = target.strip('<>').split(' "',1)[0]
                if re.match(r'^(https?://|mailto:|#)', target):
                    continue
                name = unquote(target.split('#',1)[0])
                resolved = (path.parent / name).resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    errors.append(str(relative) + ': broken local link ' + name)
    return {'status':'passed' if not errors else 'failed','files_checked':checked,'errors':errors}


if __name__ == '__main__':
    result = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(result,ensure_ascii=True,indent=2))
    raise SystemExit(0 if result['status']=='passed' else 1)
