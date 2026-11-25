#!/usr/bin/env python3
"""Add canonical inventory and biological-age metadata to regularised native states.

The historical GIS age label is preserved. The canonical biological ages used
by the article are stored separately and are checked against the inventory
years. Existing arrays, including U0, are preserved unchanged. Each source NPZ
is backed up once before its first metadata modification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np


BIOLOGICAL_AGES = {
    1985: 37.0,
    1992: 44.0,
    1998: 50.0,
    2016: 68.0,
    2020: 72.0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def scalar(payload: dict[str, np.ndarray], key: str):
    return np.asarray(payload[key]).item()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.native_dir.resolve()
    report = []

    for year, biological_age in BIOLOGICAL_AGES.items():
        path = root / f"ecouves_a5_native_initial_state_{year}.npz"
        if not path.is_file():
            raise FileNotFoundError(path)

        before = sha256(path)

        with np.load(path, allow_pickle=False) as archive:
            payload = {
                key: np.array(archive[key], copy=True)
                for key in archive.files
            }

        source_year = int(
            scalar(payload, "inventory_year")
            if "inventory_year" in payload
            else scalar(payload, "year")
        )
        if source_year != year:
            raise RuntimeError(
                f"{path}: stored year={source_year}, expected {year}"
            )

        if "inventory_year" in payload:
            stored_inventory_year = int(scalar(payload, "inventory_year"))
            if stored_inventory_year != year:
                raise RuntimeError(
                    f"{path}: inventory_year={stored_inventory_year}, "
                    f"expected {year}"
                )

        if "biological_age" in payload:
            stored_age = float(scalar(payload, "biological_age"))
            if abs(stored_age - biological_age) > 1e-12:
                raise RuntimeError(
                    f"{path}: biological_age={stored_age}, "
                    f"expected {biological_age}"
                )

        changes = []

        if "inventory_year" not in payload:
            payload["inventory_year"] = np.asarray(year, dtype=np.int64)
            changes.append(f"inventory_year={year}")

        if "biological_age" not in payload:
            payload["biological_age"] = np.asarray(
                biological_age,
                dtype=np.float64,
            )
            changes.append(f"biological_age={biological_age}")

        if changes:
            backup = path.with_suffix(".npz.pre_canonical_metadata_backup")
            if not backup.exists():
                shutil.copy2(path, backup)

            gis_note = ""
            if "gis_age" in payload:
                gis_note = (
                    f"; gis_age={scalar(payload, 'gis_age')} retained as "
                    "the historical GIS age label"
                )

            payload["metadata_patch"] = np.asarray(
                ", ".join(changes)
                + " added for the article simulation protocol"
                + gis_note
            )

            tmp = path.with_suffix(".npz.tmp")
            with tmp.open("wb") as stream:
                np.savez_compressed(stream, **payload)
            tmp.replace(path)
            status = "patched"
        else:
            status = "already_complete"

        after = sha256(path)

        with np.load(path, allow_pickle=False) as check:
            report.append(
                {
                    "year": year,
                    "file": str(path),
                    "status": status,
                    "inventory_year": int(check["inventory_year"]),
                    "biological_age": float(check["biological_age"]),
                    "gis_age": (
                        int(check["gis_age"])
                        if "gis_age" in check.files
                        else None
                    ),
                    "u0_shape": list(check["U0"].shape),
                    "sha256_before": before,
                    "sha256_after": after,
                    "keys": sorted(check.files),
                }
            )

    output = root / "canonical_metadata_patch.json"
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"[OK] {output}")
    for item in report:
        print(
            f"[SUMMARY] {item['year']}: {item['status']}; "
            f"biological_age={item['biological_age']}; "
            f"gis_age={item['gis_age']}; "
            f"sha256={item['sha256_after']}"
        )


if __name__ == "__main__":
    main()
