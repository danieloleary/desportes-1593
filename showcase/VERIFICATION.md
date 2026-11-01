# Reproduce the saved-file check

The dataset is **folio 179r**, not the reader’s folios 186 and 189.
The counter finds **4 edits / 1,301 glyphs** and **23 edits / 1,369 letters**.
Four unresolved `#` name/title placeholders count in glyphs and are excluded from
letters. Their identities have no accuracy score here.

These exposed references were made with model assistance. Agreement with them
does not establish independent manuscript accuracy, prove blinding, or reproduce
the original image-to-text pipeline. The reader’s letters have no independently
verified accuracy score in this fork.

## Download and verify

Download [the 13-file verifier ZIP](downloads/desportes-saved-verifier.zip) and
[SHA256SUMS.txt](downloads/SHA256SUMS.txt) into the same folder. On macOS or Linux:

```sh
shasum -a 256 -c SHA256SUMS.txt
unzip desportes-saved-verifier.zip
cd desportes-saved-verifier
python3 -B -m unittest -v test_score_saved.py
python3 -I -B score_saved.py \
  --gold inputs/f179r.txt \
  --machine inputs/f179r_machine_blind.txt \
  --manifest manifest.json \
  --output report.json
```

Python 3.10 or later and its standard library are sufficient. Use a fresh output
filename: an existing report is refused. The ten scorer test groups include an
independent recursive edit oracle, pinned input checks, placeholder policy,
invalid-input handling, tampering, and output-preservation controls.

## Trace the inputs and result

- [Exact public result record](evidence/saved-score.json): errors, denominators,
  method identity, source hashes, scorer hash, and unresolved-name coverage.
- [Input manifest](../contrib/saved-score/manifest.json) and
  [full method](../contrib/saved-score/METHOD.md).
- [Original gold](../gold/f179r.txt) and
  [saved machine output](../evidence/f179r_machine_blind.txt).
- [Reader source manifest](SOURCE_MANIFEST.json): hashes for the two different
  letter texts shown in the reader.

The pinned upstream commit is
`33c854af9d1a005e2d4fbb034a61c37f3682c6f6`. Original source text is by Paolo Rosson
with Claude (Anthropic), CC BY 4.0. The independent counter is MIT code. This
result record is an attributed saved-data report, not a new decipherment.

## Check the repository and rebuild the download

From the repository root:

```sh
node --test showcase/tests/source-integrity.test.cjs
python3 -I -B showcase/package_verifier.py --check
```

The six Node.js groups check exact reader text, source hashes, local links,
runtime boundaries, download bindings, and a fresh scorer run. The last group
compares published input/scorer/manifest hashes, run identity, result fields,
and placeholder coverage against the actual source files and new calculation. Rebuild the archive with
`python3 -I -B showcase/package_verifier.py`. It includes only thirteen explicit
files, checks their inventory, and uses fixed ZIP metadata and uncompressed
entries so the same source bytes reproduce the same archive hash.

The published checks are runnable locally. No GitHub Actions workflow or required
CI check is configured for this showcase; a local pass is not labeled as hosted
CI. Browser validation is recorded separately from scorer correctness.
