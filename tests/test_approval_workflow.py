import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.models.candidate import Candidate
from app.models.employment import EmploymentRecord
from app.models.skill import SkillRecord

# Use a test SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_app.db"
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_approve_candidate_success():
    async with TestingSessionLocal() as db:
        candidate_id = str(uuid.uuid4())
        candidate = Candidate(
            id=candidate_id,
            status="EXTRACTED",
            original_filename="test.docx",
            original_file_path="/tmp/test.docx",
            needs_review=True
        )
        db.add(candidate)
        # Add 1 reviewed item
        emp = EmploymentRecord(candidate_id=candidate_id, job_title="Dev", company_name="TestCorp", needs_review=False)
        db.add(emp)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/candidates/{candidate_id}/approve?approved_by=tester")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "tester"

    async with TestingSessionLocal() as db:
        c = await db.get(Candidate, candidate_id)
        assert c.status == "APPROVED"
        assert c.needs_review is False

@pytest.mark.asyncio
async def test_approve_candidate_blocked_by_review():
    async with TestingSessionLocal() as db:
        candidate_id = str(uuid.uuid4())
        candidate = Candidate(
            id=candidate_id,
            status="EXTRACTED",
            original_filename="test.docx",
            original_file_path="/tmp/test.docx",
            needs_review=True
        )
        db.add(candidate)
        # Add 1 unreviewed item
        emp = EmploymentRecord(candidate_id=candidate_id, job_title="Dev", company_name="TestCorp", needs_review=True)
        db.add(emp)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/candidates/{candidate_id}/approve?approved_by=tester")
    
    assert response.status_code == 400
    data = response.json()
    assert "1 items still need review" in data["detail"]["error"]
    assert len(data["detail"]["unreviewed_employment_ids"]) == 1

@pytest.mark.asyncio
async def test_approve_candidate_invalid_status():
    async with TestingSessionLocal() as db:
        candidate_id = str(uuid.uuid4())
        candidate = Candidate(
            id=candidate_id,
            status="UPLOADED",
            original_filename="test.docx",
            original_file_path="/tmp/test.docx"
        )
        db.add(candidate)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/candidates/{candidate_id}/approve")
    
    assert response.status_code == 400
    assert "Can only approve EXTRACTED candidates" in response.json()["detail"]
