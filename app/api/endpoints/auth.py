# backend/app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated, Any
from ...db.database import get_db
from ...core.auth import verify_password, create_access_token, get_password_hash, get_current_user
from ...schemas.auth import User, UserCreate, Token, UserMe
from ...models.user import User as UserModel
from ...schemas.token import Token as TokenSchema
from ...models.token import Token as TokenModel
import secrets

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/signup", response_model=User)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(
            email=user.email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify-token", response_model=dict)
async def verify_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Verify token validity and return user info
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "is_active": current_user.is_active
        }
    }

@router.get("/me", response_model=UserMe)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information
    """
    try:
        return {
            "valid": True,
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.profile.full_name if current_user.profile else None,
            "phone": current_user.profile.phone if current_user.profile else None,
            "is_active": current_user.is_active
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user data: {str(e)}"
        )
        
@router.post("/generate-permanent-token", response_model=TokenSchema)
async def generate_permanent_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Generate a permanent API token for external applications"""
    try:
        # Generate a secure random token
        token_str = secrets.token_hex(32)
        
        # Create token record
        token = TokenModel(
            user_id=current_user.id,
            token=token_str
        )
        
        db.add(token)
        db.commit()
        db.refresh(token)
        
        return token
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating token: {str(e)}"
        )

@router.get("/list-tokens", response_model=list[TokenSchema])
async def list_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all permanent tokens for the current user"""
    tokens = db.query(TokenModel).filter(
        TokenModel.user_id == current_user.id
    ).all()
    return tokens

@router.delete("/revoke-token/{token_id}")
async def revoke_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Revoke a specific permanent token"""
    token = db.query(TokenModel).filter(
        TokenModel.id == token_id,
        TokenModel.user_id == current_user.id
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    try:
        db.delete(token)
        db.commit()
        return {"message": "Token revoked successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking token: {str(e)}"
        )