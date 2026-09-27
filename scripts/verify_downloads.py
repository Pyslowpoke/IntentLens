import hashlib,tomllib
from pathlib import Path
lock=tomllib.loads(Path('uv.lock').read_text())
for path in Path('.local').glob('*.whl'):
    wheel=next(w for p in lock['package'] for w in p.get('wheels',[]) if w['url'].endswith('/'+path.name))
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    assert 'sha256:'+actual==wheel['hash'],f'Checksum mismatch: {path.name}'
    print(path.name,'verified',flush=True)
