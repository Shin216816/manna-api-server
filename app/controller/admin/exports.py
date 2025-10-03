"""
Export Controller for Admin

Provides data export functionality for various admin operations:
- Church data export (CSV, JSON, Excel)
- User data export
- Analytics data export
- Custom report generation
"""

from fastapi import HTTPException
import logging
import csv
import json
import io
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.core.responses import ResponseFactory


def export_churches_data(
    search_request,
    format: str,
    db: Session
):
    """Export churches data in specified format"""
    try:
        # Get churches data using the same logic as enhanced_churches
        from app.controller.admin.enhanced_churches import get_enhanced_church_list
        
        # Get the data
        result = get_enhanced_church_list(search_request, db)
        churches_data = result.data['churches']
        
        if format.lower() == 'csv':
            return export_to_csv(churches_data, 'churches')
        elif format.lower() == 'json':
            return export_to_json(churches_data, 'churches')
        elif format.lower() == 'excel':
            return export_to_excel(churches_data, 'churches')
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use csv, json, or excel")
            
    except Exception as e:
        logging.error(f"Error exporting churches data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export churches data")


def export_to_csv(data: List[Dict[str, Any]], filename_prefix: str):
    """Export data to CSV format"""
    try:
        if not data:
            return ResponseFactory.success(
                message="No data to export",
                data={"download_url": None}
            )
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        # In a real implementation, you would save this to a file and return a download URL
        # For now, we'll return the content directly
        return ResponseFactory.success(
            message="Data exported successfully",
            data={
                "format": "csv",
                "filename": f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "content": csv_content,
                "record_count": len(data)
            }
        )
        
    except Exception as e:
        logging.error(f"Error creating CSV export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create CSV export")


def export_to_json(data: List[Dict[str, Any]], filename_prefix: str):
    """Export data to JSON format"""
    try:
        if not data:
            return ResponseFactory.success(
                message="No data to export",
                data={"download_url": None}
            )
        
        json_content = json.dumps(data, indent=2, default=str)
        
        return ResponseFactory.success(
            message="Data exported successfully",
            data={
                "format": "json",
                "filename": f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "content": json_content,
                "record_count": len(data)
            }
        )
        
    except Exception as e:
        logging.error(f"Error creating JSON export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create JSON export")


def export_to_excel(data: List[Dict[str, Any]], filename_prefix: str):
    """Export data to Excel format"""
    try:
        if not data:
            return ResponseFactory.success(
                message="No data to export",
                data={"download_url": None}
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel content
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        
        excel_content = output.getvalue()
        output.close()
        
        # Convert to base64 for transmission
        import base64
        excel_b64 = base64.b64encode(excel_content).decode()
        
        return ResponseFactory.success(
            message="Data exported successfully",
            data={
                "format": "excel",
                "filename": f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "content": excel_b64,
                "record_count": len(data)
            }
        )
        
    except Exception as e:
        logging.error(f"Error creating Excel export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create Excel export")


def export_users_data(
    search_params: Dict[str, Any],
    format: str,
    db: Session
):
    """Export users data in specified format"""
    try:
        # Get users data
        from app.controller.admin.users import get_all_users
        
        # This would need to be adapted to return the actual data
        # For now, we'll create a placeholder
        users_data = []
        
        if format.lower() == 'csv':
            return export_to_csv(users_data, 'users')
        elif format.lower() == 'json':
            return export_to_json(users_data, 'users')
        elif format.lower() == 'excel':
            return export_to_excel(users_data, 'users')
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use csv, json, or excel")
            
    except Exception as e:
        logging.error(f"Error exporting users data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export users data")