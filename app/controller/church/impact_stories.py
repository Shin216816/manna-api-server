from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from sqlalchemy import func

from app.model.m_church import Church
from app.model.m_impact_story import ImpactStory
from app.core.messages import get_auth_message
from app.core.responses import ResponseFactory, SuccessResponse


def create_impact_story(
    church_id: int, story_data: dict, db: Session
) -> SuccessResponse:
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        story = ImpactStory(
            church_id=church_id,
            title=story_data["title"],
            description=story_data["description"],
            amount_used=story_data["amount_used"],
            category=story_data["category"],
            status=story_data.get("status", "draft"),
            image_url=story_data.get("image_url"),
            people_impacted=story_data.get("people_impacted", 0),
            events_held=story_data.get("events_held", 0),
            items_purchased=story_data.get("items_purchased", 0),
        )

        if story_data.get("status") == "published":
            story.published_date = datetime.now(timezone.utc)

        db.add(story)
        db.commit()
        db.refresh(story)

        return ResponseFactory.success(
            message="Impact story created successfully",
            data={
                "story": {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "amount_used": float(story.amount_used),
                    "category": story.category,
                    "status": story.status,
                    "image_url": story.image_url,
                    "published_date": story.published_date,
                    "people_impacted": story.people_impacted,
                    "events_held": story.events_held,
                    "items_purchased": story.items_purchased,
                    "created_at": story.created_at,
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to create impact story")


def get_church_impact_stories(
    church_id: int, db: Session, page: int = 1, limit: int = 20
) -> SuccessResponse:
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        offset = (page - 1) * limit

        stories = (
            db.query(ImpactStory)
            .filter(ImpactStory.church_id == church_id, ImpactStory.is_active == True)
            .order_by(ImpactStory.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        total_count = (
            db.query(func.count(ImpactStory.id))
            .filter(ImpactStory.church_id == church_id, ImpactStory.is_active == True)
            .scalar()
        )

        stories_data = []
        for story in stories:
            stories_data.append(
                {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "amount_used": float(story.amount_used),
                    "category": story.category,
                    "status": story.status,
                    "image_url": story.image_url,
                    "published_date": story.published_date,
                    "people_impacted": story.people_impacted,
                    "events_held": story.events_held,
                    "items_purchased": story.items_purchased,
                    "created_at": story.created_at,
                }
            )

        return ResponseFactory.success(
            message="Impact stories retrieved successfully",
            data={
                "stories": stories_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get impact stories")


def get_impact_story(story_id: int, church_id: int, db: Session) -> SuccessResponse:
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        story = (
            db.query(ImpactStory)
            .filter(
                ImpactStory.id == story_id,
                ImpactStory.church_id == church_id,
                ImpactStory.is_active == True,
            )
            .first()
        )

        if not story:
            raise HTTPException(status_code=404, detail="Impact story not found")

        return ResponseFactory.success(
            message="Impact story retrieved successfully",
            data={
                "id": story.id,
                "title": story.title,
                "description": story.description,
                "amount_used": float(story.amount_used),
                "category": story.category,
                "status": story.status,
                "image_url": story.image_url,
                "published_date": story.published_date,
                "people_impacted": story.people_impacted,
                "events_held": story.events_held,
                "items_purchased": story.items_purchased,
                "created_at": story.created_at,
                "updated_at": story.updated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get impact story")


def update_impact_story(
    story_id: int, church_id: int, story_data: dict, db: Session
) -> SuccessResponse:
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        story = (
            db.query(ImpactStory)
            .filter(
                ImpactStory.id == story_id,
                ImpactStory.church_id == church_id,
                ImpactStory.is_active == True,
            )
            .first()
        )

        if not story:
            raise HTTPException(status_code=404, detail="Impact story not found")

        for field, value in story_data.items():
            if hasattr(story, field):
                if field == "amount_used" and value is not None:
                    setattr(story, field, value)
                elif (
                    field == "status"
                    and value == "published"
                    and story.status != "published"
                ):
                    setattr(story, field, value)
                    story.published_date = datetime.now(timezone.utc)
                elif field != "status":
                    setattr(story, field, value)

        story.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(story)

        return ResponseFactory.success(
            message="Impact story updated successfully",
            data={
                "story": {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "amount_used": float(story.amount_used),
                    "category": story.category,
                    "status": story.status,
                    "image_url": story.image_url,
                    "published_date": story.published_date,
                    "people_impacted": story.people_impacted,
                    "events_held": story.events_held,
                    "items_purchased": story.items_purchased,
                    "updated_at": story.updated_at,
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to update impact story")


def delete_impact_story(story_id: int, church_id: int, db: Session) -> SuccessResponse:
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        story = (
            db.query(ImpactStory)
            .filter(
                ImpactStory.id == story_id,
                ImpactStory.church_id == church_id,
                ImpactStory.is_active == True,
            )
            .first()
        )

        if not story:
            raise HTTPException(status_code=404, detail="Impact story not found")

        story.is_active = False
        db.commit()

        return ResponseFactory.success(message="Impact story deleted successfully")

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to delete impact story")


def publish_impact_story(story_id: int, church_id: int, db: Session) -> SuccessResponse:
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        story = (
            db.query(ImpactStory)
            .filter(
                ImpactStory.id == story_id,
                ImpactStory.church_id == church_id,
                ImpactStory.is_active == True,
            )
            .first()
        )

        if not story:
            raise HTTPException(status_code=404, detail="Impact story not found")

        story.status = "published"
        story.published_date = datetime.now(timezone.utc)
        story.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(message="Impact story published successfully")

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to publish impact story")
