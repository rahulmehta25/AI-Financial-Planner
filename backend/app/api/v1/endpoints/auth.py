"""
Authentication endpoints for user login, registration, and token management
"""

import logging
from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user, 
    get_db, 
    get_client_ip, 
    get_user_agent,
    get_current_active_user,
    terminate_user_session,
    terminate_all_user_sessions
)
from app.core import security
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.models.user import User
from app.schemas.auth import (
    Token, AuthResponse, UserRegister, UserLogin, 
    RefreshTokenRequest, LogoutRequest, SessionList
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user account and return authentication tokens
    """
    auth_service = AuthService(db)
    
    # Get client information
    ip_address = await get_client_ip(request)
    user_agent = await get_user_agent(request)
    
    try:
        # Register user
        user = await auth_service.register_user(
            user_data=user_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create session
        session = await auth_service.create_session(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=False
        )
        
        # Create tokens
        tokens = await auth_service.create_tokens(user, session)
        
        # Prepare response
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at
        }
        
        session_dict = {
            "session_id": session.session_id,
            "user_id": str(session.user_id),
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "expires_at": session.expires_at,
            "is_active": session.is_active
        }
        
        return {
            "user": user_dict,
            "tokens": tokens,
            "session": session_dict
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    auth_service = AuthService(db)
    
    # Get client information
    ip_address = await get_client_ip(request)
    user_agent = await get_user_agent(request)
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=form_data.username,
            password=form_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create session
        session = await auth_service.create_session(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=False
        )
        
        # Create tokens
        tokens = await auth_service.create_tokens(user, session)
        
        # Prepare response
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "last_login": user.last_login
        }
        
        session_dict = {
            "session_id": session.session_id,
            "user_id": str(session.user_id),
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "expires_at": session.expires_at,
            "is_active": session.is_active
        }
        
        return {
            "user": user_dict,
            "tokens": tokens,
            "session": session_dict
        }
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/login/email", response_model=AuthResponse)
async def login_email(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Email/password login endpoint with comprehensive session management
    """
    auth_service = AuthService(db)
    
    # Get client information
    ip_address = await get_client_ip(request)
    user_agent = await get_user_agent(request)
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=user_data.email,
            password=user_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create session
        session = await auth_service.create_session(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=user_data.remember_me
        )
        
        # Create tokens
        tokens = await auth_service.create_tokens(user, session)
        
        # Prepare response
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "last_login": user.last_login
        }
        
        session_dict = {
            "session_id": session.session_id,
            "user_id": str(session.user_id),
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "expires_at": session.expires_at,
            "is_active": session.is_active
        }
        
        return {
            "user": user_dict,
            "tokens": tokens,
            "session": session_dict
        }
        
    except Exception as e:
        logger.error(f"Email login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    auth_service = AuthService(db)
    
    # Get client information
    ip_address = await get_client_ip(request)
    user_agent = await get_user_agent(request)
    
    try:
        # Refresh tokens
        tokens = await auth_service.refresh_token(
            refresh_token=refresh_data.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest = LogoutRequest(),
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Logout current user and invalidate tokens/sessions
    """
    auth_service = AuthService(db)
    
    # Get client information
    ip_address = await get_client_ip(request)
    user_agent = await get_user_agent(request)
    
    # Extract tokens from request headers
    authorization = request.headers.get("authorization")
    access_token = None
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.split(" ")[1]
    
    try:
        # Logout user
        success = await auth_service.logout_user(
            user=current_user,
            access_token=access_token,
            all_sessions=logout_data.all_sessions,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return {"message": "Successfully logged out"}
        else:
            return {"message": "Logout completed with warnings"}
            
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        # Still return success to prevent client issues
        return {"message": "Logout completed"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "is_active": current_user.is_active,
        "is_verified": current_user.email_verified,
        "is_superuser": current_user.is_superuser,
        "timezone": "UTC",
        "locale": "en_US",
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login": current_user.last_login
    }


@router.get("/sessions", response_model=SessionList)
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all active sessions for the current user
    """
    auth_service = AuthService(db)
    
    try:
        sessions = await auth_service.get_user_sessions(str(current_user.id))
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.session_id,
                "user_id": str(session.user_id),
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "expires_at": session.expires_at,
                "is_active": session.is_active
            })
        
        return {
            "sessions": session_list,
            "total": len(session_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Terminate a specific user session
    """
    try:
        success = await terminate_user_session(
            session_id=session_id,
            user_id=str(current_user.id),
            reason="user_terminated",
            db=db
        )
        
        if success:
            return {"message": "Session terminated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already terminated"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate session"
        )


@router.delete("/sessions")
async def terminate_all_sessions(
    current_user: User = Depends(get_current_active_user),
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Terminate all sessions for the current user except current one
    """
    try:
        # Extract current session ID from token if possible
        authorization = request.headers.get("authorization")
        current_session_id = None
        
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            from app.core.security_enhanced import JWTManager
            payload = JWTManager.decode_token(token, verify_exp=False)
            if payload:
                current_session_id = payload.get("session_id")
        
        # Terminate all other sessions
        terminated_count = await terminate_all_user_sessions(
            user_id=str(current_user.id),
            exclude_session_id=current_session_id,
            reason="user_terminated_all",
            db=db
        )
        
        return {
            "message": f"Successfully terminated {terminated_count} sessions",
            "terminated_count": terminated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to terminate all sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate sessions"
        )


@router.post("/verify-token")
async def verify_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify if the provided token is valid
    """
    try:
        # Extract token from Authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return {"valid": False, "reason": "No token provided"}
        
        token = authorization.split(" ")[1]
        
        # Try to get user from token
        from app.api.deps import get_current_user_from_token
        user = await get_current_user_from_token(token, db)
        
        if user:
            return {
                "valid": True,
                "user_id": str(user.id),
                "email": user.email,
                "is_active": user.is_active
            }
        else:
            return {"valid": False, "reason": "Invalid or expired token"}
            
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return {"valid": False, "reason": "Token verification failed"}