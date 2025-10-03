from fastapi import APIRouter, Depends, Body, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.controller.church.google_oauth import google_oauth_login, link_google_account, initiate_google_oauth
from app.utils.database import get_db
from app.services.oauth_service import google_oauth_service

router = APIRouter(tags=["Google OAuth"])

class GoogleOAuthLoginRequest(BaseModel):
    """Request model for Google OAuth login"""
    id_token: str = Body(..., description="Google ID token from client")

class LinkGoogleAccountRequest(BaseModel):
    """Request model for linking Google account"""
    id_token: str = Body(..., description="Google ID token from client")

@router.get("/initiate")
async def initiate_oauth_flow(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initiate Google OAuth flow
    
    This endpoint redirects the user to Google OAuth for authentication.
    """
    return initiate_google_oauth(request, db)

@router.post("/login")
async def login_with_google(
    request_data: GoogleOAuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate church admin using Google OAuth
    
    This endpoint allows church admins to log in using their Google account.
    The client must provide a valid Google ID token.
    """
    return google_oauth_login(
        id_token=request_data.id_token,
        request=request,
        db=db
    )

@router.get("/redirect")
async def google_oauth_redirect(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(None, description="State parameter for security"),
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth redirect callback
    
    This endpoint receives the authorization code from Google and processes the OAuth flow.
    It returns an HTML page that communicates with the parent window.
    """
    try:
        # Exchange authorization code for user info
        google_user_info = google_oauth_service.exchange_authorization_code(code)
        
        # Return HTML page that communicates with parent window
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google OAuth Success</title>
        </head>
        <body>
            <script>
                // Send success message to parent window
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'OAUTH_SUCCESS',
                        code: '{code}',
                        userInfo: {google_user_info}
                    }}, '*');
                    window.close();
                }} else {{
                    // If no opener, redirect to login page
                    window.location.href = '/church-admin/login';
                }}
            </script>
            <p>Authentication successful! You can close this window.</p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        # Return error page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google OAuth Error</title>
        </head>
        <body>
            <script>
                // Send error message to parent window
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'OAUTH_ERROR',
                        message: 'Authentication failed: {str(e)}'
                    }}, '*');
                    window.close();
                }} else {{
                    // If no opener, redirect to login page
                    window.location.href = '/church-admin/login?error=oauth_failed';
                }}
            </script>
            <p>Authentication failed. You can close this window and try again.</p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content, status_code=400)

@router.post("/link/{user_id}")
async def link_google_account_to_user(
    user_id: int,
    request_data: LinkGoogleAccountRequest,
    db: Session = Depends(get_db)
):
    """
    Link existing church admin account to Google OAuth
    
    This endpoint allows linking an existing church admin account to a Google account.
    The user_id must be a valid church admin user ID.
    """
    return link_google_account(
        user_id=user_id,
        id_token=request_data.id_token,
        db=db
    )
