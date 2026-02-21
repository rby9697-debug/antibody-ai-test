from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.validation.project_health import validate_project_integrity

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}/health")
def get_project_health(project_id: str, db: Session = Depends(get_db)) -> dict:
    return validate_project_integrity(project_id=project_id, db=db)
