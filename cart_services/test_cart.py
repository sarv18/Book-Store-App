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

@pytest.fixture
def book_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:9000/books/2",
        json= {
                "message": "Book retrieved successfully",
                "status": "success",
                "data": {
                    "user_id": 4,
                    "author": "sarvesh",
                    "stock": 30,
                    "id": 2,
                    "description": "string",
                    "name": "book2",
                    "price": 200
                }
        },
        status=200
    )
    
@pytest.fixture
def adjust_stock_mock():
    responses.add(
        responses.PATCH,
        "http://127.0.0.1:9000/books/adjust_stock/2",
        json= {
            "quantity": 50
        },
        status=200
    )
    
# Test case for creating a successful cart with mocked external API
@responses.activate
def test_create_or_update_cart_successful(db_setup, auth_user_mock, book_mock):
    
    # Payload for creating a cart
    data = {
        "book_id": 2,
        "quantity": 30
    }

    # Call the create cart API
    response = client.post("/cart/items", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 201
    
# Test case for create cart invalid fields
@responses.activate
def test_create_or_update_cart_invalid_field(db_setup, auth_user_mock, book_mock):
    
    # Payload for creating a cart
    data = {     
        "book_id":  "abc",
        "quantity": 30
        }

    # Call the create cart API
    response = client.post("/cart/items", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 422 
    
# Test case for ceate cart missing fields
@responses.activate
def test_create_or_update_cart_missing_field(db_setup, auth_user_mock, book_mock):
    
    # Payload for creating a cart
    data = {
       
        "quantity": 30
        }

    # Call the create cart API
    response = client.post("/cart/items", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
        
    # Assert the response status code and content
    assert response.status_code == 422
    
# Test case for getting cart successfully
@responses.activate
def test_get_cart_successful(db_setup, auth_user_mock, book_mock):

    # Add cart to the database setup
    cart1 = {
        "book_id": 1,
        "quantity": 30
    }
    cart2 = {
        "book_id": 2,
        "quantity": 30
    }

    # Insert books through API (assuming POST works correctly)
    client.post("/cart/items", json=cart1, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    client.post("/cart/items", json=cart2, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Call the GET all books API
    response = client.get("/cart/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200

# Test case for no cart found
@responses.activate
def test_get_cart_no_carts(db_setup, auth_user_mock):

    # No books are present in the database setup

    # Call the GET all books API
    response = client.get("/cart/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404

# Test case for successful cart delete
@responses.activate
def test_delete_cart_success(db_setup, auth_user_mock, book_mock):
    
    # Step 1: Create a cart to be updated
    initial_cart = {
        "book_id": 2,
        "quantity": 30
    }
    
    # Insert the cart via the API
    create_response = client.post("/cart/items", json=initial_cart, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    assert create_response.status_code == 201
    
    cart_id = create_response.json()["data"]["id"]  # Extract note_id from the response
    
    # Call the delete cart API
    response = client.delete(f"/cart/items/{cart_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200

# Test Case for trying to Delete a Non-Existent cart
@responses.activate
def test_delete_cart_not_found(db_setup, auth_user_mock):
    # cart ID that doesn't exist
    cart_id = 999
    
    # Call the delete cart API
    response = client.delete(f"/cart/items/{cart_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404

# Test case for order place successfully
@responses.activate
def test_place_order_successful(db_setup, auth_user_mock, book_mock, adjust_stock_mock): 
    # Payload for creating a cart
    data = {
        "book_id": 2,
        "quantity": 30
    }

    # Call the create cart API
    client.post("/cart/items", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
       
    # Call the palce order API
    response = client.patch(f"/cart/place-order", json= data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    print(f"Response content: {response.json()}")

    # Assert the response status code and content
    assert response.status_code == 201

# Test case to get order details successfully
@responses.activate
def test_order_details_successful(db_setup, auth_user_mock, book_mock, adjust_stock_mock): 
    
    # Payload for creating a cart
    data = {
        "book_id": 2,
        "quantity": 30
    }

    # Call the create cart API
    client.post("/cart/items", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Call to place order API
    client.patch(f"/cart/place-order", json= data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Call the GET order details API
    response = client.get(f"/order-details", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200


# Test case to cancel order successfully
@responses.activate
def test_cancel_order_successfully(db_setup, auth_user_mock, book_mock, adjust_stock_mock):

    # Payload for creating a cart
    data = {
        "book_id": 2,
        "quantity": 30
    }

    # Call the create cart API
    client.post("/cart/items", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Call to place order API
    client.patch(f"/cart/place-order", json= data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})
    
    # Call the cancel-order API
    response = client.delete(f"cancel-order", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 200
    
# Test case to cancel oreder when there is no order
@responses.activate
def test_cancel_order_no_order(db_setup, auth_user_mock, book_mock):

    # No order created
    
    # Call the delete cart API
    response = client.delete(f"cancel-order", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOTFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxfQ._XsC7qgHEpBvaZbzPmgDOOPnDUw9W6_UCpNDyhlgA-8"})

    # Assert the response status code and content
    assert response.status_code == 404
    