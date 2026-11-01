# Verifier contribution instructions

Read README.md and METHOD.md before changing scoring. This package runs only our
standard-library analysis; no acquired scripts, models or images are included.
Keep the two pinned input files unchanged and preserve CREDITS.md and their
CC BY 4.0 license. A changed method needs a new method identity and evidence.

Run `python3 -B -m unittest -v test_score_saved.py`. The exhaustive tiny oracle
validates edit arithmetic; the exposed f179r regression validates saved-input
consistency. Neither establishes independent manuscript accuracy or blinding.
Test failure handling and preserve existing output files. Reports are new files.
No external contact, publishing or execution authority is granted by this file.
