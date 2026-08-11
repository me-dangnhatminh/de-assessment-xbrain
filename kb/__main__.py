"""CLI entry point for the version-aware knowledge base pipeline.

Subcommands
-----------
inventory   Discover and display the document inventory.
build       Build the SQLite FTS5 index and write chunks.jsonl.
search      Query the FTS5 index with current-first or all-versions mode.
eval        Run all 10 predeclared evaluation cases and write JSON + Markdown results.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_DIR = REPOSITORY_ROOT / "docs/onboard/datapack/data/docs"
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "data/evidence/phase2"


class KBError(ValueError):
    """An actionable error during KB pipeline execution."""


def cmd_inventory(arguments: argparse.Namespace) -> int:
    """List all discovered documents with doc_id, version, and SHA-256."""
    from kb.inventory import inventory_documents

    docs_dir = Path(arguments.docs_dir).expanduser().resolve()
    try:
        docs = inventory_documents(docs_dir)
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"{'doc_id':<12} {'version':<10} {'effective_date':<15} {'sha256[:12]':<14} source")
    print("-" * 80)
    for doc in docs:
        sha_prefix = doc.sha256[:12]
        ver = doc.version or "(none)"
        eff = doc.effective_date or "(none)"
        print(f"{doc.doc_id:<12} {ver:<10} {eff:<15} {sha_prefix:<14} {Path(doc.source_path).name}")
    return 0


def cmd_build(arguments: argparse.Namespace) -> int:
    """Build the FTS5 index and write chunks.jsonl from the docs directory."""
    from kb.chunking import chunk_document
    from kb.index import build_index
    from kb.inventory import inventory_documents
    from kb.versioning import resolve_versions

    docs_dir = Path(arguments.docs_dir).expanduser().resolve()
    output_dir = Path(arguments.output_dir).expanduser().resolve()

    try:
        docs = inventory_documents(docs_dir)
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))

    all_chunks = resolve_versions(docs, all_chunks)
    build_index(all_chunks, output_dir)

    current_count = sum(1 for c in all_chunks if c.is_current)
    superseded_count = len(all_chunks) - current_count
    print(
        f"build complete: {len(docs)} documents, {len(all_chunks)} chunks "
        f"({current_count} current, {superseded_count} superseded)"
    )
    print(f"  index: {output_dir / 'index.sqlite'}")
    print(f"  chunks: {output_dir / 'chunks.jsonl'}")
    return 0


def cmd_search(arguments: argparse.Namespace) -> int:
    """Search the FTS5 index and print ranked results."""
    from kb.search import search_all, search_current

    db_path = Path(arguments.db).expanduser().resolve()
    if not db_path.is_file():
        print(f"error: index not found: {db_path}", file=sys.stderr)
        return 2

    query = arguments.query
    mode = arguments.mode
    top_k = arguments.top_k

    if mode == "current":
        results = search_current(db_path, query, top_k=top_k)
    else:
        results = search_all(db_path, query, top_k=top_k)

    if not results:
        print(f"No results for query: {query!r} (mode={mode})")
        return 0

    label = "current versions only" if mode == "current" else "all versions"
    print(f"Results for {query!r} — {label} (top {len(results)})")
    print("=" * 72)
    for rank, result in enumerate(results, 1):
        current_label = "[CURRENT]" if result.is_current else "[SUPERSEDED]"
        ver_label = f"v{result.version}" if result.version else ""
        eff_label = result.effective_date or ""
        print(f"{rank}. {result.doc_id} {ver_label} {eff_label} {current_label} § {result.section}")
        print(f"   chunk_id: {result.chunk_id}  bm25: {result.bm25_score:.4f}")
        snippet = result.content[:200].replace("\n", " ")
        print(f"   {snippet}...")
        print()
    return 0


def cmd_eval(arguments: argparse.Namespace) -> int:
    """Run all 10 predeclared evaluation cases and write JSON + Markdown evidence."""
    from kb.eval_cases import EVAL_CASES
    from kb.eval_report import render_eval_json, render_eval_report
    from kb.eval_runner import run_evaluation

    db_path = Path(arguments.db).expanduser().resolve()
    output_dir = Path(arguments.output_dir).expanduser().resolve()
    top_k = arguments.top_k

    if not db_path.is_file():
        print(f"error: index not found: {db_path}", file=sys.stderr)
        return 2

    results = run_evaluation(db_path, EVAL_CASES, top_k=top_k)

    json_path = render_eval_json(results, db_path, output_dir, top_k)
    md_path = render_eval_report(results, db_path, output_dir, top_k)

    pass_count = sum(1 for r in results if r.retrieval_hit_score == "pass")
    partial_count = sum(1 for r in results if r.retrieval_hit_score == "partial")
    fail_count = sum(1 for r in results if r.retrieval_hit_score == "fail")

    print(
        f"eval complete: {len(results)} cases — "
        f"{pass_count} pass, {partial_count} partial, {fail_count} fail"
    )
    print(f"  json:     {json_path}")
    print(f"  report:   {md_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the knowledge base CLI."""
    parser = argparse.ArgumentParser(prog="python -m kb")
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    # --- inventory ---
    inv_parser = subcommands.add_parser("inventory", help="list discovered documents")
    inv_parser.add_argument(
        "--docs-dir", default=str(DEFAULT_DOCS_DIR), help="path to docs directory"
    )
    inv_parser.set_defaults(handler=cmd_inventory)

    # --- build ---
    build_parser_ = subcommands.add_parser("build", help="build FTS5 index from documents")
    build_parser_.add_argument(
        "--docs-dir", default=str(DEFAULT_DOCS_DIR), help="path to docs directory"
    )
    build_parser_.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="directory for index.sqlite and chunks.jsonl",
    )
    build_parser_.set_defaults(handler=cmd_build)

    # --- search ---
    search_parser = subcommands.add_parser("search", help="query the FTS5 index")
    search_parser.add_argument("--db", required=True, help="path to index.sqlite")
    search_parser.add_argument("--query", required=True, help="search query text")
    search_parser.add_argument(
        "--mode",
        choices=["current", "all"],
        default="current",
        help="current (default) or all versions",
    )
    search_parser.add_argument("--top-k", type=int, default=5, help="number of results to return")
    search_parser.set_defaults(handler=cmd_search)

    # --- eval ---
    eval_parser = subcommands.add_parser(
        "eval", help="run predeclared evaluation cases and write JSON + Markdown report"
    )
    eval_parser.add_argument(
        "--db",
        default=str(DEFAULT_OUTPUT_DIR / "index.sqlite"),
        help="path to index.sqlite (default: data/evidence/phase2/index.sqlite)",
    )
    eval_parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="directory for eval_results.json and eval_report.md",
    )
    eval_parser.add_argument(
        "--top-k", type=int, default=5, help="number of results to retrieve per case (default 5)"
    )
    eval_parser.set_defaults(handler=cmd_eval)

    return parser


def main(arguments: list[str] | None = None) -> int:
    """Run a KB subcommand."""
    parser = build_parser()
    parsed = parser.parse_args(arguments)
    try:
        return parsed.handler(parsed)
    except KBError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
