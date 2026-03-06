from __future__ import annotations

import argparse
import glob
import shutil
import tarfile
import zipfile
from pathlib import Path

from .service import HistoryInspector


def _extract_archive(archive: Path, dest_dir: Path) -> Path:
    target = dest_dir / archive.stem
    suffix = archive.suffix.lower()
    if archive.suffixes[-2:] == [".tar", ".gz"] or suffix == ".tgz":
        target = dest_dir / archive.name.replace(".tar.gz", "").replace(".tgz", "")
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "r:gz") as handle:
            handle.extractall(target)
        return target
    if suffix == ".zip":
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "r") as handle:
            handle.extractall(target)
        return target
    raise ValueError(f"Unsupported archive format: {archive}")


def _find_watch_history(root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob("watch-history.json"):
        matches.append(path)
    for path in root.rglob("watch-history.csv"):
        matches.append(path)
    for path in root.rglob("watch-history.html"):
        matches.append(path)
    for path in root.rglob("Wiedergabeverlauf.html"):
        matches.append(path)
    return matches


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unzip Google Takeout archives and import YouTube watch history."
    )
    parser.add_argument(
        "archives",
        nargs="+",
        help="Archive glob(s), e.g. /Users/kamir/Downloads/takeout-2026*.zip",
    )
    parser.add_argument(
        "--db-path",
        default="data/app.db",
        help="SQLite DB path (default: data/app.db)",
    )
    parser.add_argument(
        "--client-secret",
        default="client_secret.json",
        help="OAuth client secret path (default: client_secret.json)",
    )
    parser.add_argument(
        "--extract-dir",
        default="data/takeout_extract",
        help="Extraction directory (default: data/takeout_extract)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove extraction directory before importing.",
    )
    parser.add_argument(
        "--fetch-metadata",
        action="store_true",
        help="Fetch video metadata via YouTube API if OAuth token exists.",
    )
    args = parser.parse_args(argv)

    extract_dir = Path(args.extract_dir)
    if args.clean and extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    archive_paths: list[Path] = []
    for pattern in args.archives:
        archive_paths.extend(Path(p) for p in glob.glob(pattern))

    if not archive_paths:
        print("No archives found.")
        return 1

    history_files: list[Path] = []
    extracted_roots: list[Path] = []
    for archive in archive_paths:
        if archive.suffix.lower() in {".json", ".csv", ".html"}:
            history_files.append(archive)
            continue
        print(f"Extracting {archive} ...")
        extracted_roots.append(_extract_archive(archive, extract_dir))

    for root in extracted_roots:
        history_files.append(root)

    if not history_files:
        print("No watch-history.json/csv found.")
        return 1

    inspector = HistoryInspector(
        db_path=args.db_path,
        client_secrets_path=args.client_secret,
    )

    total_imported = 0
    for history_file in history_files:
        print(f"Importing {history_file} ...")
        result = inspector.import_takeout_bundle(
            str(history_file),
            fetch_metadata=args.fetch_metadata,
        )
        if isinstance(result, dict) and "synced" in result:
            print(
                f"Imported: {result['synced']} items, metadata: {result['metadata_synced']}"
            )
            total_imported += result["synced"]
        else:
            print(f"Imported totals: {result}")
            total_imported += result.get("watch_history", 0)

    inspector.close()
    print(f"Done. Total imported: {total_imported}")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
