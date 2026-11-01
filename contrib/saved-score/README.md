# Desportes saved-artifact verifier

Reproduce the saved folio 179 front comparison with Python 3.10+ and its standard
library. This small kit includes our scorer, tests, method and two attributed text
inputs. No project checkout, image, downloaded script, model or network is needed.

From the extracted kit directory:

```sh
python3 -B -m unittest -v test_score_saved.py
python3 -B score_saved.py --gold inputs/f179r.txt --machine inputs/f179r_machine_blind.txt --manifest manifest.json --output report.json
```

Expected whole-page output: **4 edits / 1,301 glyphs = 99.6925%** and
**23 edits / 1,369 letters = 98.3199%**. Four unresolved `#` name/title placeholders
remain in glyph scoring and are excluded from both letter streams. Their identities
are not measured. Page scores and per-line totals are reported separately.

All three input arguments are explicit. Paths may point to this kit's inputs or
the same pinned files elsewhere. The manifest and both file snapshots must match
the declared upstream commit and hashes. The scorer reads each input once and
parses the verified bytes. An existing output is refused and remains unchanged.
Failures return nonzero without a success report. Keep each result under a new name.

These are exposed saved artifacts with model-assisted reference labels. Agreement
does not establish independent manuscript accuracy, reproduce original inference,
prove that the historical experiment was blind, or identify the unresolved people.
The original full-project inventory checker remains a separate stronger source-
inventory check. See [METHOD.md](METHOD.md) and [CREDITS.md](CREDITS.md).

## ELI10

We have two saved lists: the model's answer and the project's comparison answer.
This program counts how many additions, removals or replacements turn one into
the other. You can check the counting yourself. Checking whether the answers
correctly read the old handwriting needs a separate manuscript review.

Our code is MIT. The two input texts retain Paolo Rosson's CC BY 4.0 credit.
No manuscript images are included. The kit's checked file inventory and a run
from a fresh directory are recorded alongside this contribution's release.
