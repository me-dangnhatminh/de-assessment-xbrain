# KB Update SOP — Sao Do Finance Operational Knowledge Base

**Document:** SOP-KB-01 · **Version:** 1.0 · **Issued:** 08/2026  
**Owner:** IT Operations Manager · **Approver:** Operations Head

---

## 1. Purpose and Scope

This SOP governs adding new documents and revising existing documents in the
Sao Do Finance operational knowledge base (`kb/`). It covers metadata
requirements, re-indexing, regression evaluation, approval, and rollback.

---

## 2. Roles

| Role | Person | Responsibility |
|---|---|---|
| **Owner** | IT Operations Manager | Accountable for KB accuracy and update cadence |
| **Technical Operator** | On-duty Operator (Level 2+) | Executes file edits, rebuild, and evaluation |
| **Approver** | Operations Head | Reviews evaluation results and signs off before production use |

---

## 3. Update Cadence

- **Quarterly review:** All 8 documents reviewed on the first Monday of each quarter.
- **Ad-hoc:** Triggered immediately on any policy change, procedure revision, or
  critical error discovered in KB content.

---

## 4. Procedure: Adding a New Document

1. Name the file `<DOC-ID>_<slug>.md` (e.g. `SOP-03_quy_trinh_backup.md`) and place
   it in `docs/onboard/datapack/data/docs/`.
2. Add the required bold metadata header on line 2:
   `**Phiên bản X.Y · Ban hành: MM/YYYY · Người duyệt: <name>**`
3. Structure content with `# ` title and `## ` section headings — each `##` section
   becomes one chunk.
4. Rebuild the index (see §7) and run regression evaluation (see §8).
5. Submit to Approver with evaluation results attached (see §9).

---

## 5. Procedure: Revising an Existing Document

1. Increment the version (e.g. v1.0 → v2.0) and update `Ban hành` / `Cập nhật` date.
2. If this version replaces the previous one, add `Thay thế phiên bản trước` to the
   metadata line — this flags the new file as `is_current=1` and demotes the old one.
3. Keep the old file unchanged in the docs directory — superseded chunks remain in the
   index with `is_current=0` for historical provenance.
4. Rebuild and evaluate (§7, §8). Confirm the new version appears in current-mode search
   and the old version is excluded.

---

## 6. Metadata Validation Checklist

Before rebuilding, verify the file header contains all required fields:

- [ ] `Phiên bản` — version string (e.g. `1.0`, `2.0`)
- [ ] `Ban hành` or `Cập nhật` — date in `MM/YYYY` format
- [ ] `Người duyệt` — approver name
- [ ] For replacements: `Thay thế phiên bản trước` present in metadata line

---

## 7. Re-indexing

```bash
python -m kb build --docs-dir docs/onboard/datapack/data/docs \
                   --output-dir data/evidence/phase2
```

Verify output: chunk count should reflect new/revised documents.
Check FTS5 integrity: `python -c "import sqlite3; c=sqlite3.connect('data/evidence/phase2/index.sqlite'); c.execute('PRAGMA integrity_check').fetchone()"`.

---

## 8. Regression Evaluation

```bash
python -m kb eval --db data/evidence/phase2/index.sqlite \
                  --output-dir data/evidence/phase2
```

Compare `eval_results.json` scores against the previous baseline. Investigate any
case that degrades from `pass` to `partial` or `fail` before proceeding.

---

## 9. Approval Gate

The Approver reviews `data/evidence/phase2/eval_report.md` and confirms:
- No regressions in version-trap cases (Q08, Q09).
- Out-of-scope case (Q10) still returns no result.
- All direct-lookup cases remain `pass`.

Approver signs off in the change ticket before the updated KB is used operationally.

---

## 10. Rollback and History Retention

- **Rollback:** Restore the previous file version (`git checkout -- docs/...`), then
  rebuild and re-evaluate. The demoted version re-becomes `is_current=1`.
- **History:** Superseded documents are never deleted from the docs directory or the
  index. They remain queryable via `python -m kb search --mode all` for audit and
  provenance.
