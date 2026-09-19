from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    min_fare: float
