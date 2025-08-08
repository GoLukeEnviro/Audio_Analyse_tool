from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json
from config.settings import settings

router = APIRouter()

class ConfigUpdate(BaseModel):
    config: Dict[str, Any]

@router.get("/config/settings", summary="Get current backend configuration settings")
async def get_config_settings():
    """
    Retrieves the current backend configuration settings.
    """
    return settings.config

@router.put("/config/settings", summary="Update backend configuration settings")
async def update_config_settings(config_update: ConfigUpdate):
    """
    Updates the backend configuration settings.
    """
    try:
        # Deep merge the incoming config with the current config
        # This ensures that only provided keys are updated, and nested structures are handled
        settings.config = settings._deep_merge(settings.config, config_update.config)
        settings.save_config()
        return {"message": "Configuration updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {e}")