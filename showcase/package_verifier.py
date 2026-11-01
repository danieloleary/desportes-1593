"""Build or check the exact offline verifier download, using standard libraries."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'contrib/saved-score'
DOWNLOADS = ROOT / 'showcase/downloads'
NAME = 'desportes-saved-verifier.zip'
FILES = ('AGENTS.md', 'CLAUDE.md', 'CREDITS.md', 'HASH_MANIFEST.json', 'LICENSE',
         'METHOD.md', 'README.md', 'UPSTREAM_LICENSE.md', 'inputs/f179r.txt',
         'inputs/f179r_machine_blind.txt', 'manifest.json', 'score_saved.py',
         'test_score_saved.py')

def archive_bytes():
    snapshots = {name: (PACKAGE / name).read_bytes() for name in FILES}
    inventory = json.loads(snapshots['HASH_MANIFEST.json'])['files']
    assert set(inventory) == set(FILES) - {'HASH_MANIFEST.json'}
    for name, expected in inventory.items():
        if hashlib.sha256(snapshots[name]).hexdigest() != expected:
            raise ValueError('Verifier input changed: ' + name)
    out = io.BytesIO()
    # Stored entries avoid compression-version differences. No timestamps, host
    # paths, credentials, execution logs, scans, or other project files enter it.
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(FILES):
            info = zipfile.ZipInfo('desportes-saved-verifier/' + name, (2026, 11, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, snapshots[name])
    return out.getvalue()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify existing download without writing it')
    args = parser.parse_args()
    data = archive_bytes()
    digest = hashlib.sha256(data).hexdigest()
    checksums = digest + '  ' + NAME + '\n'
    if args.check:
        if (DOWNLOADS / NAME).read_bytes() != data or (DOWNLOADS / 'SHA256SUMS.txt').read_text() != checksums:
            raise ValueError('Download or checksum differs from the exact package source')
    else:
        DOWNLOADS.mkdir(exist_ok=True)
        (DOWNLOADS / NAME).write_bytes(data)
        (DOWNLOADS / 'SHA256SUMS.txt').write_text(checksums)
    print(json.dumps({'status': 'passed', 'files': len(FILES), 'bytes': len(data), 'sha256': digest, 'check_only': args.check}))

if __name__ == '__main__':
    main()
