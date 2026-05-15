"""Streamlit labeling UI for the eval set.

Designed for FAST labeling:
  - Pre-fills every field with the rule-based extractor's output.
  - Most fields you can just verify and click "Save & Next" — no typing.
  - Easy fields (title, company, location, posted_date, url) are NOT shown
    for editing — they're trusted directly from the crawler. Only the
    8 hard fields are exposed.
  - Skills are checkbox grids: required ☑ / preferred ☑ / both unchecked.
  - Progress bar + skip + go-back navigation.

Run (after sample_for_labeling.py has produced label_pool.jsonl):
    .venv/bin/streamlit run services/crawler_service/scripts/eval/label_ui.py -- \\
        --pool services/crawler_service/data/eval/label_pool.jsonl \\
        --gold services/crawler_service/data/eval/gold_labels.jsonl

The UI loads label_pool.jsonl, lets you label each JD, and appends each
saved label to gold_labels.jsonl. Re-running the UI resumes where you left
off (skips JDs already in gold_labels.jsonl by jd_key).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import streamlit as st


# ─── Args ─────────────────────────────────────────────────────────────────────

def _parse_args() -> dict:
    """Streamlit invokes the script with `-- arg1 arg2`; sys.argv carries them."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, help="path to label_pool.jsonl")
    ap.add_argument("--gold", required=True, help="path to gold_labels.jsonl (append-mode)")
    try:
        idx = sys.argv.index("--")
        ns = ap.parse_args(sys.argv[idx + 1:])
    except ValueError:
        ns = ap.parse_args()
    return {"pool": ns.pool, "gold": ns.gold}


# ─── IO helpers ───────────────────────────────────────────────────────────────

def load_pool(path: str) -> list[dict]:
    out: list[dict] = []
    p = Path(path)
    if not p.exists():
        st.error(f"Pool file not found: {path}")
        return out
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_done(path: str) -> set[str]:
    done: set[str] = set()
    p = Path(path)
    if not p.exists():
        return done
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("jd_key"):
                    done.add(rec["jd_key"])
            except json.JSONDecodeError:
                continue
    return done


