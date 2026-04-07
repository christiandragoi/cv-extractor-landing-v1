import os
import shutil
from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database import get_db
from app.models.template import Template
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

class TemplateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    template_type: str
    file_size: str
    is_active: bool
    fields: List[str]
    created_at: datetime

@router.get("/", response_model=List[TemplateSchema])
async def get_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).order_by(Template.created_at.desc()))
    return result.scalars().all()

@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    template_type: str = Form("lebenslauf"),
    db: AsyncSession = Depends(get_db)
):
    # Ensure resources directory exists
    upload_dir = os.path.join("app", "resources", "templates")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = f"{os.path.getsize(file_path) / 1024:.0f} KB"
    
    # Mock fields extraction logic from React
    default_fields = ["Name", "Beruf", "Erfahrung", "Ausbildung", "Zertifikate", "Sprachen"]
    
    new_template = Template(
        id=uuid4(),
        name=file.filename,
        template_type=template_type,
        file_path=file_path,
        file_size=file_size,
        is_active=False,
        fields=default_fields
    )
    
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)
    return new_template

@router.patch("/{id}/active")
async def set_active_template(id: str, db: AsyncSession = Depends(get_db)):
    # Deactivate all others
    await db.execute(update(Template).values(is_active=False))
    # Activate target
    await db.execute(update(Template).where(Template.id == id).values(is_active=True))
    await db.commit()
    return {"status": "success"}

@router.delete("/{id}")
async def delete_template(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).where(Template.id == id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if os.path.exists(template.file_path):
        os.remove(template.file_path)
        
    await db.execute(delete(Template).where(Template.id == id))
    await db.commit()
    return {"status": "success"}
