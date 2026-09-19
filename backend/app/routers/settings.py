from fastapi import APIRouter, HTTPException

from app.schemas.settings import SettingsUpdate
from app.services.metro_service import MetroService

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings():
    with MetroService() as s:
        return s.settings()


@router.put("/settings")
def put_settings(body: SettingsUpdate):
    with MetroService() as s:
        try:
            return s.update_min_fare(body.min_fare)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
