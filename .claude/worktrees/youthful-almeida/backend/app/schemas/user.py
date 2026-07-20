"""
User Pydantic Schemas

Schemas for user creation, updates, authentication, and responses.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime


class UserCreate(BaseModel):
    """Request model for creating a new user"""
    
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")
    confirm_password: str = Field(..., description="Password confirmation")
    
    # Optional fields
    company: Optional[str] = Field(None, max_length=255, description="User's company")
    title: Optional[str] = Field(None, max_length=255, description="User's job title")
    license_number: Optional[str] = Field(None, max_length=100, description="Professional license number")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "securepassword123",
                "confirm_password": "securepassword123",
                "company": "Financial Planning Inc.",
                "title": "Financial Advisor",
                "license_number": "FA12345"
            }
        }


class UserUpdate(BaseModel):
    """Request model for updating user information"""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's last name")
    company: Optional[str] = Field(None, max_length=255, description="User's company")
    title: Optional[str] = Field(None, max_length=255, description="User's job title")
    license_number: Optional[str] = Field(None, max_length=100, description="Professional license number")
    timezone: Optional[str] = Field(None, description="User's timezone")
    locale: Optional[str] = Field(None, description="User's locale preference")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "company": "New Financial Planning Inc.",
                "title": "Senior Financial Advisor",
                "timezone": "America/New_York",
                "locale": "en_US"
            }
        }


class UserLogin(BaseModel):
    """Request model for user authentication"""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    remember_me: bool = Field(False, description="Whether to remember the user session")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123",
                "remember_me": True
            }
        }


class UserResponse(BaseModel):
    """Response model for user data"""
    
    id: str = Field(..., description="Unique identifier for the user")
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    full_name: str = Field(..., description="User's full name")
    
    # Professional information
    company: Optional[str] = Field(None, description="User's company")
    title: Optional[str] = Field(None, description="User's job title")
    license_number: Optional[str] = Field(None, description="Professional license number")
    
    # Account status
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user email is verified")
    is_superuser: bool = Field(False, description="Whether the user has superuser privileges")
    
    # Preferences
    timezone: str = Field("UTC", description="User's timezone")
    locale: str = Field("en_US", description="User's locale preference")
    
    # Timestamps
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user_12345",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "company": "Financial Planning Inc.",
                "title": "Financial Advisor",
                "license_number": "FA12345",
                "is_active": True,
                "is_verified": True,
                "is_superuser": False,
                "timezone": "America/New_York",
                "locale": "en_US",
                "created_at": "2024-01-27T10:00:00Z",
                "updated_at": "2024-01-27T10:00:00Z",
                "last_login": "2024-01-27T09:30:00Z"
            }
        }


class UserProfile(BaseModel):
    """Extended user profile with additional information"""
    
    user: UserResponse = Field(..., description="Basic user information")
    
    # Statistics
    total_plans_created: int = Field(0, description="Total number of financial plans created")
    total_simulations_run: int = Field(0, description="Total number of simulations run")
    last_plan_date: Optional[datetime] = Field(None, description="Date of last plan creation")
    
    # Preferences
    preferences: dict = Field(default_factory=dict, description="User preferences and settings")
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": "user_12345",
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "full_name": "John Doe",
                    "is_active": True,
                    "is_verified": True
                },
                "total_plans_created": 5,
                "total_simulations_run": 12,
                "last_plan_date": "2024-01-27T10:00:00Z",
                "preferences": {
                    "default_risk_tolerance": "moderate",
                    "default_simulation_count": 50000,
                    "email_notifications": True
                }
            }
        }
