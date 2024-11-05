from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Base, get_db
from .routes import app
import pytest
import responses


# Create a TestClient instance
client = TestClient(app)

# Set up the test database
engine = create_engine("postgresql://postgres:password@localhost/test")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db_setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def auth_user_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:8000/user/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8",
        json= {
            "message": "Authorizaton successful",
            "status": "success",
            "data": {
                    "id": 1,
                    "email": "user91@example.com",
                    "first_name": "string",
                    "last_name": "string",
                    "is_verified": True,
                    "is_superuser": True
                }
        },
        status=200
    )

# Test case for creating a successful book with mocked external API
@responses.activate
def test_create_book_successful(db_setup, auth_user_mock):
    
    # Payload for creating a book
    data = {
        "name": "string",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
        }

    # Call the create book API
    response = client.post("/books/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 201
    
# Test case for create book invalid fields
@responses.activate
def test_create_book_invalid_field(db_setup, auth_user_mock):
    
    # Payload for creating a book
    data = {
        "name": "string",
        "author": 123,
        "description": "string",
        "price": 0,
        "stock": 0
        }

    # Call the create book API
    response = client.post("/books/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 422 
    
# Test case for ceate book missing fields
@responses.activate
def test_create_book_missing_field(db_setup, auth_user_mock):
    
    # Payload for creating a book
    data = {
        "name": "string",
        "author": "string",
        "description": "string",
        "price": 0
        }

    # Call the create book API
    response = client.post("/books/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 422
    
# Test case for getting all books successfully
@responses.activate
def test_get_all_books_successful(db_setup, auth_user_mock):

    # Add book to the database setup
    book1 = {
        "name": "string12",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }
    book2 = {
        "name": "string123",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }

    # Insert books through API (assuming POST works correctly)
    client.post("/books/", json=book1, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    client.post("/books/", json=book2, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Call the GET all books API
    response = client.get("/books/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200

# Test case for no books found
@responses.activate
def test_get_all_books_no_books(db_setup, auth_user_mock):

    # No books are present in the database setup

    # Call the GET all books API
    response = client.get("/books/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404
    
    
# Test case for successfully updating a book
@responses.activate
def test_update_book_successful(db_setup, auth_user_mock):
    
    # Step 1: Create a book to be updated
    initial_book = {
        "name": "string",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }
    
    # Insert the book via the API
    create_response = client.post("/books/", json=initial_book, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    book_id = create_response.json()["data"]["id"]  # Extract note_id from the response
    
    # Step 2: Define the updated book payload
    updated_book = {
        "name": "string",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }

    # Step 3: Call the PUT API to update the book
    response = client.put(f"/books/{book_id}", json=updated_book, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Step 4: Assert the response
    assert response.status_code == 200
    
# Test case for updating a non-existent book (404 error)
@responses.activate
def test_update_book_not_found(db_setup, auth_user_mock):
    
    # Define the payload for the update
    updated_book = {
        "name": "string",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }

    # Call the PUT API for a book ID that does not exist
    response = client.put("/books/9999", json=updated_book, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response
    assert response.status_code == 404

# Test case for successful book delete
@responses.activate
def test_delete_book_success(db_setup, auth_user_mock):
    
    # Step 1: Create a book to be updated
    initial_book = {
        "name": "string",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }
    
    # Insert the book via the API
    create_response = client.post("/books/", json=initial_book, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    book_id = create_response.json()["data"]["id"]  # Extract note_id from the response
    
    # Call the delete book API
    response = client.delete(f"/books/{book_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200

# Test Case for Trying to Delete a Non-Existent book
@responses.activate
def test_delete_book_not_found(db_setup, auth_user_mock):
    # book ID that doesn't exist
    book_id = 999
    
    # Call the delete book API
    response = client.delete(f"/books/{book_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404

# Test case for getting book by id successfully
@responses.activate
def test_get_book_by_id_successful(db_setup, auth_user_mock):

    # Add book to the database setup
    book1 = {
        "name": "string12",
        "author": "string",
        "description": "string",
        "price": 0,
        "stock": 0
    }
    
    # Insert books through API (assuming POST works correctly)
    create_response= client.post("/books/", json=book1, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Extract note_id from the response
    book_id = create_response.json()["data"]["id"]  
    
    # Call the GET all books API
    response = client.get(f"/books/{book_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200

# Test case for no books found
@responses.activate
def test_get_book_no_book(db_setup, auth_user_mock):

    # No books are present in the database setup

    # Call the GET all books API
    response = client.get(f"/books/{999}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404
    