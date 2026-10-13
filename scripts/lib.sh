#!/usr/bin/env bash
# Shared guards. This file is sourced, not a standalone command.
require_idle() {
  if ! podman container exists simplfaq-api; then
    return 0
  fi
  podman exec -i simplfaq-api python - <<'PY'
import os, sqlite3, sys
from pathlib import Path
db = sqlite3.connect(Path(os.environ.get('DATA_DIR', '/data')) / 'simplfaq.db')
tables = ('runs', 'trainings')
if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='normative_jobs'").fetchone():
    tables += ('normative_jobs',)
active = sum(db.execute(f"SELECT count(*) FROM {table} WHERE status IN ('queued','running')").fetchone()[0] for table in tables)
db.close()
if active:
    print('Há tarefas de IA em andamento. Aguarde a conclusão antes de fazer backup ou atualizar.', file=sys.stderr)
    sys.exit(1)
PY
}
