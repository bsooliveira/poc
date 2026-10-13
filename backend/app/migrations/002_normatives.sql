CREATE TABLE IF NOT EXISTS normative_documents (
  id TEXT PRIMARY KEY, system TEXT NOT NULL CHECK(system IN ('camara','depositaria')),
  title TEXT NOT NULL, listing_url TEXT NOT NULL, url TEXT NOT NULL,
  sha256 TEXT NOT NULL, version TEXT NOT NULL, effective_from TEXT NOT NULL,
  verified_at TEXT NOT NULL, ingested_at TEXT NOT NULL, status TEXT NOT NULL,
  path TEXT NOT NULL, page_count INTEGER NOT NULL, chunk_count INTEGER NOT NULL,
  origin TEXT NOT NULL DEFAULT 'official', UNIQUE(system,sha256));
CREATE UNIQUE INDEX IF NOT EXISTS one_active_manual ON normative_documents(system) WHERE status='active';
CREATE TABLE IF NOT EXISTS normative_chunks (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES normative_documents(id),
  text TEXT NOT NULL, location TEXT NOT NULL, section TEXT NOT NULL,
  page INTEGER NOT NULL, vector TEXT NOT NULL, embedding_model TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS normative_chunk_document ON normative_chunks(document_id);
CREATE TABLE IF NOT EXISTS normative_jobs (
  id TEXT PRIMARY KEY, actor TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
  finished_at TEXT, report TEXT, error TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS one_normative_job ON normative_jobs(status) WHERE status IN ('queued','running');
ALTER TABLE chunks ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}';
PRAGMA user_version=2;
