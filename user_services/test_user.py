from .routes import app
from fastapi.testclient import TestClient
from .models import get_db, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import pytest 

# Create engine and session
engine = create_engine("postgresql://postgres:password@localhost/test")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

def over_write_get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

@pytest.fixture
def db_setup():
    Base.metadata.create_all(bind = engine)
    yield 
    Base.metadata.drop_all(bind = engine)

app.dependency_overrides[get_db] = over_write_get_db

# Test successful user registration
def test_user_registration_successful(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91@example.com",
    "first_name": "string",
    "last_name": "string",
    "is_superuser": True
    }
    response = client.post("/register", json = data)
    assert response.status_code == 201  
    
# Test invalid email 
def test_user_invalid_email(db_setup):
    data = {
    "email": "user91example",
    "password": "user91@example.com",
    "first_name": "string",
    "last_name": "string",
    "is_superuser": ""
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test invalid password
def test_user_invalid_password(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91example",
    "first_name": "string",
    "last_name": "string",
    "is_superuser": ""
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test invalid first name
def test_user_invalid_first_name(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91@example.co",
    "first_name": 123,
    "last_name": "string",
    "is_superuser": ""
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test invalid last name
def test_user_invalid_last_name(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91@example.com",
    "first_name": "string",
    "last_name": 123,
    "is_superuser": ""
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# Test missing fields
def test_missing_fields(db_setup):
    data = {
    "email": "user91@example.com",
    "password": "user91example",
    "last_name": "string",
    "is_superuser": ""
    }
    response = client.post("/register", json = data)
    assert response.status_code == 422
    
# To test successful user login
def test_user_login_successful(db_setup):
    # First, create a user to login
    data = {
        "email": "user91@example.com",
        "password": "user91@example.com",
        "first_name": "string",
        "last_name": "string",
        "is_superuser": True
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    # Now, test login with the same credentials
    login_data = {
        "email": "user91@example.com",
        "password": "user91@example.com"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 201
    assert response.json()["message"] == "Login successful"

# To test user login failure (invalid password)
def test_user_login_failure_invalid_password(db_setup):
    # First, create a user
    data = {
        "email": "user92@example.com",
        "password": "user92@example.com",
        "first_name": "string",
        "last_name": "string",
        "is_superuser": True
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    # Now, test login with an incorrect password
    login_data = {
        "email": "user92@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 500

# To test user verification
def test_user_verification(db_setup):
    # Register the user
    data = {
        "email": "user93@example.com",
        "password": "user93@example.com",
        "first_name": "string",
        "last_name": "string",
        "is_superuser": True
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    # Get the verification link from the response
    access_token = response.json()["access_token"]
    
    # Test verification using the token
    response = client.get(f"/verify/{access_token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully!"
