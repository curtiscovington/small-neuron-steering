import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read(path):return json.loads(Path(path).read_text())
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def save(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)
def bind(path,spec):
 path=Path(path)
 if path.exists():
  if read(path)!=spec:raise ValueError('Run settings or inputs changed; use a new output directory')
 else:save(path,spec)
