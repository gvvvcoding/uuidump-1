#!/usr/bin/env python3
"""Keep UUIDs whose 8-character prefix is absent from the ZIP dump."""

import argparse
import sys
import uuid
import zipfile
from pathlib import Path


DUMP_MEMBER = "truncated_uuids.txt"


def main():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Compare UUIDs with the truncated UUID prefixes in a ZIP dump."
    )
    parser.add_argument("--input", type=Path, default=script_dir / "uuid.txt")
    parser.add_argument(
        "--dump", type=Path, default=script_dir / "labynet_uuid_dump.zip"
    )
    parser.add_argument("--output", type=Path, default=script_dir / "valid.txt")
    args = parser.parse_args()

    uuids = []
    seen_uuids = set()
    try:
        with args.input.open(encoding="utf-8") as input_file:
            for line_number, line in enumerate(input_file, start=1):
                value = line.strip()
                if not value:
                    continue
                try:
                    normalized = str(uuid.UUID(value))
                except ValueError:
                    raise ValueError(
                        f"Ungültige UUID in Zeile {line_number}: {value}"
                    ) from None
                if normalized not in seen_uuids:
                    seen_uuids.add(normalized)
                    uuids.append((normalized, normalized[:8].encode("ascii")))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    candidates = sorted(uuids, key=lambda item: item[1])
    candidate_index = 0
    written_count = 0
    try:
        with args.output.open("w", encoding="utf-8") as output_file:
            if candidates:
                with zipfile.ZipFile(args.dump) as archive:
                    with archive.open(DUMP_MEMBER) as dump_file:
                        for line in dump_file:
                            dump_prefix = line[:8]
                            while (
                                candidate_index < len(candidates)
                                and candidates[candidate_index][1] < dump_prefix
                            ):
                                output_file.write(f"{candidates[candidate_index][0]}\n")
                                candidate_index += 1
                                written_count += 1
                            while (
                                candidate_index < len(candidates)
                                and candidates[candidate_index][1] == dump_prefix
                            ):
                                candidate_index += 1
                            output_file.flush()

                        while candidate_index < len(candidates):
                            output_file.write(f"{candidates[candidate_index][0]}\n")
                            candidate_index += 1
                            written_count += 1
                            output_file.flush()
    except (OSError, KeyError, zipfile.BadZipFile) as error:
        print(f"Abgleich fehlgeschlagen: {error}", file=sys.stderr)
        return 1

    print(f"Abgleich abgeschlossen: {written_count} neue UUID(s) in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())