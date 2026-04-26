"""
Demo NER CV model on 1 sample per role (10 roles × 1 CV = 10 samples).
Output: formatted entity extraction results saved to docs/reports/ner_cv_demo.txt
"""

import json
import re
from pathlib import Path
from collections import defaultdict

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

MODEL_DIR = "models/ner/final"
DATA_FILE = "data/synthetic_cvs.jsonl"
OUTPUT_FILE = "docs/reports/ner_cv_demo.txt"

ENTITY_COLORS = {
    "PER": "👤", "ORG": "🏢", "JOB_TITLE": "💼",
    "SKILL": "⚙️",  "DEGREE": "🎓", "MAJOR": "📚",
    "DATE": "📅",   "LOC": "📍",    "CERT": "🏅",
    "PROJECT": "📁",
}


def clean_text(text: str, max_chars: int = 800) -> str:
    """Strip markdown, truncate for display."""
    text = re.sub(r"\*{1,2}|#{1,3}|`{1,3}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars].strip()


def group_entities(ner_results: list[dict]) -> dict[str, list[str]]:
    """Group pipeline output by entity type, deduplicate."""
    grouped = defaultdict(list)
    for ent in ner_results:
        label = ent["entity_group"]
        word = ent["word"].strip()
        # Skip very short / noisy tokens
        if len(word) < 2 or re.match(r"^[\W_]+$", word):
            continue
        if word not in grouped[label]:
            grouped[label].append(word)
    return dict(grouped)


def format_cv_demo(rec: dict, grouped: dict[str, list[str]]) -> str:
    lines = []
    sep = "─" * 68
    lines.append(sep)
    lines.append(f"  Role      : {rec['role']}  |  Seniority: {rec.get('seniority','?')}  |  YoE: {rec.get('yoe','?')}")
    lines.append(f"  CV ID     : {rec['id']}  |  Quality score: {rec.get('quality_score', '?')}")
    lines.append(sep)

    # CV text preview (first 400 chars, cleaned)
    preview = clean_text(rec.get("text_clean") or rec.get("text", ""), max_chars=400)
    lines.append("  [CV Preview]")
    for l in preview.split("\n")[:8]:
        lines.append(f"    {l}")
    lines.append("  ...")
    lines.append("")

    # Extracted entities
    lines.append("  [Extracted Entities]")
    if not grouped:
        lines.append("    (no entities detected)")
    else:
        order = ["PER", "JOB_TITLE", "ORG", "SKILL", "DEGREE", "MAJOR",
                 "DATE", "LOC", "CERT", "PROJECT"]
        for etype in order:
            if etype not in grouped:
                continue
            icon = ENTITY_COLORS.get(etype, "•")
            values = grouped[etype][:8]  # max 8 per type
            values_str = " | ".join(values)
            lines.append(f"    {icon} {etype:<12}: {values_str}")
    lines.append(sep)
    return "\n".join(lines)


def main():
    # Load data — pick 1 CV per role (first occurrence)
    records_by_role: dict[str, dict] = {}
    with open(DATA_FILE) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            role = rec["role"]
            if role not in records_by_role:
                records_by_role[role] = rec
            if len(records_by_role) == 10:
                break

    samples = list(records_by_role.values())
    print(f"Selected {len(samples)} CVs (1 per role)")

    # Load model
    print(f"Loading model from {MODEL_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)
    device = 0 if torch.cuda.is_available() else -1
    ner_pipe = pipeline(
        "ner", model=model, tokenizer=tokenizer,
        aggregation_strategy="simple", device=device,
    )
    print(f"  Device: {'GPU' if device == 0 else 'CPU'}\n")

    # Run demo
    output_blocks = []
    summary_rows = []

    for rec in samples:
        text = rec.get("text_clean") or rec.get("text", "")
        # Truncate to 512 tokens worth of chars (~2000 chars) to avoid OOM
        text_input = text[:2000]

        try:
            results = ner_pipe(text_input)
        except Exception as e:
            print(f"  [SKIP] {rec['role']}: {e}")
            continue

        grouped = group_entities(results)
        block = format_cv_demo(rec, grouped)
        output_blocks.append(block)
        print(block)

        # Summary row
        n_entities = sum(len(v) for v in grouped.values())
        etypes = ", ".join(sorted(grouped.keys()))
        summary_rows.append(
            f"  {rec['role']:<25} | entities={n_entities:3d} | types: {etypes}"
        )

    # Build full report
    header = [
        "=" * 68,
        "  NER CV Model — Demo Output",
        f"  Model  : {MODEL_DIR}",
        f"  Data   : {DATA_FILE}",
        f"  Samples: {len(output_blocks)} CVs (1 per role)",
        "=" * 68,
        "",
    ]

    summary = [
        "",
        "=" * 68,
        "  Summary",
        "=" * 68,
        f"  {'Role':<25} | Entities | Types detected",
        "  " + "─" * 64,
    ] + summary_rows + ["=" * 68]

    full_report = "\n".join(header) + "\n\n" + "\n\n".join(output_blocks) + "\n" + "\n".join(summary)

    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(full_report)
    print(f"\nReport saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
