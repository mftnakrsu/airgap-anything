# Extraction and chunking

Goal: pick how documents become text, keep every document inside the network, and write the chunking settings. Facts about docling-serve are in `catalog/docling-serve.md`; read it first.

## Contents

- The cloud rule
- Three tiers
- docling-serve OCR offline
- Not used
- Chunking

## The cloud rule

Never send documents from inside the network to a cloud agent or any hosted conversion service outside it. The air gap exists to keep them in; a copy that has left cannot be taken back, and nothing in this skill can check what the outside keeps. The connected-side agent may convert only public documents. State this rule, with that reason, wherever you write about conversion: in `rag.md`, and again when a user says "just send the PDFs to Claude to convert them, it's faster". Say no, and offer the tier that fits (below): converting inside is slower, never unsafe. Hosted engines inside Open WebUI count too: Marker sends files to datalab.to unless a URL is set (see "Not used").

## Three tiers

| Documents | Method | Notes |
|---|---|---|
| Mostly digital PDF and Office | Open WebUI's built-in extractor: PyPDFLoader (pypdf 6.21.2) for PDFs, unstructured (0.22.31) for ODT, MSG and PPTX | `CONTENT_EXTRACTION_ENGINE` empty. Keep `PDF_EXTRACT_IMAGES` off (its default) unless the RapidOCR models are staged: the image does not pre-fetch them, so test it offline first. The slim image needs Tika or Docling for PDFs and Office files (the architect's `open-webui` entry) |
| Scanned or table-heavy | `catalog/docling-serve.md`, v1.39.0 | The `-cpu` image (4.4 GB) or `-cu128` (11.4 GB) with a GPU. `CONTENT_EXTRACTION_ENGINE=docling`. Missing models raise errors instead of downloading |
| LLM wiki for coding agents | The local agent inside, with `pdftotext` from poppler-utils | Writes markdown into a git repository: `references/wiki.md` |

Sources for the built-in row: https://docs.openwebui.com/features/chat-conversations/rag/document-extraction/ and the v0.13.4 `requirements.txt` (https://raw.githubusercontent.com/open-webui/open-webui/v0.13.4/backend/requirements.txt). A pypdf extraction rate is not documented: measure it on a 100-page sample (`references/sizing.md`).

