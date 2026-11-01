# Portable saved-artifact scoring contract, version 1

This is independently authored analysis code. Upstream Python was read as a format
specification; it was not imported, copied into the implementation, or executed.
The input pair is pinned `gold/f179r.txt` and `evidence/f179r_machine_blind.txt`.

## Predeclared conventions

- Parse all 21 rows by their numeric IDs. Require matching, unique, ascending IDs;
  reject malformed records and silently lost tokens.
- Map plaintext letters to the eleven polyphonic glyph classes: an, bo, cp, dq,
  er, fs, gt, hu, ix, ly, mz. Treat v as u and j as i. This is the cipher's
  equivalence convention, not modern spelling correction.
- Q, K, P, R, and & are single glyphs, expanded to que, qui, pour, par, and et in
  letter scoring. Signs can occur inside words, such as `Kl` = `quil`.
- Ignore whitespace/word segmentation in both scores. Join split lines into one
  page stream for the primary score; expose the sum of per-line scores separately.
- Score the first glyph of each saved position. Parenthesized alternatives are
  retained in the report and never selected using the reference answer.
- Preserve `#` in glyph scoring, and remove it from both letter streams. There are
  four such placeholders in this gold page. Report their count and a sensitivity
  score retaining them; neither score measures their historical identity.
- Preserve uppercase M/L class stand-ins in the machine letter stream. They are
  unresolved plaintext and count as errors against resolved reference letters.
  No lowercase reinterpretation or oracle choice is made.
- Parse explicit gold `=class` values, but reject letter scoring for such a page
  until a separate masking/alignment contract is defined. f179r contains none.
- Use unit-cost Levenshtein insertion, deletion, and substitution distance.
  Denominator = reference stream length. Accuracy = 100 × (1 − errors / length).
  This is edit-distance accuracy, not a count of individual glyph classifications.
  Insertions can produce negative accuracy; do not clamp. Empty references have
  undefined accuracy. Traceback ties prefer diagonal, deletion, then insertion;
  edit locations can be ambiguous even when distance is fixed.

## Observability and verification

Each run verifies the two pinned snapshots against SHA-256, Git blob SHA-1 and
byte length, plus the explicitly supplied manifest against the built-in commit
and input identities. It does not verify the larger 67-file source inventory.
JSON includes input/manifest/scorer hashes, portable method version, stable run ID,
UTC timestamp, Python/platform, per-line distances, edit contexts, alternatives,
placeholder coverage and operation counts. Timestamp/environment fields may vary;
content-derived run identity and distances are stable for unchanged inputs/code.
The CLI refuses existing output files and fails visibly on missing, corrupt,
unavailable or hash-mismatched input.
Tests use hand-computed edits, a separately written recursive oracle over 225 tiny
binary string pairs, malformed formats, sign expansion, spelling equivalence,
placeholder coverage, unresolved class handling, line matching, and the pinned
artifact regression. The historical score is a regression case, not the oracle
used to prove the edit algorithm.

## What this experiment establishes

The committed machine and gold artifacts give internally consistent scores under
the stated conventions. This does not reproduce image recognition or decoding,
establish independently authored gold, demonstrate historical blinding, establish
unread-page accuracy, identify people, or prove a first/new decipherment. Gold's
header explicitly records comparison with model output and the 1593 decipherment.

Specification sources: pinned `code/glyphs.py`, `code/decode.py`,
`code/eval_e2e.py`, `gold/f179r.txt`, and `evidence/worklog_league.md`.
The f179r-specific upstream `eval_struct.py` is absent, so equivalence to that
unavailable evaluator is not claimed. Matching results are reported as consistency.
