# src/orbit_cv/middleware/rlm_context.py
import asyncio
import base64
import io
import os
import re
import traceback
from docx import Document
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage
from pypdf import PdfReader

from orbit_cv.paths import RESUMES_DIR, resolve_path

# Canonical path resolved through central path utility
CANONICAL_CV_PATH = resolve_path("candidate_cv.txt", default_route="resumes")


def _clean_and_decode_b64(b64_str: str) -> bytes:
    """Strips headers, whitespace, and padding to decode raw base64 bytes."""
    cleaned = re.sub(r"\s+", "", b64_str.strip().strip("'\""))
    if "," in cleaned:
        cleaned = cleaned.split(",", 1)[1]
    missing_padding = len(cleaned) % 4
    if missing_padding:
        cleaned += "=" * (4 - missing_padding)
    return base64.b64decode(cleaned)


def _extract_text_from_bytes(file_bytes: bytes, filename: str = "") -> str:
    """Attempts PDF, DOCX, and plain text extraction from binary stream."""
    # 1. Try PDF parsing
    try:
        reader = PdfReader(io.BytesIO(file_bytes), strict=False)
        pages_text = [
            page.extract_text() for page in reader.pages if page.extract_text()
        ]
        if pages_text:
            return "\n".join(pages_text)
    except Exception:
        pass

    # 2. Try DOCX parsing
    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        if paragraphs:
            return "\n".join(paragraphs)
    except Exception:
        pass

    # 3. Fallback to UTF-8 text decode
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return f"[Unable to extract readable text from attached file: {filename}]"


def _sync_write_file(text: str) -> bool:
    """Synchronous worker function executing filesystem operations on a background thread."""
    try:
        RESUMES_DIR.mkdir(parents=True, exist_ok=True)
        with open(CANONICAL_CV_PATH, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        print(f"[RLMContextMiddleware ERROR] Write to disk failed: {e}")
        traceback.print_exc()
        return False


async def _save_extracted_text_to_disk_async(text: str) -> bool:
    """Non-blocking wrapper using asyncio.to_thread to offload file I/O."""
    return await asyncio.to_thread(_sync_write_file, text)


class RLMContextMiddleware(AgentMiddleware):
    name: str = "rlm_context"

    def __init__(self, storage_path: str = "/context/"):
        super().__init__()
        self.storage_path = storage_path

    async def _sanitize_request_messages_async(self, request):
        messages = getattr(request, "messages", [])
        if not messages:
            return request

        sanitized_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage) and isinstance(msg.content, list):
                new_content = []
                for block in msg.content:
                    if isinstance(block, dict):
                        # Extract potential file/base64 payload fields
                        data_candidates = [
                            block.get("data"),
                            block.get("url"),
                            block.get("path"),
                            block.get("content"),
                            block.get("base64"),
                        ]

                        payload = next(
                            (c for c in data_candidates if isinstance(c, str) and c.strip()),
                            None,
                        )
                        filename = block.get("name") or block.get("filename") or "uploaded_doc"

                        if payload and (
                            payload.startswith("data:")
                            or payload.startswith("JVBERi")
                            or payload.startswith("UEsDB")
                            or len(payload) > 200  # High probability of Base64 payload
                        ):
                            try:
                                file_bytes = _clean_and_decode_b64(payload)
                                extracted_text = _extract_text_from_bytes(file_bytes, filename)

                                # Execute thread-offloaded disk write
                                written = await _save_extracted_text_to_disk_async(extracted_text)

                                if written and CANONICAL_CV_PATH.exists():
                                    note = f"[System Note: Raw text extracted and saved to disk at {CANONICAL_CV_PATH}]\n\n"
                                else:
                                    note = f"[System Note: Raw text extracted, BUT FAILED TO SAVE TO DISK at {CANONICAL_CV_PATH}]\n\n"

                                new_content.append({
                                    "type": "text",
                                    "text": (
                                        f"\n--- START ATTACHED RESUME / DOCUMENT ({filename}) ---\n"
                                        f"{note}"
                                        f"{extracted_text}\n"
                                        f"--- END ATTACHED RESUME / DOCUMENT ---\n"
                                    ),
                                })
                                continue
                            except Exception as e:
                                print(f"[RLMContextMiddleware Exception]: {e}")
                                traceback.print_exc()

                        new_content.append(block)
                    else:
                        new_content.append(block)
                msg.content = new_content
            sanitized_messages.append(msg)

        request.messages = sanitized_messages
        return request

    def wrap_model_call(self, request, handler):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Create sub-task if already executing on an active event loop
            future = asyncio.run_coroutine_threadsafe(
                self._sanitize_request_messages_async(request), loop
            )
            request = future.result()
        else:
            request = asyncio.run(self._sanitize_request_messages_async(request))

        return handler(request)

    async def awrap_model_call(self, request, handler):
        request = await self._sanitize_request_messages_async(request)
        return await handler(request)

    def __call__(self, state, next_fn):
        return next_fn(state)