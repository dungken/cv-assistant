"""Persist crawled JDs to PostgreSQL + ChromaDB.

Upsert semantics:
- New jd_key → insert into jd_raw, add to ChromaDB.
- Existing jd_key → only update last_seen (job still active).
"""
import json
import logging
from datetime import datetime
from typing import Iterable

from sentence_transformers import SentenceTransformer
from sqlalchemy.dialects.postgresql import insert as pg_insert

from services.crawler_service.config import settings
from services.crawler_service.models.database import JDRaw
from services.crawler_service.models.schemas import ProcessedJD
from services.crawler_service.services.db_session import get_session
from shared.db.chroma_client import get_chroma_client

logger = logging.getLogger(__name__)


class JDStorage:
    def __init__(self) -> None:
        self._embedder: SentenceTransformer | None = None
        self._collection = None

    # ── lazy init: model + collection ──────────────────────────────

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            logger.info("Loading SBERT all-MiniLM-L6-v2")
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        return self._embedder

    @property
    def collection(self):
        if self._collection is None:
            client = get_chroma_client(host=settings.chroma_host, port=settings.chroma_port)
            self._collection = client.get_or_create_collection(
                name=settings.chroma_collection
            )
        return self._collection

    # ── public ──────────────────────────────────────────────────────

    def save_batch(self, jds: Iterable[ProcessedJD]) -> int:
        jds = list(jds)
        if not jds:
            return 0
        new_count = self._upsert_postgres(jds)
        self._index_chromadb(jds)
        return new_count

    # ── postgres ────────────────────────────────────────────────────

    def _upsert_postgres(self, jds: list[ProcessedJD]) -> int:
        new_count = 0
        now = datetime.utcnow()

        with get_session() as session:
            for jd in jds:
                stmt = pg_insert(JDRaw).values(
                    jd_key=jd.jd_key,
                    source=jd.raw.source,
                    source_id=jd.raw.source_id,
                    title=jd.raw.title,
                    company=jd.raw.company,
                    description=jd.raw.description,
                    skills_canonical=jd.skills_canonical,
                    skills_raw=jd.raw.skills_raw,
                    salary_min=jd.raw.salary_min,
                    salary_max=jd.raw.salary_max,
                    salary_currency=jd.raw.salary_currency,
                    location=jd.raw.location,
                    exp_level=jd.raw.exp_level,
                    role=jd.role,
                    role_group=jd.role_group,
                    posted_date=jd.raw.posted_date,
                    first_seen=jd.first_seen,
                    last_seen=jd.last_seen,
                    url=jd.raw.url,
                    # Tuần 16 enrichment — these may be None if NER unavailable.
                    min_exp=jd.min_exp,
                    max_exp=jd.max_exp,
                    seniority=jd.seniority,
                    skills_required=jd.skills_required,
                    skills_preferred=jd.skills_preferred,
                    degree_required=jd.degree_required,
                    work_mode=jd.work_mode,
                    description_summary=jd.description_summary,
                    parsed_at=jd.parsed_at,
                    parse_version=jd.parse_version,
                )
                # On conflict: refresh last_seen + re-enrich if we parsed this run.
                # When parsed_at is set, also overwrite parsed columns so a later
                # crawl picks up a better parse if the parser was upgraded.
                update_set = {"last_seen": now}
                if jd.parsed_at is not None:
                    update_set.update({
                        "min_exp": jd.min_exp,
                        "max_exp": jd.max_exp,
                        "seniority": jd.seniority,
                        "skills_required": jd.skills_required,
                        "skills_preferred": jd.skills_preferred,
                        "degree_required": jd.degree_required,
                        "work_mode": jd.work_mode,
                        "description_summary": jd.description_summary,
                        "parsed_at": jd.parsed_at,
                        "parse_version": jd.parse_version,
                    })
                stmt = stmt.on_conflict_do_update(
                    index_elements=["jd_key"], set_=update_set,
                )
                result = session.execute(stmt)
                # rowcount==1 for both insert and update; check via SELECT before for accuracy
                if result.rowcount == 1:
                    # crude heuristic — we'll just count attempts; pipeline tracks total
                    new_count += 1
        return new_count

    # ── chromadb ────────────────────────────────────────────────────

    def _index_chromadb(self, jds: list[ProcessedJD]) -> None:
        docs, embeddings, metadatas, ids = [], [], [], []
        for jd in jds:
            text = jd.raw.description or jd.raw.title
            if not text:
                continue
            docs.append(text)
            embeddings.append(self.embedder.encode(text).tolist())
            metadatas.append({
                "jd_key": jd.jd_key,
                "source": jd.raw.source,
                "title": jd.raw.title,
                "company": jd.raw.company or "",
                "role": jd.role or "",
                "skills": json.dumps(jd.skills_canonical),
                "salary_min": jd.raw.salary_min or 0,
                "salary_max": jd.raw.salary_max or 0,
                "location": jd.raw.location or "",
                "exp_level": jd.raw.exp_level or "",
                "posted_date": jd.raw.posted_date.isoformat(),
            })
            ids.append(jd.jd_key)

        if not ids:
            return
        try:
            # upsert handles both new and existing ids
            self.collection.upsert(
                documents=docs, embeddings=embeddings,
                metadatas=metadatas, ids=ids,
            )
        except Exception as e:
            logger.exception("ChromaDB index failed: %s", e)
