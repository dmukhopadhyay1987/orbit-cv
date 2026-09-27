import asyncio
import os
import traceback
from pathlib import Path
from orbit_cv.paths import RESUMES_DIR, resolve_path

CANONICAL_CV_PATH = resolve_path("candidate_cv.txt", default_route="resumes")


def sync_write_resume(text: str, target_path: Path = CANONICAL_CV_PATH) -> bool:
    """Synchronous file write to disk."""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        print(f"[ResumeStorage ERROR] Write to disk failed: {e}")
        traceback.print_exc()
        return False


async def save_extracted_resume_async(text: str, target_path: Path = CANONICAL_CV_PATH) -> bool:
    """Non-blocking async wrapper offloading disk I/O."""
    return await asyncio.to_thread(sync_write_resume, text, target_path)