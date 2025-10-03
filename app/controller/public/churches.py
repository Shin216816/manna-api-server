from sqlalchemy.orm import Session
from app.core.responses import ResponseFactory
from app.core.exceptions import MannaException, ValidationError
from app.utils.database import engine
from sqlalchemy import text


def get_public_churches(db: Session, limit: int = 50, search: str = None):
    """Get public list of active churches for donor selection"""
    try:
        # Use raw SQL to avoid relationship issues
        from app.utils.database import engine
        
        search_clause = ""
        params = {"limit": limit}
        
        if search:
            search_clause = "AND (name ILIKE :search OR city ILIKE :search OR state ILIKE :search)"
            params["search"] = f"%{search}%"
        
        with engine.connect() as conn:
            result = conn.execute(
                text(f"""
                SELECT id, name, city, state, website, phone
                FROM churches 
                WHERE is_active = true {search_clause}
                ORDER BY name ASC
                LIMIT :limit
                """),
                params
            ).fetchall()
            
            churches = []
            for row in result:
                churches.append({
                    "id": row[0],
                    "name": row[1],
                    "city": row[2],
                    "state": row[3],
                    "website": row[4],
                    "phone": row[5],
                    "verified": True  # All active churches are considered verified for public listing
                })
        
        return ResponseFactory.success(
            message="Churches retrieved successfully",
            data={
                "churches": churches,
                "total": len(churches)
            }
        )
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to get churches: {str(e)}")


def get_public_church_by_id(db: Session, church_id: int):
    """Get a specific church by ID for public access"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT id, name, city, state, website, phone
                FROM churches 
                WHERE id = :church_id AND is_active = true
                """),
                {"church_id": church_id}
            ).fetchone()
            
            if not result:
                raise ValidationError("Church not found")
            
            church = {
                "id": result[0],
                "name": result[1],
                "city": result[2],
                "state": result[3],
                "website": result[4],
                "phone": result[5],
                "verified": True
            }
        
        return ResponseFactory.success(
            message="Church retrieved successfully",
            data={"church": church}
        )
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to get church: {str(e)}")
