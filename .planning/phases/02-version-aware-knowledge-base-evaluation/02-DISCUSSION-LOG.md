# Phase 2: Discussion Log

**Date:** 2026-08-12
**Phase:** Version-Aware Knowledge Base & Evaluation
**Mode:** Interactive (default)

## Areas Discussed

### 1. Metadata Extraction
| Question | Options Presented | Selected |
|---|---|---|
| How to extract metadata from Vietnamese source docs? | Regex parse from header / Manual mapping table / Regex + override table | **Regex + override table** |
| How to represent missing metadata values? | Explicit null / Empty string | **Explicit null** |
| Should chunk content stay in Vietnamese? | Keep Vietnamese / Translate to English | **Keep Vietnamese** |

### 2. Chunking Boundaries
| Question | Options Presented | Selected |
|---|---|---|
| At what level to chunk documents? | Per ## section / Per document / Per numbered item | **Per ## section** |
| Should chunks include document-level header? | Prepend doc header / Section content only | **Prepend doc header** |

### 3. Version Resolution
| Question | Options Presented | Selected |
|---|---|---|
| How to store version precedence in SQLite? | is_current column / Supersession table / Status enum column | **is_current column** |
| How to detect POL-01 supersession? | Parse supersession phrase / Date-only comparison | **Parse supersession phrase** |
| How to handle current vs superseded at query time? | Filter-then-rank / Rank-then-partition | **Filter-then-rank** |

### 4. Evaluation Design
| Question | Options Presented | Selected |
|---|---|---|
| Distribution of 10 eval questions across 4 types? | 4-3-2-1 split / 3-3-2-2 split / You decide | **4-3-2-1 split** |
| How many eval questions to actually execute? | All 10 retrieval-only / Minimum 3 / Retrieval + LLM for 3 | **All 10 retrieval-only** |
| What format for evaluation results? | Structured JSON / Markdown report / JSON + rendered Markdown | **JSON + rendered Markdown** |
| How to score retrieval hit vs groundedness? | Two separate scores / Combined score + diagnosis | **Two separate scores** |

## Deferred Ideas
- Bedrock-generated answers for eval (→ Phase 3)
- Semantic/embedding search (out of scope per stack)
