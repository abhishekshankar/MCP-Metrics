"""Blueprint API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.auth import require_read
from database import get_db
from services.blueprint_service import BlueprintService

router = APIRouter(prefix="/blueprints", tags=["blueprints"])


@router.get("")
def list_blueprints(db: Session = Depends(get_db), role: str = Depends(require_read)):
    service = BlueprintService(db)
    return service.list_available()


@router.get("/{name}")
def get_blueprint(name: str, db: Session = Depends(get_db), role: str = Depends(require_read)):
    service = BlueprintService(db)
    blueprint = service.load(name)
    return blueprint.model_dump()
