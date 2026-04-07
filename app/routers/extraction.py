"""
Extraction Router - Main CV extraction + template population endpoint.

Flow:
1. Upload template (DOCX) + CV (PDF/DOCX/JPEG) + optional instructions
2. AI extracts structured data from CV using the master prompt + custom instructions
3. Template is populated with the extracted data using python-docx
4. Populated DOCX is returned for download
"""

import json
import logging
import uuid
import tempfile
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.services.template_population_service import (
    TemplatePopulationService,
    WELDER_MASTER_PROMPT,
    extract_text_from_bytes,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory task storage (simple approach; use DB for production)
_tasks = {}


class ExtractionResult(BaseModel):
    task_id: str
    status: str
    candidate_name: Optional[str] = None
    error: Optional[str] = None
    download_url: Optional[str] = None


async def _call_ai_for_extraction(
    cv_text: str,
    custom_instructions: str = "",
    model: str = "gpt-4o"
) -> dict:
    """
    Call the AI provider to extract structured data from CV text.
    Uses the existing ProviderManager from the app.
    """
    from app.ai.provider_manager import ProviderManager
    from app.database import AsyncSessionLocal

    pm = ProviderManager()

    # Build the prompt
    system_prompt = WELDER_MASTER_PROMPT
    if custom_instructions:
        system_prompt += f"\n\nZUSÄTZLICHE ANWEISUNGEN DES OPERATORS:\n{custom_instructions}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extrahiere die folgenden CV-Daten:\n\n{cv_text[:8000]}"}
    ]

    # Use the provider manager with a session for key access
    async with AsyncSessionLocal() as session:
        raw_response, provider_name, model_used = await pm.try_extraction(messages, session)

    # Parse JSON from response
    import re
    # Try to find JSON in the response
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if not json_match:
        raise ValueError(f"AI returned no valid JSON: {raw_response[:500]}")

    result = json.loads(json_match.group())
    logger.info(f"AI extraction completed using {provider_name} ({model_used})")
    return result


async def _call_ai_vision_for_extraction(
    image_path: str,
    custom_instructions: str = "",
    model: str = "gpt-4o"
) -> dict:
    """
    Call the AI with vision capability to extract data from a CV image.
    """
    import base64
    from app.ai.provider_manager import ProviderManager
    from app.database import AsyncSessionLocal

    pm = ProviderManager()

    system_prompt = WELDER_MASTER_PROMPT
    if custom_instructions:
        system_prompt += f"\n\nZUSÄTZLICHE ANWEISUNGEN DES OPERATORS:\n{custom_instructions}"

    # Read and encode image
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    suffix = Path(image_path).suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png"
    }.get(suffix, "image/jpeg")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Extrahiere die Daten aus diesem Lebenslauf. {system_prompt}"},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
            ]
        }
    ]

    async with AsyncSessionLocal() as session:
        raw_response, provider_name, model_used = await pm.try_extraction(messages, session)

    import re
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if not json_match:
        raise ValueError(f"AI returned no valid JSON: {raw_response[:500]}")

    result = json.loads(json_match.group())
    return result


@router.post("/process", response_model=ExtractionResult)
async def process_extraction(
    template: UploadFile = File(..., description="Word template (.docx)"),
    cv_file: UploadFile = File(..., description="Candidate CV (PDF/DOCX/JPEG)"),
    instructions: Optional[str] = Form("", description="Custom extraction instructions"),
    ai_model: Optional[str] = Form("gpt-4o", description="AI model to use"),
):
    """
    Main extraction endpoint:
    1. Save uploaded files temporarily
    2. Extract text from CV
    3. Call AI for structured data extraction
    4. Populate template with extracted data
    5. Return populated document
    """
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {"status": "processing"}

    try:
        # Save uploaded files
        template_bytes = await template.read()
        cv_bytes = await cv_file.read()
        cv_filename = cv_file.filename or "cv.pdf"

        # Save template to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_tpl:
            tmp_tpl.write(template_bytes)
            template_path = tmp_tpl.name

        # Save CV to temp file
        cv_suffix = Path(cv_filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=cv_suffix) as tmp_cv:
            tmp_cv.write(cv_bytes)
            cv_path = tmp_cv.name

        try:
            # Extract text from CV
            cv_text = extract_text_from_bytes(cv_bytes, cv_filename)

            # Handle image CVs
            if cv_text.startswith("__IMAGE_FILE__"):
                data = await _call_ai_vision_for_extraction(cv_path, instructions or "", ai_model)
            else:
                # Call AI for extraction
                data = await _call_ai_for_extraction(cv_text, instructions or "", ai_model)

            # Populate template
            populator = TemplatePopulationService(template_path)
            output_bytes = populator.get_bytes(data)

            # Save output
            candidate_name = data.get("candidate", {}).get("full_name", "candidate")
            output_filename = f"{candidate_name}_Lebenslauf.docx".replace(" ", "_")

            output_dir = Path("storage_local/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{task_id}_{output_filename}"

            with open(output_path, "wb") as f:
                f.write(output_bytes)

            _tasks[task_id] = {
                "status": "completed",
                "candidate_name": candidate_name,
                "download_url": f"/api/v1/extraction/download/{task_id}",
                "output_path": str(output_path),
                "data": data,
            }

            return ExtractionResult(
                task_id=task_id,
                status="completed",
                candidate_name=candidate_name,
                download_url=f"/api/v1/extraction/download/{task_id}",
            )

        finally:
            # Cleanup temp files
            try:
                os.unlink(template_path)
            except OSError:
                pass
            try:
                os.unlink(cv_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Extraction failed for task {task_id}: {e}")
        _tasks[task_id] = {"status": "failed", "error": str(e)}
        return ExtractionResult(
            task_id=task_id,
            status="failed",
            error=str(e),
        )


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """Download the populated template."""
    task = _tasks.get(task_id)
    if not task or task.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Result not found or not completed")

    output_path = task.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="File not found")

    candidate_name = task.get("candidate_name", "candidate")
    return FileResponse(
        path=output_path,
        filename=f"{candidate_name}_Lebenslauf.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/status/{task_id}", response_model=ExtractionResult)
async def get_status(task_id: str):
    """Check extraction task status."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ExtractionResult(
        task_id=task_id,
        status=task.get("status", "unknown"),
        candidate_name=task.get("candidate_name"),
        error=task.get("error"),
        download_url=task.get("download_url"),
    )


@router.get("/preview/{task_id}")
async def preview_result(task_id: str):
    """Preview extracted data (JSON) before downloading."""
    task = _tasks.get(task_id)
    if not task or task.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Result not found or not completed")
    return JSONResponse(content=task.get("data", {}))
