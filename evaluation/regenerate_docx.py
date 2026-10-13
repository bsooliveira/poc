"""Exercise the current exporter against a previously collected fictitious event."""
import json
import sys
from pathlib import Path

from app.output import document_bytes

event = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
Path(sys.argv[2]).write_bytes(document_bytes(event))
print("DOCX generated from existing fictitious fixture")
