"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse, UserWithTokenResponse
from app.services.auth_service import AuthService

# Rate limiter: 5 requests per minute per IP
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserWithTokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user and return tokens."""
    auth_service = AuthService(db)
    try:
        user = await auth_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    tokens = auth_service.create_tokens(user)
    return UserWithTokenResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        subscription_tier=user.subscription_tier,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        **tokens,
    )


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_service.create_tokens(user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user_tuple: tuple = Depends(get_current_active_user)):
    """Get current user info with proper JWT authentication."""
    user, payload = current_user_tuple
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        subscription_tier=user.subscription_tier,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        New access token and refresh token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    from app.utils.jwt import verify_refresh_token, create_access_token, create_refresh_token
    
    user, _ = current_user
    
    try:
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        token_user_id = payload.get("sub")
        
        if token_user_id != str(user.id):
            raise HTTPException(
                status_code=401,
                detail="Refresh token does not belong to current user",
            )
        
        # Create new tokens
        auth_service = AuthService(db)
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid refresh token: {str(e)}",
        )


@router.post("/logout")
async def logout(
    current_user: tuple = Depends(get_current_active_user),
):
    """Logout user and invalidate tokens.
    
    Note: This is a simple implementation. For production, consider:
    - Adding tokens to a Redis blacklist
    - Implementing token versioning
    - Storing revoked tokens in database
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    user, _ = current_user
    
    # TODO: Implement token blacklist/revocation
    # For now, we instruct the client to discard tokens
    # In production, add the token to a Redis set with expiration
    
    return {
        "message": "Successfully logged out",
        "detail": "Please discard your tokens on the client side",
    }
