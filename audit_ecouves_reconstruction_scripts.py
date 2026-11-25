#!/usr/bin/env python3
"""Locate the scripts and metadata used to reconstruct Ecouves target states.

Run from the PyDynamicForest repository root. The script scans the repository
and the local ECOUVES_NUM archive, then writes one compact Markdown audit file.
It does not modify any source or result file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py", ".ipynb", ".qmd", ".md", ".txt", ".json", ".yaml", ".yml",
    ".toml", ".csv", ".tex", ".sh",
}

KEY_PATTERNS = {
    "target-state construction": re.compile(
        r"target[_ -]?state|solver[_ -]?compatibility|native[_ -]?initial[_ -]?state",
        re.I,
    ),
    "Ecouves A5": re.compile(r"ecouves|écouves|\bA5\b", re.I),
    "height reconstruction": re.compile(
        r"height[_ -]?dbh|hauteur[_ -]?diam|allometr|allométr|hauteur_ech|residual",
        re.I,
    ),
    "selected years": re.compile(r"1985|1992|1998|2016|2020"),
    "joint distributions or marginals": re.compile(
        r"joint[_ -]?(state|distribution)|marginal|contour|heatmap|rho_HD|sigma_D",
        re.I,
    ),
    "NPZ state writing": re.compile(r"savez|\.npz|native_nodal_mass|quadrature_weights", re.I),
}

EXCLUDED_PARTS = {
    ".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache",
    "site-packages", "node_modules",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def readable_file(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.lower() in TEXT_EXTENSIONS
        and not any(part in EXCLUDED_PARTS for part in path.parts)
        and path.stat().st_size <= 5_000_000
    )


def safe_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding, errors="strict")
        except UnicodeError:
            pass
    return ""


def scan(root: Path, label: str) -> list[dict]:
    results = []
    if not root.exists():
        return results

    for path in root.rglob("*"):
        if not readable_file(path):
            continue
        text = safe_text(path)
        if not text:
            continue

        categories = []
        snippets = []
        for category, pattern in KEY_PATTERNS.items():
            matches = list(pattern.finditer(text))
            if matches:
                categories.append(category)
                for match in matches[:2]:
                    line_no = text.count("\n", 0, match.start()) + 1
                    raw_line = text.splitlines()[line_no - 1].strip()
                    if raw_line and len(raw_line) <= 260:
                        snippets.append((line_no, raw_line))

        if not categories:
            continue

        # Stronger score for combinations that are likely to construct states.
        score = len(categories)
        if "Ecouves A5" in categories and "NPZ state writing" in categories:
            score += 3
        if "target-state construction" in categories and "height reconstruction" in categories:
            score += 3
        if path.suffix.lower() == ".py":
            score += 1

        results.append(
            {
                "source": label,
                "path": path,
                "relative": path.relative_to(root),
                "score": score,
                "categories": categories,
                "snippets": list(dict.fromkeys(snippets))[:8],
                "sha256": sha256(path),
                "size": path.stat().st_size,
            }
        )

    return sorted(results, key=lambda item: (-item["score"], str(item["relative"])))


def read_json_metadata(archive_root: Path) -> list[dict]:
    records = []
    if not archive_root.exists():
        return records

    names = {
        "reproducibility.json", "configuration.json", "figure_manifest.json",
        "ecouves_a5_frozen_1985_2020_metadata.json",
    }
    for path in archive_root.rglob("*.json"):
        if path.name not in names:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue

        selected = {}
        for key in (
            "purpose", "scenario", "git_commit", "command", "runner_path",
            "initial_state_path", "target_state_dir", "output_dir",
            "height_provider_1985", "height_values_1985_are_measured",
            "residual_height_variability_1985_simulated",
        ):
            if key in data:
                selected[key] = data[key]

        if selected:
            records.append(
                {
                    "path": path,
                    "relative": path.relative_to(archive_root),
                    "values": selected,
                }
            )
    return records


def render_candidate(item: dict) -> list[str]:
    lines = [
        f"### `{item['relative']}`",
        "",
        f"- Source : **{item['source']}**",
        f"- Score de pertinence : **{item['score']}**",
        f"- Catégories : {', '.join(item['categories'])}",
        f"- Taille : {item['size']} octets",
        f"- SHA-256 : `{item['sha256']}`",
    ]
    if item["snippets"]:
        lines += ["- Extraits repérés :"]
        for line_no, snippet in item["snippets"]:
            escaped = snippet.replace("`", "'")
            lines.append(f"  - L{line_no}: `{escaped}`")
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path.home() / "Downloads" / "ECOUVES_NUM_2026-11-18",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("audit_ecouves_reconstruction_scripts.md"),
    )
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    repo = args.repo.resolve()
    archive = args.archive.resolve()
    output = args.output.resolve()

    candidates = scan(repo, "dépôt PyDynamicForest") + scan(archive, "archive locale")
    candidates = sorted(candidates, key=lambda item: (-item["score"], item["source"], str(item["relative"])))
    metadata = read_json_metadata(archive)

    likely = [item for item in candidates if item["score"] >= 6][: args.top]
    secondary = [item for item in candidates if 3 <= item["score"] < 6][:15]

    lines = [
        "# Audit des scripts de reconstruction Écouves A5",
        "",
        "## Périmètre",
        "",
        f"- Dépôt : `{repo}`",
        f"- Archive locale : `{archive}`",
        "- Recherche en lecture seule dans les scripts, métadonnées, rapports et manifestes.",
        "- Objectif : retrouver la chaîne ayant construit les états cibles 1985, 1992, 1998, 2016 et 2020 ainsi que les figures jointes et marginales.",
        "",
        "## Verdict automatique",
        "",
    ]

    if likely:
        lines.append(f"**{len(likely)} fichiers fortement candidats ont été trouvés.**")
    else:
        lines.append("**Aucun fichier fortement candidat n'a été trouvé.** Les métadonnées ci-dessous restent à examiner.")

    lines += ["", "## Métadonnées de reproductibilité", ""]
    if not metadata:
        lines.append("Aucune métadonnée ciblée trouvée.")
    else:
        for record in metadata:
            lines.append(f"### `{record['relative']}`")
            lines.append("")
            for key, value in record["values"].items():
                lines.append(f"- `{key}` : `{value}`")
            lines.append("")

    lines += ["## Fichiers fortement candidats", ""]
    if likely:
        for item in likely:
            lines.extend(render_candidate(item))
    else:
        lines.append("Aucun.")

    lines += ["## Fichiers secondaires", ""]
    if secondary:
        for item in secondary:
            lines.extend(render_candidate(item))
    else:
        lines.append("Aucun.")

    lines += [
        "## Recherche de noms de sorties déjà produites",
        "",
    ]
    output_names = (
        "ecouves_a5_native_initial_state_1985.npz",
        "ecouves_a5_native_initial_state_1992.npz",
        "ecouves_a5_native_initial_state_1998.npz",
        "ecouves_a5_native_initial_state_2016.npz",
        "ecouves_a5_native_initial_state_2020.npz",
        "figure_1_joint_states.png",
        "figure_2_stand_trajectories.png",
        "figure_3_structural_diagnostics.png",
    )
    for name in output_names:
        paths = list(repo.rglob(name)) + list(archive.rglob(name))
        if paths:
            for path in paths:
                lines.append(f"- `{name}` : `{path}`")
        else:
            lines.append(f"- `{name}` : non trouvé")

    lines += [
        "",
        "## Étape suivante",
        "",
        "Transmettre ce fichier d'audit. Les trois à cinq candidats principaux pourront alors être inspectés précisément avant toute nouvelle écriture de code.",
    ]

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] {output}")
    print(f"[SUMMARY] strong_candidates={len(likely)} secondary_candidates={len(secondary)} metadata_files={len(metadata)}")


if __name__ == "__main__":
    main()
