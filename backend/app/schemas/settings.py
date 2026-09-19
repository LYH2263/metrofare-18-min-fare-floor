from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    floor_fare: float | None = None
