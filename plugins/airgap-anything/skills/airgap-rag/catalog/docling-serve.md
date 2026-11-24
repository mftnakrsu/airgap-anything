# Docling Serve (`docling-serve`)

HTTP service that converts scanned and layout-heavy documents (PDF, Office, images) into markdown with layout, table and OCR models. Open WebUI calls it as its content extraction engine.

| Field | Value |
|---|---|
| Kind | `extractor` |
| Version | `v1.39.0` |
| License | MIT; each model's weights keep their own license |
| Install | container image `quay.io/docling-project/docling-serve-cpu:v1.39.0` (4.4 GB), or `-cu128` (11.4 GB, amd64) with a GPU; same names on `ghcr.io/docling-project/` |
| Evidence | docs |
| Last verified | 2026-11-24 |

Release v1.39.0 (2026-11-23) bundles docling-slim 2.152.0 (https://api.github.com/repos/docling-project/docling-serve/releases/latest). Open WebUI v0.13.4 itself is in the architect's `open-webui` entry; this entry covers only the extractor.

## Choose when

- The documents are scanned, photographed or table-heavy, so a text layer is missing or wrong.
- A separate extraction service is acceptable: it needs its own container and, for speed, a GPU.

## Avoid when

- The documents are mostly digital PDF and Office files: Open WebUI's built-in extractor (pypdf and unstructured) is enough and needs no extra service.
- Documents must be read in a language other than the Latin-script ones that EasyOCR covers and no extra models can be staged (see Caveats).

## Configuration

Open WebUI side (read from the Open WebUI docs, https://docs.openwebui.com/reference/env-configuration):

- `CONTENT_EXTRACTION_ENGINE=docling`.
- `DOCLING_SERVER_URL`, default `http://docling:5001`.
- `DOCLING_API_KEY`, sent as the `X-Api-Key` header; the value comes from the environment, never from a file in the repository.
- `DOCLING_PARAMS`, a JSON object, default `{}`. The old per-field `DOCLING_*` variables are ignored. Open WebUI forwards every key to `/v1/convert/file` unchanged. Example for Latin-script languages, with the user's own languages in `ocr_lang` (derived from the loader and the server schema, not run): `{"do_ocr": true, "ocr_preset": "easyocr", "ocr_lang": ["tr", "en"]}`. `ocr_lang` takes BCP-47 tags in order of preference (https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/usage.md).
- Open WebUI's docs still show the deprecated `ocr_engine` with engine-specific language codes; `ocr_engine` still works in v1.39.0 but is copied into `ocr_preset` with a deprecation warning. The default of `ocr_preset` is `auto` in the source read for the research.

Server side:

- Behind Open WebUI keep `UVICORN_WORKERS=1` and raise `DOCLING_SERVE_MAX_SYNC_WAIT` above its 120 s default (https://docs.openwebui.com/features/chat-conversations/rag/document-extraction/docling.md).
- `DOCLING_SERVE_API_KEY` sets an API key on the service: "If specified, all the API requests must contain the header `X-Api-Key` with this value" (https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/configuration.md). Open WebUI's `DOCLING_API_KEY` is what it sends in that header, so the two must hold the same value, each from the environment of its host.
- Compute engines are local (2 workers), rq (Redis) and ray; file and page limits are unset by default (same page).
- The container listens on port 5001 as UID 1001; models live in `DOCLING_SERVE_ARTIFACTS_PATH=/opt/app-root/src/.cache/docling/models` (https://raw.githubusercontent.com/docling-project/docling-serve/main/Containerfile).
- Check inside the network: `GET /v1/capabilities` lists the engines, and one test conversion with the network cut shows that nothing is downloaded (read from the research; not run).

## Egress switches

| Connection | Default | Switch | Source |
|---|---|---|---|
| Remote services (documents sent to an outside API) | off | keep `DOCLING_SERVE_ENABLE_REMOTE_SERVICES=false` | https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/configuration.md |
| Bundled web UI | off | keep `DOCLING_SERVE_ENABLE_UI=false` | https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/configuration.md |
| Metrics (`/metrics`, served locally only) | on (`DOCLING_SERVE_OTEL_ENABLE_METRICS` and `_PROMETHEUS` true; traces and OTLP export false) | nothing leaves the host; keep traces and OTLP export off | https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/configuration.md |
| Model download at start | only when `DOCLING_SERVE_ARTIFACTS_PATH` is empty | keep the baked path or mount a staged one; missing models raise errors instead of downloading | https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/models.md |

No telemetry or update check is documented for docling-serve or for the Docling library.

## Caveats

- OCR languages in the stock image:
  - EasyOCR has `english_g2` and `latin_g2` baked in, and its Latin list includes `tr`, `de` and `fr`: confirmed from source (https://raw.githubusercontent.com/JaidedAI/EasyOCR/v1.7.2/easyocr/config.py).
  - RapidOCR's baked `ch` model resolves to the multilingual `multi_PP-OCRv6_rec_small`, which lists `tr`, `de`, `fr` and about 40 more: inferred from the RapidOCR YAML, not run; recognition quality for diacritics was not tested. RapidOCR reads one language per conversion.
  - Tesseract has English and OSD data only: any other language fails offline.
  - Cyrillic, Arabic, Devanagari, Thai, Greek and Korean models are not baked in; they must be staged.
- Missing models raise errors instead of downloading, and the error can surface inside an HTTP 200 response; Open WebUI shows a `failure` or `skipped` status as the file's error.
- The `code_formula` model and the VLMs are not baked into the image; the skill does not use them.
- The stock images were not pulled for the research: the baked-model list comes from the Containerfile at the tag. Verify with the check inside the network.
- Open WebUI does not use Docling's chunk endpoints: it requests `md` and `json`, reads the markdown, and splits it again with its own splitter. Docling's heading hierarchy (the `do_pdf_heading_hierarchy` option) decides whether Open WebUI's header splitter finds headings; not tested on real documents.
- Throughput with OCR on (4,008 pages, EasyOCR): 3.1 s per page on an 8-vCPU EPYC, 0.49 s on an L4 GPU, 1.27 s on an M3 Max; turning OCR off saves 50 to 60 percent (https://arxiv.org/html/2501.17887). Peak memory is about 6.2 GB at 4 threads (https://arxiv.org/html/2408.09869).
- Conversion on the connected side may only handle public documents; documents from inside the network never leave it.

## Carry in

### Images

| Image | Hardware | Digest |
|---|---|---|
| `quay.io/docling-project/docling-serve-cpu:v1.39.0` (4.4 GB) | amd64, arm64 | not recorded |
| `quay.io/docling-project/docling-serve-cu128:v1.39.0` (11.4 GB) | amd64, GPU | not recorded |

`:v1.39.0` is a multi-arch manifest list on Quay (https://quay.io/api/v1/repository/docling-project/docling-serve-cpu/tag/?specificTag=v1.39.0). The plain `docling-serve` image is 8.7 GB on amd64 and 4.4 GB on arm64; `-cu130` exists for amd64 and arm64. CUDA images have no `latest` tag.

### Models

Baked into the image, nothing to carry for the default setup:

| Model | Size | License | Source |
|---|---|---|---|
| layout (`docling-layout-heron`) | 171.7 MB | Apache-2.0 | https://huggingface.co/api/models/docling-project/docling-layout-heron?blobs=true |
| tableformer (accurate 212.8 MB, fast 145.5 MB) | 358.3 MB together | CDLA-Permissive-2.0 and Apache-2.0 tags | https://huggingface.co/api/models/docling-project/docling-models?blobs=true |
| picture_classifier (`DocumentFigureClassifier-v2.5`) | 16.4 MB | MIT | https://huggingface.co/api/models/docling-project/DocumentFigureClassifier-v2.5?blobs=true |
| rapidocr (`ch`, torch and onnxruntime) | not documented | not documented | https://raw.githubusercontent.com/docling-project/docling/main/docling/utils/model_downloader.py |
| easyocr (`english_g2`, `latin_g2`) | not documented | not documented | https://raw.githubusercontent.com/docling-project/docling/main/docling/utils/model_downloader.py |

Extra models, such as other OCR languages, are fetched on a connected machine with `docling-tools models download --output-dir DIR` and mounted at `DOCLING_SERVE_ARTIFACTS_PATH` (https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/models.md).

### Runtime downloads to stage in advance

| What | Needed | Source |
|---|---|---|
| `code_formula` model and the VLMs | not used | https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/models.md |
| EasyOCR models for other scripts (`cyrillic_g2`, `arabic_g1`, ...) | only when those languages are in the documents | https://raw.githubusercontent.com/docling-project/docling/main/docling/utils/model_downloader.py |

### Telemetry and egress to switch off before the first start

All rows of Egress switches; keep the defaults and set the two switches explicitly in the container environment.

## Evidence

- https://api.github.com/repos/docling-project/docling-serve/releases/latest
- https://github.com/docling-project/docling-serve
- https://quay.io/api/v1/repository/docling-project/docling-serve-cpu/tag/?specificTag=v1.39.0
- https://raw.githubusercontent.com/docling-project/docling-serve/main/Containerfile
- https://raw.githubusercontent.com/docling-project/docling-serve/main/os-packages.txt
- https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/configuration.md
- https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/models.md
- https://raw.githubusercontent.com/docling-project/docling-serve/main/docs/usage.md
- https://raw.githubusercontent.com/docling-project/docling/main/docling/utils/model_downloader.py
- https://docling-project.github.io/docling/usage/model_catalog
- https://docs.openwebui.com/features/chat-conversations/rag/document-extraction/docling.md
- https://docs.openwebui.com/reference/env-configuration
- https://raw.githubusercontent.com/RapidAI/RapidOCR/v3.10.0/python/rapidocr/default_models.yaml
- https://arxiv.org/html/2501.17887
- https://arxiv.org/html/2408.09869
