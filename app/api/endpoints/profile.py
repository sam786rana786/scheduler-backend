import datetime
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pytz import common_timezones, timezone
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
import json
import os
from ...db.database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...models.profile import Profile as ProfileModel
from ...schemas.profile import Profile, ProfileUpdate, TimezoneResponse

router = APIRouter()

@router.get("/me", response_model=Profile)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.id).first()
    if not profile:
        # Create default profile if none exists
        profile = ProfileModel(
            user_id=current_user.id,
            time_zone="UTC"  # Default timezone
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return Profile(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        scheduling_url=profile.scheduling_url,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        welcome_message=profile.welcome_message,
        company_logo=profile.company_logo,
        phone=profile.phone,
        job_title=profile.job_title,
        full_name=profile.full_name,
        company=profile.company,
        time_zone=profile.time_zone
    )

@router.put("/me")
async def update_profile(
    profile_data: str = Form(...),
    company_logo: Optional[UploadFile] = None,
    avatar: Optional[UploadFile] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Parse the profile_data JSON string
        try:
            profile_data_dict = json.loads(profile_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=422,
                detail="Invalid JSON in profile_data"
            )

        # Get or create profile
        profile = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.id).first()
        if not profile:
            profile = ProfileModel(user_id=current_user.id)
            db.add(profile)

        # Update profile fields
        for key, value in profile_data_dict.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        # Handle file upload for company logo
        if company_logo:
            os.makedirs("uploads/logo", exist_ok=True)
            file_path = f"uploads/logo/{company_logo.filename}"
            with open(file_path, "wb") as buffer:
                content = await company_logo.read()
                buffer.write(content)
            profile.company_logo = f"/uploads/logo/{company_logo.filename}"

        # Handle file upload for avatar
        if avatar:
            os.makedirs("uploads/avatars", exist_ok=True)
            file_path = f"uploads/avatars/{avatar.filename}"
            with open(file_path, "wb") as buffer:
                content = await avatar.read()
                buffer.write(content)
            profile.avatar_url = f"/uploads/avatars/{avatar.filename}"

        try:
            db.commit()
            db.refresh(profile)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

        return Profile(
            id=profile.id,
            user_id=profile.user_id,
            email=current_user.email,
            scheduling_url=profile.scheduling_url,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            welcome_message=profile.welcome_message,
            company_logo=profile.company_logo,
            phone=profile.phone,
            job_title=profile.job_title,
            full_name=profile.full_name,
            company=profile.company,
            time_zone=profile.time_zone
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
@router.get("/timezones", response_model=List[TimezoneResponse])
def get_timezones():
    timezone_choices = []
    for tz in common_timezones:
        timezone_choices.append(TimezoneResponse(label=f"{tz.replace('_', ' ')} ({tz})", value=tz))
    return timezone_choices