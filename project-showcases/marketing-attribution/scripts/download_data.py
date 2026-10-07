"""Download the pinned public Kaggle distribution; reject unexpected bytes."""
from pathlib import Path
import hashlib
import io
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.kaggle.com/api/v1/datasets/download/fatimahabibkhan/attribution-data?datasetVersionNumber=1'
SHA256 = 'b17dde7505e6fb41b9fd21bdbb587adc425e53f8d9e1df0a6ccea78092df5ee4'

def main():
    with urllib.request.urlopen(URL, timeout=120) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    matches = [n for n in archive.namelist() if n.lower().replace(' ','_') == 'attribution_data.csv']
    if len(matches) != 1:
        raise ValueError('Expected exactly one attribution CSV in the archive')
    content = archive.read(matches[0])
    digest = hashlib.sha256(content).hexdigest()
    if digest != SHA256:
        raise ValueError(f'Source checksum changed: {digest}; review the source before analysis')
    dest = ROOT/'data'/'attribution_data.csv'
    dest.parent.mkdir(exist_ok=True)
    dest.write_bytes(content)
    print(f'Downloaded {len(content):,} bytes; SHA256 verified')

if __name__ == '__main__':
    main()
