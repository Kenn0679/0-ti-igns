import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA_VERSION = 1
HASH_CHUNK_SIZE = 1024 * 1024


@dataclass
class ManifestEntry:
    hash: str
    document_name: str
    updated_at: str


@dataclass
class DeltaResult:
    added: list[Path] = field(default_factory=list)
    updated: list[Path] = field(default_factory=list)
    unchanged: list[Path] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    hashes: dict[str, str] = field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_file_hash(file_path: Path) -> str:
    digest = hashlib.sha256()

    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, ManifestEntry]:
    if not manifest_path.exists():
        logger.info("No existing manifest found at %s; treating all files as new", manifest_path)
        return {}

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.warning(
            "Failed to read manifest at %s (%s); treating all files as new",
            manifest_path,
            error,
        )
        return {}

    entries: dict[str, ManifestEntry] = {}
    for name, data in raw.get("files", {}).items():
        try:
            entries[name] = ManifestEntry(
                hash=data["hash"],
                document_name=data["document_name"],
                updated_at=data.get("updated_at", ""),
            )
        except KeyError:
            logger.warning("Skipping malformed manifest entry for %s", name)

    return entries


def save_manifest(manifest_path: Path, entries: dict[str, ManifestEntry], store_name: str) -> None:
    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "store_name": store_name,
        "last_run": utc_now_iso(),
        "files": {
            name: {
                "hash": entry.hash,
                "document_name": entry.document_name,
                "updated_at": entry.updated_at,
            }
            for name, entry in entries.items()
        },
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = manifest_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(manifest_path)

    logger.info("Manifest persisted: %s (%d tracked file(s))", manifest_path, len(entries))


def compute_delta(current_files: list[Path], manifest: dict[str, ManifestEntry]) -> DeltaResult:
    result = DeltaResult()
    current_names = {file_path.name for file_path in current_files}

    for file_path in current_files:
        current_hash = compute_file_hash(file_path)
        result.hashes[file_path.name] = current_hash

        previous = manifest.get(file_path.name)
        if previous is None:
            result.added.append(file_path)
        elif previous.hash != current_hash:
            result.updated.append(file_path)
        else:
            result.unchanged.append(file_path)

    for tracked_name in manifest:
        if tracked_name not in current_names:
            result.deleted.append(tracked_name)

    return result