def append_gold(path: str, record: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─── UI ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="JD Labeling", layout="wide")
    args = _parse_args()

    pool = load_pool(args["pool"])
    if not pool:
        st.stop()
    done_keys = load_done(args["gold"])
    remaining = [jd for jd in pool if jd["jd_key"] not in done_keys]

    # ── Header / progress ──
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("JD Labeling")
        st.caption(f"Pool: {args['pool']}  ·  Gold: {args['gold']}")
    with col2:
        st.metric("Progress", f"{len(done_keys)} / {len(pool)}")
        st.progress(len(done_keys) / max(len(pool), 1))

    if not remaining:
        st.success(f"Done! All {len(pool)} JDs labeled. Run `run_eval.py` next.")
        st.stop()

    # ── Current JD ──
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if st.session_state.idx >= len(remaining):
        st.session_state.idx = 0
    jd = remaining[st.session_state.idx]

    st.divider()
    cols = st.columns([4, 1])
    with cols[0]:
        st.subheader(jd["title"])
        st.caption(
            f"**{jd['company']}**  ·  stratum: `{jd['stratum']}`  ·  "
            f"[open on ITviec]({jd['url']})"
        )
    with cols[1]:
        st.write(f"#{st.session_state.idx + 1} / {len(remaining)}")
        if st.button("⏭ Skip", help="Move to next without saving"):
            st.session_state.idx = (st.session_state.idx + 1) % len(remaining)
            st.rerun()

    # ── Two-column layout: description left, label form right ──
    left, right = st.columns([3, 2])

    with left:
        st.markdown("**Description**")
        # Render the description in a scrollable container.
        st.text_area(
            "JD body (read-only)",
            jd["description"],
            height=600,
            label_visibility="collapsed",
        )

    with right:
        st.markdown("**Labels**")
        pre = jd.get("pre_labels") or {}

        seniority = st.selectbox(
            "Seniority",
            options=["null", "junior", "mid", "senior", "lead"],
            index={"null": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4}.get(
                pre.get("seniority") or "null", 0
            ),
            help="Title literally contains the level word? If no → null.",
        )

        cmin, cmax = st.columns(2)
        with cmin:
            min_exp = st.number_input(
                "Min exp (years)",
                min_value=0, max_value=30, step=1,
                value=int(pre.get("min_exp") or 0),
                help="0 = not specified",
            )
        with cmax:
            max_exp = st.number_input(
                "Max exp (years)",
                min_value=0, max_value=30, step=1,
                value=int(pre.get("max_exp") or 0),
                help="0 = not specified",
            )

        degree = st.selectbox(
            "Degree required",
            options=["null", "Bachelor", "Master", "PhD"],
            index={"null": 0, "Bachelor": 1, "Master": 2, "PhD": 3}.get(
                pre.get("degree_required") or "null", 0
            ),
        )

        work_mode = st.selectbox(
            "Work mode",
            options=["null", "onsite", "hybrid", "remote"],
            index={"null": 0, "onsite": 1, "hybrid": 2, "remote": 3}.get(
                pre.get("work_mode") or "null", 0
            ),
        )

        st.markdown("---")
        st.markdown("**Skills** (Required ✓ / Preferred ⭐ / Neither blank)")

        # All canonical chips for this JD. Pre-fill from rule extractor.
        all_skills = jd.get("skills_canonical") or []
        pre_req = set(pre.get("skills_required") or [])
        pre_pref = set(pre.get("skills_preferred") or [])

        skill_state: dict[str, str] = {}
        for s in all_skills:
            default = "required" if s in pre_req else ("preferred" if s in pre_pref else "neither")
            opts = ["neither", "required", "preferred"]
            choice = st.radio(
                s,
                options=opts,
                index=opts.index(default),
                horizontal=True,
                key=f"skill_{jd['jd_key']}_{s}",
                label_visibility="visible",
            )
            skill_state[s] = choice

        st.markdown("---")
        st.markdown("**Salary** (numeric only — leave 0 if hidden)")
        s1, s2, s3 = st.columns([2, 2, 1])
        with s1:
            salary_min = st.number_input("Min", min_value=0, value=0, step=100)
        with s2:
            salary_max = st.number_input("Max", min_value=0, value=0, step=100)
        with s3:
            salary_currency = st.selectbox("Curr", ["", "USD", "VND"])

        st.divider()
        save_col, back_col = st.columns([3, 1])
        with save_col:
            if st.button("💾 Save & Next", type="primary", use_container_width=True):
                gold = {
                    "jd_key": jd["jd_key"],
                    "title": jd["title"],
                    "stratum": jd["stratum"],
                    "gold_labels": {
                        "seniority": None if seniority == "null" else seniority,
                        "min_exp": int(min_exp) if min_exp > 0 else None,
                        "max_exp": int(max_exp) if max_exp > 0 else None,
                        "degree_required": None if degree == "null" else degree,
                        "work_mode": None if work_mode == "null" else work_mode,
                        "skills_required": [s for s, v in skill_state.items() if v == "required"],
                        "skills_preferred": [s for s, v in skill_state.items() if v == "preferred"],
                        "salary_min": int(salary_min) if salary_min > 0 else None,
                        "salary_max": int(salary_max) if salary_max > 0 else None,
                        "salary_currency": salary_currency or None,
                    },
                }
                append_gold(args["gold"], gold)
                st.session_state.idx = 0  # next JD will be the new first remaining
                st.rerun()
        with back_col:
            if st.button("← Back", help="Go to previous JD (does not undo save)"):
                st.session_state.idx = max(0, st.session_state.idx - 1)
                st.rerun()


if __name__ == "__main__":
    main()
