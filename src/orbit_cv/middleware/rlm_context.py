from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage

from orbit_cv.parsers.document_parser import clean_and_decode_b64, extract_text_from_bytes
from orbit_cv.services.resume_storage import CANONICAL_CV_PATH, save_extracted_resume_async


class RLMContextMiddleware(AgentMiddleware):
    name: str = "rlm_context"

    async def _process_payload_block(self, block: dict) -> dict | None:
        """Processes an individual block within content lists."""
        data_candidates = [
            block.get("data"),
            block.get("url"),
            block.get("path"),
            block.get("content"),
            block.get("base64"),
        ]
        payload = next((c for c in data_candidates if isinstance(c, str) and c.strip()), None)
        filename = block.get("name") or block.get("filename") or "uploaded_doc"

        # Check if payload is base64 document
        if payload and (
            payload.startswith("data:")
            or payload.startswith("JVBERi")  # PDF magic header
            or payload.startswith("UEsDB")  # DOCX/Zip magic header
            or len(payload) > 200
        ):
            try:
                file_bytes = clean_and_decode_b64(payload)
                extracted_text = extract_text_from_bytes(file_bytes, filename)
                written = await save_extracted_resume_async(extracted_text)

                status_note = (
                    f"[System Note: Raw text extracted and saved to disk at {CANONICAL_CV_PATH}]\n\n"
                    if written
                    else f"[System Note: Raw text extracted, BUT FAILED TO SAVE TO DISK at {CANONICAL_CV_PATH}]\n\n"
                )

                return {
                    "type": "text",
                    "text": (
                        f"\n--- START ATTACHED RESUME / DOCUMENT ({filename}) ---\n"
                        f"{status_note}"
                        f"{extracted_text}\n"
                        f"--- END ATTACHED RESUME / DOCUMENT ---\n"
                    ),
                }
            except Exception as e:
                print(f"[RLMContextMiddleware Exception]: {e}")
        return block

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
                        processed_block = await self._process_payload_block(block)
                        new_content.append(processed_block)
                    else:
                        new_content.append(block)
                msg.content = new_content
            sanitized_messages.append(msg)

        request.messages = sanitized_messages
        return request

    async def awrap_model_call(self, request, handler):
        request = await self._sanitize_request_messages_async(request)
        return await handler(request)

    def wrap_model_call(self, request, handler):
        # Sync wrapper delegation
        import asyncio
        request = asyncio.run(self._sanitize_request_messages_async(request))
        return handler(request)