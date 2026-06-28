"""Blueprint API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth import require_admin, require_read
from database import get_db
from observability.logging import log_operation
from services.blueprint_service import BlueprintService

router = APIRouter(prefix="/blueprints", tags=["blueprints"])


class SaveBlueprintRequest(BaseModel):
    content: dict[str, Any]


@router.get("")
def list_blueprints(db: Session = Depends(get_db), role: str = Depends(require_read)):
    service = BlueprintService(db)
    return service.list_available()


@router.get("/{name}")
def get_blueprint(name: str, db: Session = Depends(get_db), role: str = Depends(require_read)):
    service = BlueprintService(db)
    blueprint = service.load(name)
    return blueprint.model_dump()


@router.post("/{name}")
def save_blueprint(
    name: str,
    request: SaveBlueprintRequest,
    db: Session = Depends(get_db),
    role: str = Depends(require_admin),
):
    """Save or update a custom blueprint."""
    service = BlueprintService(db)
    try:
        service.save_custom(name, request.content)
        log_operation("blueprint.saved", name=name, actor="api")
        return {"message": f"Blueprint '{name}' saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save blueprint: {e}") from e
