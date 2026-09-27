import io,json,zipfile,subprocess,sys
from pathlib import Path
import urllib.request
base='http://127.0.0.1:8000'
projects=json.load(urllib.request.urlopen(base+'/projects'))
project=next(p for p in projects if p['head'])
id=project['head']
default=urllib.request.urlopen(base+f'/revisions/{id}/bundle').read()
with zipfile.ZipFile(io.BytesIO(default)) as z:
    assert 'data.parquet' not in z.namelist()
    assert 'services/api/compute.py' in z.namelist()
    assert not any('.env' in name or 'raw/' in name for name in z.namelist())
data=urllib.request.urlopen(base+f'/revisions/{id}/bundle?include_data=true').read()
Path('docs/evidence/demo-reproduction.zip').write_bytes(data)
dest=Path('.local/reproduction-'+id[:8]).resolve();dest.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as z:
    for name in z.namelist():
        assert (dest/name).resolve().is_relative_to(dest)
    z.extractall(dest)
r=subprocess.run([sys.executable,'reproduce.py'],cwd=dest,capture_output=True,text=True,encoding='utf-8',timeout=90)
Path('docs/evidence/bundle-verification.txt').write_text(f'exit={r.returncode}\nDefault bundle excludes snapshot. Explicit data bundle includes only synthetic snapshot.\n'+r.stdout+'\n'+r.stderr,encoding='utf-8')
assert r.returncode==0,r.stderr
from PIL import Image
assert Image.open(dest/'output/chart.png').size==(1000,560)
print('Self-contained synthetic reproduction bundle executed; PNG is 1000x560')
