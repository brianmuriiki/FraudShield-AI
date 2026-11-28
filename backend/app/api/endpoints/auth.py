from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import Role
from app.core.dependencies import get_client_ip, get_current_user, get_current_user_optional, oauth2_scheme
from app.core.security import DUMMY_HASH, create_access_token, decode_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import MessageResponse
from app.schemas.user import UserOut
from app.services.audit_service import log_action
from app.services.auth_controls import login_is_limited, record_login_failure, revoke_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _authenticate(db: Session, email: str, password: str, ip) -> TokenResponse:
    email = email.strip().lower()
    if login_is_limited(db, email, ip):
        db.commit()
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts. Try again later.",
                            headers={"Retry-After": str(settings.LOGIN_RATE_WINDOW_MINUTES * 60)})
    user = db.scalar(select(User).where(User.email == email))
    valid = verify_password(password, user.hashed_password if user else DUMMY_HASH)
    if user is None or not valid or not user.is_active:
        log_action(db, action="login_failed", entity_type="user", entity_id=None,
                   description=f"Failed login attempt for '{email[:100]}'", ip_address=ip)
        record_login_failure(db, email, ip)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    user.last_login_at = datetime.now(timezone.utc)
    log_action(db, action="login", entity_type="user", entity_id=str(user.id),
               description="User logged in", user_id=user.id, ip_address=ip)
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """JSON login: {"email": "...", "password": "..."}."""
    return _authenticate(db, payload.email, payload.password, get_client_ip(request))


@router.post("/token", response_model=TokenResponse, include_in_schema=True)
def login_form(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 form login (used by the Swagger 'Authorize' button)."""
    return _authenticate(db, form.username, form.password, get_client_ip(request))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: User | None = Depends(get_current_user_optional),
):
    """Administrators create users with any role. Public self-registration (if enabled in
    settings) always yields the least-privileged BI Analyst role."""
    if actor is None:
        if not settings.ALLOW_PUBLIC_REGISTRATION:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required",
                                headers={"WWW-Authenticate": "Bearer"})
        role = Role.BI_ANALYST
    else:
        if actor.role != Role.ADMINISTRATOR.value:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only administrators can create users")
        role = payload.role or Role.BI_ANALYST

    if db.scalar(select(User.id).where(User.email == payload.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists")
    user = User(email=payload.email, full_name=payload.full_name,
                hashed_password=hash_password(payload.password), role=role.value)
    db.add(user)
    db.flush()
    log_action(db, action="user_created", entity_type="user", entity_id=str(user.id),
               description=f"User {user.email} created with role {role.value}",
               user_id=actor.id if actor else None, ip_address=get_client_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, token: str = Depends(oauth2_scheme), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke this bearer token until its original expiration."""
    claims = decode_access_token(token)
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    revoke_token(db, jti=claims["jti"], user_id=user.id, expires_at=expires_at)
    log_action(db, action="logout", entity_type="user", entity_id=str(user.id),
               description="User logged out", user_id=user.id, ip_address=get_client_ip(request))
    db.commit()
    return MessageResponse(message="Logged out. This access token has been revoked.")
