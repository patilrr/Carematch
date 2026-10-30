from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    preferred_language: str = Field(default="en", pattern="^(en|hi|mr)$")


class PatientLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PatientOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: str | None
    preferred_language: str
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    patient: PatientOut
