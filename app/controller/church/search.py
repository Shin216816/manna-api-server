from sqlalchemy.orm import Session
from app.model.m_church import Church
from fastapi import HTTPException
from app.core.responses import ResponseFactory

def search_churches(query: str, db: Session):
    """Search for churches by name, address, or city (case-insensitive, partial match). If query is empty or 'all', return all active churches (max 20)."""
    try:
        q = (query or "").strip()
        base_query = db.query(Church).filter(Church.is_active == True)
        if not q or q.lower() == "all":
            results = base_query.limit(20).all()
        else:
            like_q = f"%{q}%"
            results = base_query.filter(
                (Church.name.ilike(like_q)) |
                (Church.address.ilike(like_q))
            ).limit(20).all()
        
        churches = [
            {
                "id": c.id,
                "name": c.name,
                "address": c.address,
                "phone": c.phone,
                "website": c.website,
                "kyc_status": c.kyc_status,
                "is_active": c.is_active
            }
            for c in results
        ]
        
        return ResponseFactory.success(
            message="Churches retrieved successfully",
            data={"churches": churches}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") 
