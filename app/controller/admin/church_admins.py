from fastapi import HTTPException
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.model.m_church_admin import ChurchAdmin
from app.core.responses import ResponseFactory


def assign_role(id: int, role: str, db):
    """Assign role to church admin"""
    try:
        if role not in ["admin", "treasurer", "staff", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        admin_user = db.query(ChurchAdmin).filter_by(id=id).first()
        if not admin_user:
            raise HTTPException(status_code=404, detail="Church admin not found")
        
        admin_user.role = role
        db.commit()
        
        return ResponseFactory.success(
            message=f"Role updated to {role}",
            data={
                "admin_id": id,
                "role": role,
                "updated": True
            }
        )

    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        
        raise HTTPException(status_code=500, detail="ADMIN.CHURCH_ADMIN.DB_ERROR")

    except Exception as e:
        
        raise HTTPException(status_code=500, detail="ADMIN.CHURCH_ADMIN.ERROR") 
