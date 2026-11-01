"""Prepare the reader from pinned public text. No upstream code is imported."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PIN = '33c854af9d1a005e2d4fbb034a61c37f3682c6f6'
EXPECTED = {'reading/f189_reading.txt': '4a40c269d98f82372da19b76a6823030f12fbeefd9148f54fd162b974bbd7f56', 'reading/f186_reading.txt': '49c48a7f995482933ccb5f5d26bd8b0f64915c7ae71a73032ec593641c41331f'}

def main():
    letters, sources = [], {}
    for folio, name, canvas in [('f189', 'Girolamo Frachetta', 353),
                                 ('f186', 'Pietro Aldobrandini', 347)]:
        relative = 'reading/' + folio + '_reading.txt'
        raw = (ROOT / relative).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == EXPECTED[relative], relative
        text = raw.decode('utf-8')
        before, marker, after = text.partition('\nTRANSLATION')
        assert marker, relative
        # Preserve the source translation and every uncertainty marker verbatim.
        english = after.partition('\n')[2].strip()
        assert english and '(?)' in before
        sources[relative] = hashlib.sha256(raw).hexdigest()
        letters.append({'id': folio, 'recipient': name, 'folio': folio[1:],
            'french': before.rstrip(), 'english': english,
            'source': '../' + relative,
            'published': '../reading/' + folio + '.md',
            'archive': 'https://gallica.bnf.fr/ark:/12148/btv1b9060633d/f' + str(canvas) + '.item'})
    data = {'pin': PIN, 'letters': letters, 'sources': sources,
        'attribution': 'Paolo Rosson with Claude (Anthropic), Two cipher letters of July 1593, read for the first time, 2026. Cipher key: Satoshi Tomokiyo. Text: CC BY 4.0.',
        'scope': 'Published provisional readings and existing English translations. No new decipherment or manuscript accuracy improvement is claimed.'}
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace('<', '\\u003c')
    (ROOT / 'showcase/data.js').write_text('window.DESPORTES = ' + payload + ';\n')
    (ROOT / 'showcase/SOURCE_MANIFEST.json').write_text(json.dumps({'upstream_commit': PIN, 'files': sources}, indent=2) + '\n')

if __name__ == '__main__':
    main()
