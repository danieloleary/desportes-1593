# Contribute a checkable change

Choose one task: interface, saved-score tooling, a focused decoder repair, or a
sourced reading correction. Retain counterexamples and unresolved readings.

Run the reader and owned checks from the repository root:

```sh
python3 showcase/serve.py
python3 -B -m unittest discover -s contrib/saved-score -p test_score_saved.py -v
node --test showcase/tests/source-integrity.test.cjs
```

The reader is bound to fixed public source hashes. A different source revision
requires a deliberate pin/hash update. Rebuild with
`python3 -I -B showcase/build_data.py`, inspect the diff, and rerun the integrity
check. Do not smooth away `(?)`, `[ ]`, damaged text, or open identities.

The scorer uses only our standard-library code and attributed saved text. Its
instructions and method define the scoring contract. Original recognition and
training scripts and checkpoints need their own dependency, artifact, rights,
and execution review. The reader and scorer do not reproduce that full pipeline.

Keep this showcase separate from the decoder-history PR. Preserve licenses and
credit. Do not publish full scans, private research, approval history, credentials,
or a private Site export. Prepare an explicit inventory before publishing formerly
private material. Archive image terms remain separate from text and code licenses.
