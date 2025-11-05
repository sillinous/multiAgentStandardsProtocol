#!/usr/bin/env python3
"""Scan repositories for candidate agent projects.

This script is deliberately conservative and read-only. It walks a
configurable root directory, scores folders based on agent-related
indicators (files, directory names, keywords), and writes a discovery
report JSON file under the integration hub.

See `design/agent-discovery-spec.md` for requirements.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

EXCLUDE_DEFAULT = {".git", "node_modules", "__pycache__", ".venv", ".pytest_cache", "build", "dist"}
FILE_INDICATORS = {
    "capabilities.json": 3,
    "manifest.json": 2,
    "capabilities.schema.json": 2,
    "agent.py": 3,
    "main.py": 1,
    "pyproject.toml": 1,
    "package.json": 1,
    "README.md": 1,
    "README": 1,
}
DIR_INDICATORS = {
    "agentx": 3,
    "agents": 2,
    "agent_ecosystem": 2,
    "mcp": 1,
    "runtime": 1,
    "orchestrator": 2,
    "adapter": 1,
    "adapters": 1,
}
KEYWORD_INDICATORS = {
    "@runtime_checkable": 1,
    "class Agent": 1,
    "CapabilityToken": 2,
    "IntentContract": 2,
    "cap-supervisor": 1,
    "AgentX": 1,
    "MCP": 1,
    "capabilities": 1,
}
TEXT_EXTENSIONS = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".txt"}

KNOWN_PATH_PATTERNS = {
    'agent-zero': 'agent-zero',
    'ApiaryFundingAndResearch': 'ApiaryFundingAndResearch',
    'nexus-workforce': 'nexus-workforce',
    'agentx/examples': 'agentx/examples',
}


@dataclass
class Indicator:
    type: str
    value: str


@dataclass
class Candidate:
    path: str
    score: int
    indicators: list[Indicator]
    last_modified: str
    status: str
    notes: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover agent candidates in a repository tree")
    parser.add_argument("root", nargs="?", default="C:/GitHub", help="Root directory to scan (default: C:/GitHub)")
    parser.add_argument("--output-dir", default="knowledge/discovery-reports", help="Where to write discovery reports (relative or absolute path)")
    parser.add_argument("--known-manifest", default="manifests/reference/README.md", help="Manifest reference table to mark known agents")
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum directory depth to scan")
    parser.add_argument("--threshold", type=int, default=3, help="Minimum score to include a candidate")
    parser.add_argument("--exclude", nargs="*", default=[], help="Additional directories to exclude")
    parser.add_argument("--markdown", action="store_true", help="Also emit a Markdown summary alongside JSON")
    return parser.parse_args()


def load_known_agents(manifest_file: Path) -> set[str]:
    if not manifest_file.exists():
        return set()
    pattern = re.compile(r"`([^`]+)`")
    known: set[str] = set()
    for line in manifest_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.search(line)
        if match:
            known.add(match.group(1).strip())
    return known


def iter_dirs(root: Path, max_depth: int) -> Iterable[tuple[Path, list[str], list[str]]]:
    root = root.resolve()
    for current_root, dirs, files in os.walk(root):
        current_path = Path(current_root)
        depth = len(current_path.relative_to(root).parts)
        if depth > max_depth:
            dirs[:] = []
            continue
        yield current_path, dirs, files


def evaluate_directory(path: Path, files: list[str], dirs: list[str], exclude: set[str], max_files: int = 5) -> tuple[int, list[Indicator]]:
    score = 0
    found: list[Indicator] = []

    for file_name in files:
        weight = FILE_INDICATORS.get(file_name)
        if weight:
            score += weight
            found.append(Indicator(type="file", value=file_name))
    for dir_name in list(dirs):
        if dir_name in exclude:
            continue
        weight = DIR_INDICATORS.get(dir_name)
        if weight:
            score += weight
            found.append(Indicator(type="dir", value=dir_name))

    # Keyword scan (limited)
    scanned = 0
    for file_name in files:
        if scanned >= max_files:
            break
        suffix = Path(file_name).suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            continue
        file_path = path / file_name
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for keyword, weight in KEYWORD_INDICATORS.items():
            if keyword in content:
                score += weight
                found.append(Indicator(type="keyword", value=f"{keyword} ({file_name})"))
        scanned += 1

    return score, found


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    known_agents = load_known_agents(Path(args.known_manifest))
    known_patterns = set(KNOWN_PATH_PATTERNS.values())
    exclude = EXCLUDE_DEFAULT | set(args.exclude)

    candidates: list[Candidate] = []
    total_scanned = 0

    for current_path, dirs, files in iter_dirs(root, args.max_depth):
        dirs[:] = [d for d in dirs if d not in exclude]
        total_scanned += 1
        score, indicators = evaluate_directory(current_path, files, dirs, exclude)
        if score >= args.threshold:
            status = "known" if (any(k in str(current_path) for k in known_agents) or any(pattern in str(current_path) for pattern in known_patterns)) else "new"
            last_modified_ts = max((current_path / item).stat().st_mtime for item in files) if files else current_path.stat().st_mtime
            last_modified = datetime.fromtimestamp(last_modified_ts, tz=timezone.utc).isoformat()
            candidates.append(
                Candidate(
                    path=str(current_path),
                    score=score,
                    indicators=indicators,
                    last_modified=last_modified,
                    status=status,
                )
            )

    generated_at = datetime.now(timezone.utc).isoformat()
    report = {
        "generated_at": generated_at,
        "root": str(root),
        "summary": {
            "total_scanned": total_scanned,
            "candidates_found": len(candidates),
            "known_agents": sum(1 for c in candidates if c.status == "known"),
            "new_candidates": sum(1 for c in candidates if c.status == "new"),
        },
        "candidates": [
            {
                "path": c.path,
                "score": c.score,
                "indicators": [asdict(ind) for ind in c.indicators],
                "last_modified": c.last_modified,
                "status": c.status,
                "notes": c.notes,
            }
            for c in sorted(candidates, key=lambda cand: cand.score, reverse=True)
        ],
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"discovery-report-{timestamp}.json"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"Wrote discovery report: {json_path}")

    if args.markdown:
        md_lines = ["# Agent Discovery Report", "", f"Generated at: {generated_at}", "", "## Summary", "", f"- Total directories scanned: {total_scanned}", f"- Candidates found: {len(candidates)}", f"- Known agents: {report['summary']['known_agents']}" , f"- New candidates: {report['summary']['new_candidates']}", "", "## Candidates", ""]
        for cand in sorted(candidates, key=lambda c: c.score, reverse=True):
            md_lines.append(f"- **{cand.path}** (score {cand.score}, status {cand.status})")
            for ind in cand.indicators:
                md_lines.append(f"  - {ind.type}: {ind.value}")
        md_path = output_dir / f"discovery-report-{timestamp}.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"Wrote markdown summary: {md_path}")


if __name__ == "__main__":
    main()
