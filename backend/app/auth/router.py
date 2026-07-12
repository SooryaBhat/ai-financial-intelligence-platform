"""
Authentication router — /api/v1/auth
Public endpoints (no auth required): signup, login, refresh
Protected endpoints (auth required): logout, me, onboard
"""
from fastapi import APIRouter, Depends, Request, status

from app.auth.service import auth_service
from app.dependencies.auth import get_current_user_raw
from app.schemas.auth import (
    LoginRequest,
    OnboardRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a Supabase Auth user and a matching user profile. Returns JWT tokens.",
)
def signup(data: SignupRequest):
    result = auth_service.signup(data)
    return SuccessResponse(data=result)


@router.post(
    "/login",
    response_model=SuccessResponse,
    summary="Login with email and password",
    description="Authenticates the user via Supabase Auth and returns JWT access + refresh tokens.",
)
def login(data: LoginRequest):
    result = auth_service.login(data)
    return SuccessResponse(data=result)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and invalidate session",
)
def logout(request: Request, token_data: dict = Depends(get_current_user_raw)):
    jwt = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    auth_service.logout(jwt)
    return MessageResponse(message="Logged out successfully.")


@router.post(
    "/refresh",
    response_model=SuccessResponse,
    summary="Refresh JWT tokens",
)
def refresh(data: RefreshRequest):
    result = auth_service.refresh(data.refresh_token)
    return SuccessResponse(data=result)


@router.post(
    "/onboard",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create first company after signup",
    description="Called after signup to create the user's first company and assign them the Owner role.",
)
def onboard(data: OnboardRequest, token_data: dict = Depends(get_current_user_raw)):
    company = auth_service.onboard(data, token_data["id"])
    return SuccessResponse(data=company)


@router.get(
    "/me",
    response_model=SuccessResponse,
    summary="Get current authenticated user",
)
def me(token_data: dict = Depends(get_current_user_raw)):
    return SuccessResponse(data=token_data)
