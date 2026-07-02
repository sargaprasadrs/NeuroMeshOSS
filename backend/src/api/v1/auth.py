from datetime import timedelta
from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.entities.user import User
from src.core.ports.repositories import IUserRepository
from src.adapters.database.session import get_db_session
from src.adapters.database.repositories import SqlAlchemyUserRepository
from src.services.auth_service import AuthService
from src.config.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> IUserRepository:
    """Dependency injector supplying the SQL repository adapter."""
    return SqlAlchemyUserRepository(session)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterUserRequest,
    user_repo: IUserRepository = Depends(get_user_repository),
) -> TokenResponse:
    # Check if email is already taken
    existing = await user_repo.get_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already registered.",
        )

    # Store User domain entity
    hashed_pwd = AuthService.get_password_hash(req.password)
    user = User(
        id=uuid4(),
        email=req.email,
        password_hash=hashed_pwd,
        is_active=True,
        role="user",
    )
    await user_repo.save(user)

    # Automatically issue token
    access_token = AuthService.create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=access_token)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: IUserRepository = Depends(get_user_repository),
) -> TokenResponse:
    user = await user_repo.get_by_email(form_data.username)
    if not user or not AuthService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )
    return TokenResponse(access_token=access_token)
