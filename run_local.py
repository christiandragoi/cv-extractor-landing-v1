"""
Local launcher for CV Extractor Phase 1 API.
Uses SQLite - no PostgreSQL or Redis needed!
"""
import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).parent
VENV = BASE / ".venv-local"
PY = sys.executable


def run(cmd, **kwargs):
    print(f"\n> {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    return subprocess.run(cmd, **kwargs)


def ensure_venv():
    pip = VENV / "Scripts" / "pip.exe"
    python = VENV / "Scripts" / "python.exe"

    if not VENV.exists():
        print("Creating virtual environment...")
        run([PY, "-m", "venv", str(VENV)], check=True)

    print("Installing local requirements...")
    run([str(pip), "install", "--quiet", "-r", str(BASE / "requirements.local.txt")], check=True)
    return str(python)


if __name__ == "__main__":
    os.chdir(BASE)

    python_bin = ensure_venv()
    uvicorn_bin = str(VENV / "Scripts" / "uvicorn.exe")

    # Copy .env.local → .env for this session
    env_local = BASE / ".env.local"
    env_file = BASE / ".env"
    if env_local.exists() and not env_file.exists():
        import shutil
        shutil.copy(env_local, env_file)
        print("Copied .env.local → .env")
    elif not env_file.exists():
        print("WARNING: No .env file found. Creating minimal .env ...")
        env_file.write_text(
            "ENVIRONMENT=development\n"
            "SECRET_KEY=local-dev-secret\n"
            "DATABASE_URL=sqlite+aiosqlite:///./cv_extractor_local.db\n"
            "REDIS_URL=redis://localhost:6379/0\n"
            "STORAGE_ROOT=./storage_local\n"
            "CORS_ORIGINS=http://localhost:3000,http://localhost:8001\n"
        )

    # Create storage dir
    (BASE / "storage_local").mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("  CV Extractor Phase 1 API - Local Dev Server")
    print("="*60)
    print("  URL:     http://localhost:8001")
    print("  Docs:    http://localhost:8001/docs")
    print("  Health:  http://localhost:8001/api/v1/health")
    print("="*60)
    print("  Database: SQLite (cv_extractor_local.db)")
    print("  No PostgreSQL or Redis required!")
    print("="*60 + "\n")

    run([
        uvicorn_bin, "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload",
        "--reload-dir", str(BASE / "app"),
        "--log-level", "info"
    ])
