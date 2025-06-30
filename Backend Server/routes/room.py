from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from typing import Optional
from database import db
from routes.auth import get_current_user

router = APIRouter()

class Room(BaseModel):
    name: str
    description: Optional[str] = None

@router.post("/room/add")
def add_room(room: Room, current_user: str = Depends(get_current_user)):
    result = db.users.update_one(
        {"email": current_user},
        {"$push": {"rooms": room.dict()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Room added to user"}

@router.get("/rooms")
def get_rooms(current_user: str = Depends(get_current_user)):
    user = db.users.find_one({"email": current_user})
    if not user or "rooms" not in user:
        return []
    return user["rooms"]

@router.delete("/room/delete/{room_name}")
def delete_room(room_name: str = Path(...), current_user: str = Depends(get_current_user)):
    result = db.users.update_one(
        {"email": current_user},
        {"$pull": {"rooms": {"name": room_name}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Room not found or already deleted")
    return {"message": "Room and its devices deleted"} 