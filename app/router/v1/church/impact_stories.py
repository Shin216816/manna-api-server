from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.controller.church.impact_stories import (
    create_impact_story, get_church_impact_stories, get_impact_story,
    update_impact_story, delete_impact_story, publish_impact_story
)
from app.utils.database import get_db
from app.middleware.church_admin_auth import church_admin_auth
from app.core.responses import SuccessResponse

impact_stories_router = APIRouter(tags=["Church Impact Stories"])

@impact_stories_router.post("/create", response_model=SuccessResponse)
async def create_impact_story_route(
    story_data: dict = Body(...),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    return create_impact_story(current_user["church_id"], story_data, db)

@impact_stories_router.get("/list", response_model=SuccessResponse)
async def get_church_impact_stories_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    return get_church_impact_stories(current_user["church_id"], db, page, limit)

@impact_stories_router.get("/test", response_model=SuccessResponse)
async def test_impact_stories_endpoint(
    db: Session = Depends(get_db)
):
    """Test endpoint without authentication"""
    from app.core.responses import ResponseFactory
    return ResponseFactory.success(
        message="Impact stories endpoint is working",
        data={"test": True, "endpoint": "impact-stories"}
    )

@impact_stories_router.post("/{story_id}/publish", response_model=SuccessResponse)
async def publish_impact_story_route(
    story_id: int,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    return publish_impact_story(story_id, current_user["church_id"], db)

@impact_stories_router.get("/{story_id}", response_model=SuccessResponse)
async def get_impact_story_route(
    story_id: int,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    return get_impact_story(story_id, current_user["church_id"], db)

@impact_stories_router.put("/{story_id}", response_model=SuccessResponse)
async def update_impact_story_route(
    story_id: int,
    story_data: dict = Body(...),
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    return update_impact_story(story_id, current_user["church_id"], story_data, db)

@impact_stories_router.delete("/{story_id}", response_model=SuccessResponse)
async def delete_impact_story_route(
    story_id: int,
    current_user: dict = Depends(church_admin_auth),
    db: Session = Depends(get_db)
):
    return delete_impact_story(story_id, current_user["church_id"], db)
