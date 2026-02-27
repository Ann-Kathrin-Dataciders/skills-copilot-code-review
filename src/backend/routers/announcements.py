"""
Endpoints for Announcements Management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from ..database import announcements_collection
from ..routers.auth import get_current_user

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def announcement_serializer(doc):
    return {
        "id": str(doc.get("_id", "")),
        "message": doc["message"],
        "start_date": doc.get("start_date"),
        "expiration_date": doc["expiration_date"]
    }


@router.get("", response_model=List[dict])
def list_announcements():
    """List all announcements (not expired)"""
    now = datetime.now()
    docs = announcements_collection.find(
        {
            "expiration_date": {"$gte": now},
            "$or": [
                {"start_date": {"$lte": now}},
                {"start_date": None},
            ],
        }
    )
    return [announcement_serializer(doc) for doc in docs]


@router.post("", response_model=dict)
def create_announcement(message: str, expiration_date: datetime, start_date: Optional[datetime] = None, user=Depends(get_current_user)):
    """Create a new announcement (auth required)"""

    doc = {
        "message": message,
        "expiration_date": expiration_date,
    }
    if start_date:
        doc["start_date"] = start_date
    result = announcements_collection.insert_one(doc)
    return {"id": str(result.inserted_id)}


@router.put("/{announcement_id}", response_model=dict)
def update_announcement(announcement_id: str, message: Optional[str] = None, expiration_date: Optional[datetime] = None, start_date: Optional[datetime] = None, user=Depends(get_current_user)):
    """Update an announcement (auth required)"""
    update = {}
    if message is not None:
        update["message"] = message
    if expiration_date is not None:
        update["expiration_date"] = expiration_date
    if start_date is not None:
        update["start_date"] = start_date
    if not update:
        raise HTTPException(status_code=400, detail="No update fields provided")
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"updated": True}


@router.delete("/{announcement_id}", response_model=dict)
def delete_announcement(announcement_id: str, user=Depends(get_current_user)):
    """Delete an announcement (auth required)"""
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"deleted": True}
