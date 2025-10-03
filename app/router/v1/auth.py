"""
OAuth Authentication Routes

Provides OAuth login endpoints for Google and Apple authentication.
These are separate from mobile-specific auth routes to provide clean API organization.
"""

from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.controller.auth.google_oauth import google_oauth_login as google_oauth_controller
from app.controller.auth.apple_oauth import apple_oauth_login as apple_oauth_controller
from app.schema.auth_schema import GoogleOAuthRequest, AppleOAuthRequest
from app.utils.database import get_db
from app.core.responses import SuccessResponse
from app.config import config
import urllib.parse
import json

# Create OAuth router
oauth_router = APIRouter(tags=["OAuth Authentication"])

@oauth_router.get("/google/redirect")
async def google_oauth_callback(
    code: str,
    state: str | None = None
):
    """
    Handle Google OAuth callback with authorization code
    
    This endpoint processes the authorization code from Google and routes to the appropriate
    OAuth handler based on the flow type (church admin vs donor).
    """
    try:
        if not code:
            # Return HTML page that sends error message to parent
            error_html = """
            <!DOCTYPE html>
            <html>
            <head><title>OAuth Error</title></head>
            <body>
            <script>
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'OAUTH_ERROR',
                        message: 'Authorization code is required'
                    }, '*');
                    window.close();
                }
            </script>
            <p>Authorization code is required. Closing window...</p>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html)
        
        # Parse state to determine OAuth flow type
        flow_type = "church_admin"  # Default to church admin flow
        
        if state:
            try:
                import urllib.parse
                state_params = urllib.parse.parse_qs(urllib.parse.unquote(state))
                
                # Check if this is a donor flow (has oauth_type)
                if 'oauth_type' in state_params and state_params['oauth_type'][0] == 'donor':
                    flow_type = "donor"
                # Check if this is a church admin flow (has oauth_type)
                elif 'oauth_type' in state_params:
                    flow_type = state_params['oauth_type'][0]
            except:
                pass
        
        # Route to appropriate OAuth handler
        if flow_type == "donor":
            # Handle donor OAuth callback
            try:
                from app.controller.donor.google_oauth import google_oauth_callback as donor_callback
                from app.utils.database import get_db
                
                # Get database session using proper context manager
                db_generator = get_db()
                db = next(db_generator)
                
                try:
                    # Call the donor callback
                    result = await donor_callback(
                        code=code,
                        state=state or "",
                        request=None,
                        db=db
                    )
                finally:
                    # Ensure database session is properly closed
                    try:
                        next(db_generator)
                    except StopIteration:
                        pass
                
                # Extract user data from result
                if hasattr(result, 'data') and result.data:
                    user_data = result.data.get('user', {})
                    tokens = result.data.get('tokens', {})
                    is_new_user = result.data.get('is_new_user', False)
                    
                    # Merge tokens into user_data for frontend compatibility
                    complete_user_data = {
                        **user_data,
                        'access_token': tokens.get('access_token'),
                        'refresh_token': tokens.get('refresh_token'),
                        'user_id': user_data.get('id'),  # Map id to user_id for frontend
                        'church_id': user_data.get('church_id'),  # Include church_id for frontend
                        'is_new_user': is_new_user
                    }
                    
                    # Return HTML that sends success message to parent window
                    success_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head><title>OAuth Success</title></head>
                    <body>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'OAUTH_SUCCESS',
                                userData: {json.dumps(complete_user_data)}
                            }}, '*');
                            window.close();
                        }}
                    </script>
                    <p>Authentication successful! Closing window...</p>
                    </body>
                    </html>
                    """
                    return HTMLResponse(content=success_html)
                else:
                    raise Exception("Invalid response from OAuth callback")
                    
            except Exception as e:
                import logging
                logging.error(f"Donor OAuth callback error: {str(e)}")
                # Return error HTML
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head><title>OAuth Error</title></head>
                <body>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'OAUTH_ERROR',
                            message: 'Authentication failed: {str(e)}'
                        }}, '*');
                        window.close();
                    }}
                </script>
                <p>Authentication failed. Closing window...</p>
                </body>
                </html>
                """
                return HTMLResponse(content=error_html)
        else:
            # Default: church admin flow - send code back to parent window
            success_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>OAuth Success</title></head>
            <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'OAUTH_SUCCESS',
                        code: '{code}',
                        state: '{state or ""}'
                    }}, '*');
                    window.close();
                }}
            </script>
            <p>Authentication successful! Closing window...</p>
            </body>
            </html>
            """
            return HTMLResponse(content=success_html)
        
    except Exception as e:
        # Return HTML page that sends error message to parent
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'OAUTH_ERROR',
                    message: '{str(e)}'
                }}, '*');
                window.close();
            }}
        </script>
        <p>Authentication failed. Closing window...</p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)

@oauth_router.post("/google/login", response_model=SuccessResponse)
async def google_oauth_login_route(
    data: GoogleOAuthRequest,
    db: Session = Depends(get_db)
):
    """Google OAuth login endpoint"""
    return google_oauth_controller(data, db)

@oauth_router.post("/google/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def google_oauth_register_route(
    data: GoogleOAuthRequest,
    db: Session = Depends(get_db)
):
    """Google OAuth registration endpoint"""
    return google_oauth_controller(data, db)

@oauth_router.post("/apple/login", response_model=SuccessResponse)
async def apple_oauth_login_route(
    data: AppleOAuthRequest,
    db: Session = Depends(get_db)
):
    """Apple OAuth login endpoint"""
    return apple_oauth_controller(data, db)

@oauth_router.post("/apple/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def apple_oauth_register_route(
    data: AppleOAuthRequest,
    db: Session = Depends(get_db)
):
    """Apple OAuth registration endpoint"""
    return apple_oauth_controller(data, db)
