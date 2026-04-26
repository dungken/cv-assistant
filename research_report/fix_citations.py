#!/usr/bin/env python3
"""
fix_citations.py
1. Thêm <a id="ref-N"> anchor vào mỗi entry trong tai_lieu_tham_khao.md
2. Trong mọi file .md còn lại, đổi [N] thành [[N]](path#ref-N)
   - path là đường dẫn tương đối từ file đó đến tai_lieu_tham_khao.md
"""

import re
import os
from pathlib import Path

REPORT_DIR = Path(__file__).parent
REF_FILE   = REPORT_DIR / "tai_lieu_tham_khao.md"

# ── Bước 1: thêm anchor vào file tài liệu tham khảo ─────────────────────────

def add_anchors_to_ref_file():
    text = REF_FILE.read_text(encoding="utf-8")

    # Tìm pattern đầu dòng: [N] ...  (N là 1-2 chữ số)
    # Chỉ thêm anchor nếu chưa có để idempotent
    def replacer(m):
        n = m.group(1)
        anchor = f'<a id="ref-{n}"></a>\n'
        full   = m.group(0)
        # Không thêm nếu dòng trước đó đã có anchor này
        return anchor + full

    # Kiểm tra đã có anchor chưa
    if '<a id="ref-1">' in text:
        print("Anchors already present in reference file — skipping step 1.")
        return

    # Thêm anchor trước mỗi dòng bắt đầu bằng [N]
    new_text = re.sub(r'(?m)^(\[(\d{1,2})\] )', lambda m: f'<a id="ref-{m.group(2)}"></a>\n{m.group(1)}', text)
    REF_FILE.write_text(new_text, encoding="utf-8")
    print(f"✓ Added anchors to {REF_FILE.name}")

# ── Bước 2: cập nhật citation links trong các chương ─────────────────────────

def get_relative_ref_path(from_file: Path) -> str:
    """Tính đường dẫn tương đối từ from_file đến tai_lieu_tham_khao.md"""
    return os.path.relpath(REF_FILE, from_file.parent).replace("\\", "/")

def linkify_citations(md_file: Path):
    text = md_file.read_text(encoding="utf-8")
    rel  = get_relative_ref_path(md_file)

    changed = False
    result  = []

    for line in text.splitlines(keepends=True):
        # Bỏ qua các dòng trong code block
        if line.startswith("```") or line.startswith("    "):
            result.append(line)
            continue

        # Thay [N] → [[N]](path#ref-N)
        # Nhưng KHÔNG thay nếu đã là [[N]](...) rồi
        # Và KHÔNG thay trong URL / code inline / anchor thẻ HTML
        def replace_citation(m):
            n    = m.group(1)
            orig = m.group(0)
            # Nếu ký tự trước là [ → đã là [[N]] rồi, bỏ qua
            return f"[[{n}]]({rel}#ref-{n})"

        new_line = re.sub(
            r'(?<!\[)\[(\d{1,2})\](?!\()',   # [N] nhưng không phải [[N]] và không phải [N](
            replace_citation,
            line
        )

        if new_line != line:
            changed = True
        result.append(new_line)

    if changed:
        md_file.write_text("".join(result), encoding="utf-8")
        print(f"✓ Updated citations in {md_file.relative_to(REPORT_DIR)}")
    else:
        print(f"  (no changes) {md_file.relative_to(REPORT_DIR)}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Bước 1
    add_anchors_to_ref_file()

    # Bước 2 — tất cả .md trừ file tham khảo chính
    md_files = sorted(REPORT_DIR.rglob("*.md"))
    chapter_files = [f for f in md_files if f != REF_FILE and f.name != "fix_citations.py"]

    print(f"\nProcessing {len(chapter_files)} chapter files...")
    for f in chapter_files:
        linkify_citations(f)

    print("\nDone! Verify with:")
    print("  grep -n 'ref-' docs/research_report/tai_lieu_tham_khao.md | head -10")
    print("  grep -n 'tai_lieu' docs/research_report/chuong1/1.2_nen_tang_NLP_BERT.md | head -5")

if __name__ == "__main__":
    main()
