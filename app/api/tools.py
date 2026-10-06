"""Demo support: indexed source metadata and byte-level fingerprint registry."""
import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix='/tools', tags=['Demo tools'])
ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)


@router.get('/sources')
def sources():
    try:
        chunks = json.loads((ROOT / 'data/processed/chunks.json').read_text())
        records = {}
        for chunk in chunks:
            key = chunk['source_id']
            if key not in records:
                records[key] = {field: chunk.get(field) for field in
                                ('source_id', 'source_name', 'source_url', 'document_title')}
                records[key]['chunk_count'] = 0
            records[key]['chunk_count'] += 1
        return {'sources': list(records.values())}
    except (OSError, ValueError, KeyError, TypeError):
        logger.exception('Could not read indexed sources')
        raise HTTPException(503, 'Indexed sources are unavailable.')


@router.post('/fingerprint')
async def fingerprint(audio: UploadFile = File(...), title: str = Form(..., min_length=1, max_length=200)):
    title = title.strip()
    if not title:
        raise HTTPException(422, 'A title is required.')
    if Path(audio.filename or '').suffix.lower() not in {'.mp3', '.wav', '.m4a', '.ogg', '.webm'}:
        raise HTTPException(415, 'Unsupported audio format.')
    digest = hashlib.sha256()
    size = 0
    while block := await audio.read(65536):
        size += len(block)
        if size > 25 * 1024 * 1024:
            raise HTTPException(413, 'Maximum file size is 25 MB.')
        digest.update(block)
    if not size:
        raise HTTPException(400, 'Empty file.')
    sha = digest.hexdigest()
    at = datetime.now(timezone.utc).isoformat()
    database = Path(os.environ.get('BASEERAH_REGISTRY_DB', str(ROOT / 'data/runtime/fingerprints.sqlite3')))
    try:
        database.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database, timeout=10) as db:
            db.execute('CREATE TABLE IF NOT EXISTS fingerprints (sha256 TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL, size INTEGER NOT NULL)')
            db.execute('INSERT OR IGNORE INTO fingerprints VALUES (?, ?, ?, ?)', (sha, title, at, size))
            row = db.execute('SELECT title, created_at, size FROM fingerprints WHERE sha256 = ?', (sha,)).fetchone()
        return {'sha256': sha, 'title': row[0], 'created_at': row[1], 'size': row[2], 'identity_verified': False}
    except (sqlite3.Error, OSError):
        logger.exception('Fingerprint registry failed')
        raise HTTPException(503, 'Fingerprint registry is unavailable.')


@router.post('/fingerprint/check')
async def check_fingerprint(audio: UploadFile = File(...)):
    if Path(audio.filename or '').suffix.lower() not in {'.mp3', '.wav', '.m4a', '.ogg', '.webm'}:
        raise HTTPException(415, 'Unsupported audio format.')
    digest = hashlib.sha256()
    size = 0
    while block := await audio.read(65536):
        size += len(block)
        if size > 25 * 1024 * 1024:
            raise HTTPException(413, 'Maximum file size is 25 MB.')
        digest.update(block)
    if not size:
        raise HTTPException(400, 'Empty file.')
    sha = digest.hexdigest()
    database = Path(os.environ.get('BASEERAH_REGISTRY_DB', str(ROOT / 'data/runtime/fingerprints.sqlite3')))
    if not database.exists():
        return {'sha256': sha, 'match_found': False}
    try:
        with sqlite3.connect(database, timeout=10) as db:
            row = db.execute('SELECT title, created_at FROM fingerprints WHERE sha256 = ?', (sha,)).fetchone()
        return {'sha256': sha, 'match_found': row is not None,
                'title': row[0] if row else None, 'created_at': row[1] if row else None}
    except sqlite3.Error:
        logger.exception('Fingerprint lookup failed')
        raise HTTPException(503, 'Fingerprint registry is unavailable.')
