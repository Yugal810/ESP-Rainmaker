from fastapi import APIRouter, HTTPException
from models import OTAUpdateCheck, OTARegistration, OTAUpdateResponse, OTARegistrationResponse
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/ota", tags=["OTA"])

# Load OTA server configuration from environment variables
OTA_SERVER_URL = os.getenv("OTA_SERVER_URL", "http://127.0.0.1:8001")
OTA_API_KEY = os.getenv("OTA_API_KEY")

@router.post("/check-update", response_model=OTAUpdateResponse)
async def check_update(update_check_data: OTAUpdateCheck):
    try:
        async with httpx.AsyncClient() as client:
            # Get latest version from OTA server
            response = await client.get(
                f"{OTA_SERVER_URL}/version",
                headers={"X-API-Key": OTA_API_KEY}
            )
            response.raise_for_status()
            latest_version = response.json().get("version")
            
            # Compare versions
            update_available = latest_version > update_check_data.current_version
            
            return OTAUpdateResponse(
                update_available=update_available,
                new_version=latest_version if update_available else "",
                download_url=f"{OTA_SERVER_URL}/firmware" if update_available else ""
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OTA server: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/register-device", response_model=OTARegistrationResponse)
async def register_device(registration_data: OTARegistration):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OTA_SERVER_URL}/device/register",
                headers={"X-API-Key": OTA_API_KEY},
                json={
                    "device_id": registration_data.device_id,
                    "device_type": registration_data.device_type,
                    "firmware_version": registration_data.current_version
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return OTARegistrationResponse(
                registration_status=data.get("status") == "success",
                device_token=""  # OTA server doesn't provide a token
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OTA server: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") 