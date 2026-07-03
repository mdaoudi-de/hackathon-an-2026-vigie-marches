"""Utilitaires partagés : session HTTP, téléchargements, DuckDB et traçabilité.

Chaque ingestion enregistre une ligne dans la table `_provenance`
(source, URL, date de collecte, nombre de lignes) : c'est le socle de la
traçabilité exigée par le sujet — tout signal du score de risque doit pouvoir
être remonté jusqu'à sa source et sa date de collecte.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import requests
from requests.adapters import HTTPAdapter, Retry
from tqdm import tqdm

from ingestion import config


def get_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "HEAD"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({"User-Agent": config.USER_AGENT})
    return session


def download(session: requests.Session, url: str, dest: Path, desc: str) -> Path:
    """Télécharge `url` vers `dest` en streaming avec barre de progression."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, stream=True, timeout=120, allow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f, tqdm(
            total=total or None, unit="B", unit_scale=True, desc=desc
        ) as bar:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                bar.update(len(chunk))
        tmp.replace(dest)
    return dest


def write_jsonl(records: list[dict], dest: Path) -> Path:
    """Écrit les enregistrements bruts en JSON Lines (conservés dans data/raw/ pour audit)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return dest


def strip_xssi(text: str) -> str:
    """Retire la garde anti-JSON-hijacking `)]}',` renvoyée par certaines APIs UE (EDES)."""
    return text.lstrip()[5:] if text.lstrip().startswith(")]}',") else text


def connect_db() -> duckdb.DuckDBPyConnection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(config.DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _provenance (
            source        VARCHAR,
            url           VARCHAR,
            table_cible   VARCHAR,
            lignes        BIGINT,
            collecte_le   TIMESTAMP,
            licence       VARCHAR,
            note          VARCHAR
        )
        """
    )
    return conn


def log_provenance(
    conn: duckdb.DuckDBPyConnection,
    source: str,
    url: str,
    table: str,
    licence: str,
    note: str = "",
) -> int:
    """Journalise l'ingestion et retourne le nombre de lignes de la table cible."""
    lignes = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
    conn.execute(
        "DELETE FROM _provenance WHERE table_cible = ?",
        [table],
    )
    conn.execute(
        "INSERT INTO _provenance VALUES (?, ?, ?, ?, ?, ?, ?)",
        [source, url, table, lignes, datetime.now(timezone.utc), licence, note],
    )
    print(f"  -> table {table} : {lignes:,} lignes".replace(",", " "))
    return lignes
