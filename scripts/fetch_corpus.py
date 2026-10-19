"""Download inert pinned metadata only; never import upstream Python or run servers."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

REVISION = "295fe37cd972ea9aa1b48578b2d7bcc40a72ee12"
PATH = "Website/mcpso_servers_cleaned.json"
URL = "https://raw.githubusercontent.com/Snakinya/MCPCorpus/" + REVISION + "/" + PATH

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/raw")
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "mcpcorpus_servers.json"
    with urlopen(Request(URL, headers={"User-Agent": "MCPShield-research"}), timeout=60) as response:
        raw = response.read(80_000_001)
    if len(raw) > 80_000_000:
        raise ValueError("Corpus exceeds download limit")
    entries = json.loads(raw)
    if not isinstance(entries, list):
        raise ValueError("Expected JSON array")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != "cc14fc4fe5c68b73e77cbaa3e64fc2b58616a8e61d0e96d92b8fd861702b9e20":
        raise ValueError("Pinned corpus checksum mismatch")
    if destination.exists() and destination.read_bytes() != raw:
        raise ValueError("Refusing to overwrite a different snapshot")
    destination.write_bytes(raw)
    manifest = {"repository": "https://github.com/Snakinya/MCPCorpus", "revision": REVISION,
                "path": PATH, "url": URL, "sha256": digest, "bytes": len(raw), "records": len(entries),
                "label_status": "UNLABELED_METADATA", "license": "No repository license file found at pinned revision; verify reuse terms before redistribution."}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
