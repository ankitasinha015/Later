"""Rebuild the CA bundle that lets Python talk to HTTPS APIs on this machine.

Norton Antivirus runs with HTTPS Scanning on. It intercepts every outbound TLS
connection and re-signs it with a root it generates locally. Browsers and curl
trust that root because it is in the Windows store; Python is not, because it
ships its own bundle via certifi. The result is:

    APIConnectionError: Connection error.

with the real cause two levels down in __cause__:

    CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate

The fix is a bundle holding certifi's roots plus Norton's. The important detail
is that **Norton regenerates its root periodically** (seen May and August 2026),
and a stale bundle fails in exactly the same way as no bundle at all, which
makes it look like the fix was never applied. If TLS breaks again, check the
mtime of Norton's cert first, then rerun this.

Usage:
    .venv\\Scripts\\python.exe scripts\\rebuild_ca_bundle.py

Then make sure .env contains:
    SSL_CERT_FILE=C:\\Users\\<you>\\certs\\cacert.pem

Anything that calls load_dotenv() before constructing its HTTP client picks
that up automatically. No system environment variables need changing.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

import certifi

NORTON_CERT = pathlib.Path(r"C:\ProgramData\Norton\Antivirus\wscert.pem")
OUTPUT = pathlib.Path.home() / "certs" / "cacert.pem"


def main() -> int:
    if not NORTON_CERT.exists():
        print(f"Norton cert not found at {NORTON_CERT}.")
        print("If Norton HTTPS Scanning is off, no custom bundle is needed.")
        return 1

    certifi_path = pathlib.Path(certifi.where())
    norton_mtime = dt.datetime.fromtimestamp(NORTON_CERT.stat().st_mtime)

    if OUTPUT.exists():
        bundle_mtime = dt.datetime.fromtimestamp(OUTPUT.stat().st_mtime)
        print(f"existing bundle: {bundle_mtime:%Y-%m-%d}")
        print(f"norton cert:     {norton_mtime:%Y-%m-%d}")
        if norton_mtime > bundle_mtime:
            print("-> Norton's root is newer. This is almost certainly your problem.")
        backup = OUTPUT.with_suffix(f".pem.bak-{dt.date.today():%Y%m%d}")
        backup.write_bytes(OUTPUT.read_bytes())
        print(f"backed up to {backup.name}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    merged = (
        certifi_path.read_text(encoding="utf-8").rstrip()
        + f"\n\n# Norton Web/Mail Shield Root (TLS interception), merged {dt.date.today():%Y-%m-%d}\n"
        + NORTON_CERT.read_text(encoding="utf-8").strip()
        + "\n"
    )
    OUTPUT.write_text(merged, encoding="utf-8", newline="\n")

    print(f"wrote {OUTPUT} ({merged.count('BEGIN CERTIFICATE')} certificates)")
    print(f"set SSL_CERT_FILE={OUTPUT} in .env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
