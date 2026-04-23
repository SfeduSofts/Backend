from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi import Cookie, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin_schema import Admin as AdminSchema

import httpx
import secrets
import os

load_dotenv()

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.admin_repository = AdminRepository(db)

    def add_admin(self, email: str) -> AdminSchema:
        existing_admin = self.admin_repository.get_by_email(email)
        if existing_admin:
            raise HTTPException(status_code=400, detail="Admin with this email already exists")
        return self.admin_repository.create(AdminSchema(email=email))
    
    def get_admin_by_email(self, email: str) -> AdminSchema:
        admin = self.admin_repository.get_by_email(email=email)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return AdminSchema.model_validate(admin)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        SECRET_KEY = os.getenv("SECRET_KEY")
        ALGORITHM = os.getenv("ALGORITHM")

        to_encode = data.copy()

        expire = datetime.utcnow() + (
            expires_delta if expires_delta else timedelta(minutes=15)
        )

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt


    @staticmethod
    def get_current_user(access_token: str = Cookie(None)):
        SECRET_KEY = os.getenv("SECRET_KEY")
        ALGORITHM = os.getenv("ALGORITHM")

        if not access_token:
            return None

        try:

            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])

            return {
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role")
            }

        except JWTError:
            return None
        
    @staticmethod
    def microsoft_login():
        MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
        REDIRECT_URI = os.getenv("REDIRECT_URI")
        MS_TENANT_ID = os.getenv("MS_TENANT_ID")
        MS_AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"
        MS_AUTHORIZATION_URL = f"{MS_AUTHORITY}/oauth2/v2.0/authorize"
        MS_SCOPES = [
            "openid",
            "profile",
            "email",
            "User.Read"
        ]
        state = secrets.token_urlsafe(32)

        params = {
            "client_id": MS_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(MS_SCOPES),
            "state": state,
            "response_mode": "query",
            "prompt": "select_account"
        }

        auth_url = f"{MS_AUTHORIZATION_URL}?{'&'.join([f'{k}={v}' for k,v in params.items()])}"

        return RedirectResponse(auth_url)
        
    @staticmethod
    async def microsoft_callback(
            code: str,
            request: Request,
            db: Session = Depends(get_db)
    ):
        MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
        MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
        REDIRECT_URI = os.getenv("REDIRECT_URI")
        MS_TENANT_ID = os.getenv("MS_TENANT_ID", "common")
        MS_AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"
        MS_TOKEN_URL = f"{MS_AUTHORITY}/oauth2/v2.0/token"
        SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL")
        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        token_data = {

            "client_id": MS_CLIENT_ID,
            "client_secret": MS_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }


        async with httpx.AsyncClient() as client:

            token_response = await client.post(
                MS_TOKEN_URL,
                data=token_data
            )

            if token_response.status_code != 200:

                raise HTTPException(
                    status_code=400,
                    detail="Token exchange failed"
                )

            token_json = token_response.json()

            access_token_ms = token_json.get("access_token")

            # Получаем пользователя из Microsoft Graph

            user_info_response = await client.get(

                "https://graph.microsoft.com/v1.0/me",

                headers={
                    "Authorization": f"Bearer {access_token_ms}"
                }
            )

            if user_info_response.status_code != 200:

                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user info"
                )

            user_info = user_info_response.json()

            email = (
                user_info.get("userPrincipalName")
                or user_info.get("mail")
            )

            name = user_info.get("displayName")

            if not email:

                raise HTTPException(
                    status_code=400,
                    detail="Email not found"
                )

            email = email.lower()

            # =====================
            # Определяем роль
            # =====================

            role = None

            if email == SUPERADMIN_EMAIL:

                role = "superadmin"
            
            else:

                admin = db.query(Admin).filter(
                    Admin.email == email
                ).first()

                if admin:
                    role = "admin"

            # =====================
            # Если не admin и не superadmin
            # =====================

            if role is None:

                return RedirectResponse("/")

            # =====================
            # создаем JWT
            # =====================

            jwt_token = AuthService.create_access_token(

                data={
                    "email": email,
                    "name": name,
                    "role": role
                },

                expires_delta=timedelta(
                    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
                )
            )

            response = RedirectResponse("/")

            response.set_cookie(

                key="access_token",

                value=jwt_token,

                httponly=True,

                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,

                samesite="lax"
            )

            return response
