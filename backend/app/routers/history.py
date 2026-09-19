from fastapi import APIRouter, HTTPException
from app.services.metro_service import MetroService

router = APIRouter(tags=["history"])


@router.get("/history")
def history(limit: int = 50):
    with MetroService() as s:
        return {"items": s.history(limit)}


@router.get("/history/{run_id}")
def history_run(run_id: int):
    with MetroService() as s:
        row = s.history_run(run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="记录不存在")
        return row
