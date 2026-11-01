"""Independent, standard-library scoring of saved glyph/letter artifacts.

No upstream imports, recogniser, decoder, language model, or checkpoints are used.
The format/normalisation contract is documented in METHOD.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

COMMIT = "33c854af9d1a005e2d4fbb034a61c37f3682c6f6"
METHOD = "saved-artifact-edit-v1-portable-1"
PAIR_SPEC = "an bo cp dq er fs gt hu ix ly mz".split()
LETTER_CLASS = {letter: cls for pair, cls in zip(PAIR_SPEC, "ABCDEFGHILM") for letter in pair}
LETTER_CLASS.update(v="H", j="I")
SIGNS = {"Q": "que", "K": "qui", "P": "pour", "R": "par", "&": "et"}
CLASSES = frozenset("ABCDEFGHILMQKPR&#")
TOKEN_PATTERN = re.compile(r"([^\s\[\]]+)\[([^\[\]]+)\]")


@dataclass(frozen=True)
class Row:
    number: int
    glyphs: str
    letters: str  # '#' names and '?' unknown letters are preserved until scoring.
    alternatives: tuple[dict, ...] = ()


def canonical_letters(text: str) -> str:
    return text.replace("v", "u").replace("j", "i")


def parse_gold(data: str) -> list[Row]:
    rows = []
    for source_line, line in enumerate(data.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("|")
        if len(fields) != 3:
            raise ValueError(f"Gold line {source_line}: expected exactly three fields")
        number, ranges, text = (field.strip() for field in fields)
        if not number.isdecimal() or not text:
            raise ValueError(f"Gold line {source_line}: invalid row number or empty text")
        for span in ranges.split():
            match = re.fullmatch(r"(\d+)-(\d+)", span)
            if not match or int(match[1]) >= int(match[2]):
                raise ValueError(f"Gold line {source_line}: invalid range {span!r}")
        glyphs, letters = [], []
        i = 0
        while i < len(text):
            symbol = text[i]
            if symbol.isspace():
                i += 1
                continue
            if symbol == "=":
                i += 1
                if i >= len(text) or text[i] not in CLASSES:
                    raise ValueError(f"Gold line {source_line}: invalid explicit glyph class")
                glyphs.append(text[i])
                letters.append("?")
            elif symbol in LETTER_CLASS:
                glyphs.append(LETTER_CLASS[symbol])
                letters.append(canonical_letters(symbol))
            elif symbol in SIGNS or symbol == "#":
                glyphs.append(symbol)
                letters.append(SIGNS.get(symbol, symbol))
            else:
                raise ValueError(f"Gold line {source_line}: unsupported symbol {symbol!r}")
            i += 1
        rows.append(Row(int(number), "".join(glyphs), "".join(letters)))
    validate_row_numbers(rows)
    return rows


def parse_glyph_string(data: str) -> tuple[str, tuple[dict, ...]]:
    primary, alternatives = [], []
    i = 0
    while i < len(data):
        if data[i] not in CLASSES:
            raise ValueError(f"Invalid primary glyph at offset {i}: {data!r}")
        primary.append(data[i])
        i += 1
        if i < len(data) and data[i] == "(":
            end = data.find(")", i + 1)
            if end == -1 or not data[i + 1:end] or any(c not in CLASSES for c in data[i + 1:end]):
                raise ValueError(f"Invalid alternatives at offset {i}: {data!r}")
            alternatives.append({"glyph_index": len(primary) - 1, "primary": primary[-1], "alternatives": data[i + 1:end]})
            i = end + 1
    return "".join(primary), tuple(alternatives)


def parse_machine(data: str) -> list[Row]:
    rows = []
    for source_line, line in enumerate(data.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or not fields[0].isdecimal():
            raise ValueError(f"Machine line {source_line}: expected row number and tokens")
        glyphs, letters, alternatives = [], [], []
        position = 0
        for match in TOKEN_PATTERN.finditer(fields[1]):
            if fields[1][position:match.start()].strip():
                raise ValueError(f"Machine line {source_line}: unparsed text")
            word, glyph_string = match.groups()
            if not re.fullmatch(r"[a-z]+|[ABCDEFGHILM]|#", word):
                raise ValueError(f"Machine line {source_line}: unsupported word {word!r}")
            primary, uncertain = parse_glyph_string(glyph_string)
            offset = sum(len(s) for s in glyphs)
            glyphs.append(primary)
            letters.append(canonical_letters(word))
            alternatives.extend({**a, "glyph_index": offset + a["glyph_index"], "word": word} for a in uncertain)
            position = match.end()
        if not glyphs or fields[1][position:].strip():
            raise ValueError(f"Machine line {source_line}: empty or unparsed token stream")
        rows.append(Row(int(fields[0]), "".join(glyphs), "".join(letters), tuple(alternatives)))
    validate_row_numbers(rows)
    return rows


def validate_row_numbers(rows: list[Row]) -> None:
    numbers = [row.number for row in rows]
    if not numbers or len(set(numbers)) != len(numbers) or numbers != sorted(numbers):
        raise ValueError("Rows must be nonempty, unique, and in ascending order")


def edit_alignment(reference: str, hypothesis: str) -> dict:
    """Unit-cost Levenshtein alignment; ties prefer diagonal, deletion, insertion."""
    matrix = [list(range(len(hypothesis) + 1))]
    for i, expected in enumerate(reference, 1):
        row = [i]
        previous = matrix[-1]
        for j, observed in enumerate(hypothesis, 1):
            row.append(min(previous[j - 1] + (expected != observed), previous[j] + 1, row[j - 1] + 1))
        matrix.append(row)
    i, j = len(reference), len(hypothesis)
    changes = []
    while i or j:
        if i and j and matrix[i][j] == matrix[i - 1][j - 1] + (reference[i - 1] != hypothesis[j - 1]):
            i -= 1
            j -= 1
            if reference[i] == hypothesis[j]:
                continue
            operation, r_index, h_index = "substitution", i, j
        elif i and matrix[i][j] == matrix[i - 1][j] + 1:
            i -= 1
            operation, r_index, h_index = "deletion", i, None
        else:
            j -= 1
            operation, r_index, h_index = "insertion", None, j
        changes.append({
            "operation": operation,
            "reference_index": r_index,
            "hypothesis_index": h_index,
            "reference": reference[r_index] if r_index is not None else None,
            "hypothesis": hypothesis[h_index] if h_index is not None else None,
            "reference_context": reference[max(0, i - 12):min(len(reference), i + 13)],
            "hypothesis_context": hypothesis[max(0, j - 12):min(len(hypothesis), j + 13)],
        })
    changes.reverse()
    counts = {kind: sum(e["operation"] == kind for e in changes) for kind in ("substitution", "deletion", "insertion")}
    errors = matrix[-1][-1]
    assert errors == sum(counts.values())
    return {
        "reference_length": len(reference), "hypothesis_length": len(hypothesis),
        "edit_errors": errors, "operations": counts,
        "edit_error_rate": errors / len(reference) if reference else None,
        "accuracy_percent": 100 * (1 - errors / len(reference)) if reference else None,
        "changes": changes,
    }


def score_pair(gold: list[Row], machine: list[Row]) -> dict:
    if [r.number for r in gold] != [r.number for r in machine]:
        raise ValueError("Gold and machine line IDs must match exactly")
    # Unknown alphabetic values cannot be scored without an explicit masking contract.
    if any("?" in row.letters for row in gold):
        raise ValueError("Letter scoring requires resolved gold letters; explicit =class labels need a masking contract")
    rows = []
    reference_glyphs = hypothesis_glyphs = reference_letters = hypothesis_letters = ""
    for reference, hypothesis in zip(gold, machine):
        r_letters = reference.letters.replace("#", "")
        h_letters = hypothesis.letters.replace("#", "")
        rows.append({"line": reference.number, "glyph": edit_alignment(reference.glyphs, hypothesis.glyphs),
                     "letter": edit_alignment(r_letters, h_letters), "alternatives": list(hypothesis.alternatives)})
        reference_glyphs += reference.glyphs
        hypothesis_glyphs += hypothesis.glyphs
        reference_letters += r_letters
        hypothesis_letters += h_letters
    glyph = edit_alignment(reference_glyphs, hypothesis_glyphs)
    letter = edit_alignment(reference_letters, hypothesis_letters)
    retained = edit_alignment("".join(r.letters for r in gold), "".join(r.letters for r in machine))
    # Whole-page and per-line alignments are both exposed; they need not agree on other inputs.
    for key, metric in (("glyph", glyph), ("letter", letter)):
        metric["sum_of_per_line_errors"] = sum(row[key]["edit_errors"] for row in rows)
    unresolved = [{"line": r.number, "value": ch} for r in machine for ch in r.letters if ch in "ABCDEFGHILM"]
    return {
        "glyph": glyph, "letter": letter, "per_line": rows,
        "letter_with_name_placeholders_sensitivity": retained,
        "coverage": {
            "line_count": len(gold), "line_ids": [r.number for r in gold],
            "gold_name_placeholders": sum(r.letters.count("#") for r in gold),
            "machine_name_placeholders": sum(r.letters.count("#") for r in machine),
            "machine_class_standins": unresolved,
            "machine_alternative_glyph_positions": sum(len(r.alternatives) for r in machine),
            "name_identity_accuracy": None,
        },
    }


EXPECTED = {
    "gold": {"path": "gold/f179r.txt", "bytes": 2212,
             "sha256": "7c6ddf401f28041d1746fa4cfd4ac2d0de0143d2963fbc9071d7986a816fa7e6",
             "git_blob_sha1": "b44fa2e4ffb5335e8fb7c024eab860f14051a057"},
    "machine": {"path": "evidence/f179r_machine_blind.txt", "bytes": 3793,
                "sha256": "3809eb14cf0e47384376ad972aa192aead79cc50656529ba8085d72a79f0ee7b",
                "git_blob_sha1": "b59d941b40d4b1d6bac08fb47e59bea018f383c7"},
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def check_manifest(data: bytes) -> dict:
    manifest = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(manifest, dict) or manifest.get("schema") != "desportes-saved-inputs-v1" or manifest.get("commit") != COMMIT:
        raise ValueError("Manifest must identify the pinned Desportes input contract")
    if not isinstance(manifest.get("inputs"), dict) or set(manifest["inputs"]) != set(EXPECTED):
        raise ValueError("Manifest must contain exactly gold and machine records")
    for role, expected in EXPECTED.items():
        record = manifest["inputs"][role]
        if not isinstance(record, dict) or any(record.get(k) != v for k, v in expected.items()) or type(record.get("bytes")) is not int:
            raise ValueError(f"Manifest does not match the pinned {role} record")
        expected_url = f"https://raw.githubusercontent.com/pangoleen/desportes-1593/{COMMIT}/{expected['path']}"
        if record.get("url") != expected_url:
            raise ValueError(f"Manifest source URL mismatch: {role}")
    return manifest


def check_snapshot(role: str, data: bytes) -> str:
    expected = EXPECTED[role]
    digest = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if digest != expected["sha256"] or blob != expected["git_blob_sha1"] or len(data) != expected["bytes"]:
        raise ValueError(f"Pinned input hash/size mismatch: {role}")
    return data.decode("utf-8")


def make_report(gold_data: bytes, machine_data: bytes, manifest_data: bytes) -> dict:
    check_manifest(manifest_data)
    gold_text = check_snapshot("gold", gold_data)
    machine_text = check_snapshot("machine", machine_data)
    results = score_pair(parse_gold(gold_text), parse_machine(machine_text))
    if results["coverage"]["line_ids"] != list(range(21)):
        raise ValueError("Pinned page must contain all 21 rows")
    module_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    identity = {"method": METHOD, "commit": COMMIT,
                "inputs_sha256": {role: expected["sha256"] for role, expected in EXPECTED.items()},
                "manifest_sha256": hashlib.sha256(manifest_data).hexdigest(),
                "scorer_sha256": module_hash}
    return {**identity, "run_id": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20],
            "schema": "desportes-saved-report-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(), "platform": platform.platform(),
            "scope": "Saved-artifact consistency only; exposed model-assisted reference, no image inference, independent expert accuracy or proof of blinding",
            "results": results}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--machine", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Create a new JSON report; existing files are refused")
    args = parser.parse_args(argv)
    try:
        # Each input is read once. Hash verification and parsing use the same snapshot.
        report = make_report(args.gold.read_bytes(), args.machine.read_bytes(), args.manifest.read_bytes())
        payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as target:
                target.write(payload)
            glyph, letter = report["results"]["glyph"], report["results"]["letter"]
            print(f"{report['run_id']}: glyph {glyph['edit_errors']}/{glyph['reference_length']}; "
                  f"letter {letter['edit_errors']}/{letter['reference_length']}; saved-artifact consistency")
        else:
            print(payload, end="")
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        parser.exit(1, f"Verification failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