One line for the alternative: Apache Tika 4.2.0 (Apache-2.0, `apache/tika:4.2.0`, 188 MB; `-full` 611 MB adds Tesseract for eng, fra, deu, ita, spa and jpn). It runs on the JVM, CPU only, with no layout or table models. Open WebUI speaks the Tika 3 API by default, so set `TIKA_SERVER_VERSION=4` for Tika 4.2 (https://tika.apache.org/, https://docs.openwebui.com/features/chat-conversations/rag/document-extraction/apachetika.md). Not configured by this skill.

## docling-serve OCR offline

- **EasyOCR** has `english_g2` and `latin_g2` baked into the image. EasyOCR's Latin list includes `tr`, `de` and `fr`, so it is the default for Latin-script languages.
- **RapidOCR**'s baked default `ch` maps to `multi_PP-OCRv6_rec_small`, which lists `tr`, `de`, `fr` and about 40 more. The mapping was read from a YAML and not run, so it is `estimate`. RapidOCR also uses only the first language given.
- **Tesseract** has English only, so it cannot read other languages offline.
- **Not baked in:** Cyrillic, Arabic, Devanagari, Thai, Greek and Korean models. If the documents need one, stage it on the connected side with `docling-tools models download --output-dir DIR` and carry it (`catalog/docling-serve.md`, Carry in).
- **Setting:** Open WebUI forwards `DOCLING_PARAMS` unchanged to `/v1/convert/file`. Write, with the user's languages from the `languages` answer: `{"do_ocr": true, "ocr_preset": "easyocr", "ocr_lang": ["tr", "en"]}`. Open WebUI's own docs still show the deprecated `ocr_engine`; it still works in v1.39.0 but is copied into `ocr_preset` with a warning. Without `ocr_lang` the engine default applies (English for EasyOCR, Simplified Chinese for RapidOCR).
- **Headings:** Open WebUI splits on the markdown headings it finds in Docling's output. The option `do_pdf_heading_hierarchy` makes Docling emit heading levels, and otherwise "every detected heading stays at level 1" (docling-serve usage.md). Whether it helps on real documents was not tested: try it on the retrieval sample and keep it only if it helps.
- **Server side:** `UVICORN_WORKERS=1`, and raise `DOCLING_SERVE_MAX_SYNC_WAIT` above its 120 s default. The research gives no better number: set it above the conversion time of the largest document in your 100-page sample.
- **Check inside:** `GET /v1/capabilities` lists the engines, and a conversion with the network off proves that nothing is downloaded (`references/verification.md`, check 3).

Source for this section: the v1.39.0 research of 2026-11-24 (https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/usage.md, https://raw.githubusercontent.com/JaidedAI/EasyOCR/v1.7.2/easyocr/config.py, https://raw.githubusercontent.com/RapidAI/RapidOCR/v3.10.0/python/rapidocr/default_models.yaml).

## Not used

| Tool | Reason |
|---|---|
| Marker | Open WebUI's `datalab_marker` engine sends files to datalab.to unless `DATALAB_MARKER_API_BASE_URL` is set, and the weights carry a modified OpenRAIL-M license, free only for research, personal use and startups under USD 5M (https://github.com/datalab-to/marker) |
| MinerU | Its `full` extra pins `vllm<0.31.0`, while the architect's catalog pins vLLM v0.34.0 (https://raw.githubusercontent.com/opendatalab/MinerU/master/pyproject.toml). Its license also adds terms above 100M monthly active users |
| Unstructured as a separate service | Its telemetry is on by default; it is switched off with `DO_NOT_TRACK` or `SCARF_NO_ANALYTICS` (https://github.com/Unstructured-IO/unstructured). The built-in copy inside Open WebUI runs under an image that sets both to true (that these silence it is inferred, not tested) |

## Chunking

Settings in Open WebUI v0.13.4 (env reference and source; all are persistent config, so after the first start the admin panel holds them):

| Variable | Default | Meaning |
|---|---|---|
| `ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER` | True | Splits on markdown headings h1 to h6 first; each piece is then split again by the chosen splitter |
| `CHUNK_MIN_SIZE_TARGET` | 0 (off) | Merges undersized pieces, but only inside that header split; no chunk goes above `CHUNK_SIZE` |
| `RAG_TEXT_SPLITTER` | `character` | `character` counts characters; `token` counts tiktoken `cl100k_base` tokens (the encoding is baked into the image); `token_transformers` counts tokens with the tokenizer in `RAG_TOKENIZER_MODEL`, which would have to be staged and is not on the slim image |
| `CHUNK_SIZE` and `CHUNK_OVERLAP` | 1024 and 100 | In the splitter's unit |

There is no semantic chunking in Open WebUI. docling-serve has chunk endpoints (`/v1/chunk/hybrid`, `/v1/chunk/hierarchical`), but Open WebUI never uses them: it takes Docling's markdown and splits it again with its own splitter. Do not add `chunking_*` keys to `DOCLING_PARAMS`.

The skill's choice, written to `docs/airgap/rag/`:

- Keep the header splitter on, so chunks follow the structure of the documents.
- Keep the `character` splitter at 1024 and 100. That is far below the embedding models' limits (32K and 8,192 tokens), so no tokenizer has to be staged.
- Set `CHUNK_MIN_SIZE_TARGET=256`, so that tiny sections, for example a heading alone, merge into a neighbor. The value, one quarter of `CHUNK_SIZE`, is an `estimate`: tune it with the retrieval check (`references/verification.md`, check 2).
- Write in `rag.md`: "reindex after changing them". Open WebUI's docs say to reindex existing documents after a change; an admin endpoint `POST /api/v1/knowledge/reindex` exists (read from source at tag v0.13.4).

Source: https://docs.openwebui.com/reference/env-configuration and the v0.13.4 source (`routers/retrieval.py`, `config.py`), read 2026-11-24.
