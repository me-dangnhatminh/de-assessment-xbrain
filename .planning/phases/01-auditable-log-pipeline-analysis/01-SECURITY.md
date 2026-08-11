---
phase: 01
slug: auditable-log-pipeline-analysis
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-12
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Package registry/source → local environment | Third-party package identity and code enter the reviewer environment. | third-party code / dependency integrity |
| `docs/onboard/**` → pipeline CLI | Supplied bytes are untrusted, immutable assessment inputs. | JSONL log records / source integrity |
| CLI paths → generated output root | Caller-controlled paths could otherwise overwrite source or unrelated files. | filesystem paths / path-injection |
| Untrusted JSONL bytes → parser/validator | Malformed, oversized, duplicated, or misleading records enter deterministic code. | log records / data quality |
| Validation result → downstream analytical path | Rejected records must remain attributable and must not cross the quality boundary. | ledger disposition / repudiation |
| Generated Parquet/ledger → DuckDB SQL | Evidence is trusted only after schema/hash/conservation verification; paths remain parameter-bound. | SQL bindings / injection |
| Generated evidence → report/manifest | Tampered or stale artifacts could be presented as verified customer results. | evidence hashes / integrity |
| CLI `--clean`/output root → filesystem | Destructive cleanup must remain limited to known generated Phase 1 files. | filesystem paths / elevation |
| Persisted manifests → verification verdict | Generated JSON is attacker/corruption-controlled and cannot authenticate itself. | manifest metadata / spoofing |
| Documentation/Make commands → reviewer shell | Commands must be exact, locked, and free of secret/network/cloud assumptions. | shell commands / supply-chain |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-SC | Tampering | uv/PyPI package bootstrap and installs | high | mitigate | Human-approved `uv.lock` pins the resolution; `uv lock --check` + `uv sync --locked` gates; no new package-manager surface added. | closed |
| T-01-01 | Tampering | `pipeline/__main__.py` output-root handling | high | mitigate | `validate_output_root` resolves paths and rejects any generated root within `docs/onboard` before writes. | closed |
| T-01-02 | Denial of Service | JSONL line parsing | medium | mitigate | Stream only the selected line and enforce the 1 MiB maximum before JSON parsing. | closed |
| T-01-03 | Repudiation | tracer evidence | medium | mitigate | Tracer manifest records source path, source line, pre/post SHA-256, output hashes, row counts, SQL path, and command metadata. | closed |
| T-01-04 | Information Disclosure | CLI diagnostics | low | accept | Fictional assessment data; diagnostics name only the selected line/path and avoid unrelated file dumps. | closed |
| T-01-05 | Tampering | output path validation and writers | high | mitigate | Resolve paths, reject outputs within `docs/onboard`, hash supplied files before/after, atomically replace only explicit generated paths. | closed |
| T-01-06 | Denial of Service | `iter_source_lines` / JSON parsing | medium | mitigate | Stream one line at a time and reject lines above the documented 1 MiB maximum before parsing. | closed |
| T-01-07 | Repudiation | validation/disposition and ledger/Parquet publication | medium | mitigate | One result per physical line retains raw provenance, all issues/normalizations, final action, source hash, duplicate cross-reference, and both conservation equations. | closed |
| T-01-08 | Information Disclosure | diagnostics and ledger | low | accept | Full fictional-source ledger content is required reviewer evidence; ordinary logs omit unrelated bulk data. | closed |
| T-01-09 | Spoofing | provenance fields | medium | mitigate | Bind source-line identifiers to byte-level source SHA-256 and canonical record digest rather than record-supplied identifiers. | closed |
| T-01-10 | Tampering | SQL execution | high | mitigate | Load only checked-in static SQL; bind dataset paths as parameters; never concatenate caller input into query text. | closed |
| T-01-11 | Repudiation | customer-answer tables | medium | mitigate | Fixed IDs, SQL/result paths, schemas, deterministic ordering, and aggregate reconciliation preserve production lineage. | closed |
| T-01-12 | Information Disclosure | result tables | low | accept | Tables contain aggregates and service names from fictional data, not full raw messages or identifiers. | closed |
| T-01-13 | Tampering | unusual-day interpretation | medium | mitigate | SQL pins the strict threshold/ratio and tests service contribution sums; downstream wording remains descriptive. | closed |
| T-01-14 | Denial of Service | bounded local run | low | accept | 2,923-line bounded dataset with pre-parse caps; restartable through atomic outputs. | closed |
| T-01-15 | Tampering | `run_manifest.json` / committed evidence | high | mitigate | Hash every required artifact and SQL file, bind row counts/query IDs/paths, fail verification on any mismatch. | closed |
| T-01-16 | Elevation of Privilege | `--clean` path handling | high | mitigate | Resolve the root, reject supplied/project roots, enumerate exact generated targets, test refusal before deletion. | closed |
| T-01-17 | Repudiation | reviewer report claims | medium | mitigate | Render answers only from result files; cite SQL, dataset hash, counts, and manifest ID beside each claim. | closed |
| T-01-18 | Information Disclosure | README/manifest | low | accept | No credentials/account identifiers; manifest allowlists non-secret runtime versions and repository-relative local paths. | closed |
| T-01-19 | Denial of Service | full verification | low | accept | Bounded local dataset with four fixed queries; failures stay visible and restartable through atomic outputs. | closed |
| T-01-20 | Tampering | `verify_run_manifest()` source-integrity verdict | high | mitigate | Recompute every live supplied-file digest and require exact three-way equality with both persisted inventory lists. | closed |
| T-01-21 | Repudiation | forged/stale manifest rebuild sequence | medium | mitigate | Deterministic adversarial regressions rebuild derived metadata around a forgery and require a named verification failure. | closed |
| T-01-22 | Tampering | Phase 1 roadmap contract | medium | mitigate | One Goal line changed only; canonical grammar validated; all four technical success criteria and plan history asserted present. | closed |
| T-01-23 | Information Disclosure | inventory mismatch diagnostics | low | accept | Relative supplied paths/digests are required evidence; errors name the mismatched layer without dumping source contents. | closed |
| T-01-24 | Tampering | `cmd_run()` / `cmd_all()` input selection | high | mitigate | `require_canonical_log_input()` resolves before cleanup/writes and requires exact equality with the canonical supplied-log path; same-byte foreign file tested. | closed |
| T-01-25 | Spoofing | `source_manifest.input` | high | mitigate | Require canonical inventory membership and recompute the live SHA-256 before accepting descriptor, source inventory, or rebuilt run manifest. | closed |
| T-01-26 | Tampering | Parquet/ledger row-count evidence | high | mitigate | Measure Parquet with DuckDB and final actions from strict ledger parsing during verification; source-count forgery + rebuild tested. | closed |
| T-01-27 | Tampering | concurrent writer/verifier on one output root | low | accept | Documented local workflow is single-writer; verification follows atomic publication; observable mixed-state reads fail closed. | closed |
| T-01-28 | Information Disclosure | Integrity error messages | low | accept | Relative evidence paths and count categories are required reviewer evidence; diagnostics identify the failed layer without emitting source records. | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-01-04 | T-01-04 | Fictional assessment data; diagnostics avoid unrelated bulk dumps. | Phase plan threat model | 2026-08-11 |
| R-01-08 | T-01-08 | Full fictional-source ledger is required reviewer evidence. | Phase plan threat model | 2026-08-11 |
| R-01-12 | T-01-12 | Result tables hold fictional aggregates, not raw messages/identifiers. | Phase plan threat model | 2026-08-11 |
| R-01-14 | T-01-14 | Bounded 2,923-line local batch; restartable after visible failure. | Phase plan threat model | 2026-08-11 |
| R-01-18 | T-01-18 | No credentials/account identifiers exist in Phase 1 artifacts. | Phase plan threat model | 2026-08-11 |
| R-01-19 | T-01-19 | Bounded local verification; failures visible and restartable. | Phase plan threat model | 2026-08-11 |
| R-01-23 | T-01-23 | Relative paths/digests are required evidence; errors name the layer only. | Phase plan threat model | 2026-08-11 |
| R-01-27 | T-01-27 | Single-writer local workflow; no supported concurrent-write contract. | Phase plan threat model | 2026-08-11 |
| R-01-28 | T-01-28 | Diagnostics identify the failed layer without emitting source records. | Phase plan threat model | 2026-08-11 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-12 | 29 | 29 | 0 | ZCode orchestrator |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-12
