from pydantic import BaseModel, EmailStr


class Admin(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True