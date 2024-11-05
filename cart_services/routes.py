from fastapi import FastAPI, Depends, HTTPException, Security, Request
from sqlalchemy.orm import Session
from .models import Cart, CartItem, get_db
from .schemas import CreateCartItemSchema
from .utils import auth_user
from settings import settings, logger
from fastapi.security import APIKeyHeader
import requests as http


# Initialize FastAPI app with dependency
app = FastAPI(dependencies=[Security(APIKeyHeader(name="Authorization", auto_error=False)), Depends(auth_user)])

# CREATE Cart Item
@app.post("/cart/items/", status_code=201)
def create_or_update_cart_item(request: Request, body: CreateCartItemSchema, db: Session = Depends(get_db)):
    """
    Create a new cart item and update the cart. Only authorized users can perform this action.
    Parameters:
    body: A `CreateCartItemSchema` schema instance containing the cart item details.
    db: The database session to interact with the database.
    Returns:
    dict: A dictionary containing a success message and the newly created cart details.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        # Verify the book exists in book_services
        book_service_url = f"{settings.book_services_url}{body.book_id}"
        response = http.get(book_service_url, headers={"Authorization": request.headers.get("Authorization")})
      
        # It chaecks the response is not satisfying then raise error
        if response.status_code != 200:
            logger.info(f"Book with ID {body.book_id} not found.")
            raise HTTPException(status_code=400, detail=f"Book with ID {body.book_id} not found")

        # Parse the response JSON
        book_response = response.json()
        
        # Extract book price from book_response
        book_price = book_response["data"].get("price")
        book_stock = book_response["data"].get("stock")

        # Validate that price and stock are available
        if book_price is None or book_stock is None:
            logger.error("Book price or stock not found in book data.")
            raise HTTPException(status_code=500, detail="Book price or stock not available")
        
        # Check if requested quantity exceeds the stock available
        if body.quantity > book_stock:
            logger.error(f"Requested quantity {body.quantity} exceeds available stock {book_stock}.")
            raise HTTPException(status_code=400, detail="Requested quantity exceeds available stock")
  
        # Get or create the user's cart
        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == False).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        # Check if the cart item already exists
        cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.book_id == body.book_id).first()
        if cart_item:
            cart_item.quantity = body.quantity
            cart_item.price = book_price * body.quantity
        else:
            cart_item = CartItem(cart_id=cart.id, book_id=body.book_id, quantity=body.quantity)
            cart_item.price = book_price * body.quantity
            db.add(cart_item)

        # Recalculate total price and quantity
        db.commit()
        db.refresh(cart)
        cart.total_price = sum(item.price for item in cart.items)
        cart.total_quantity = sum(item.quantity for item in cart.items)
        
        # Commit all changes
        db.commit()
        logger.info(f"Cart updated for user: {user_data['email']}")

        return {
            "message": "Cart item added successfully",
            "status": "success",
            "data": cart_item.to_dict
        }

    except HTTPException as e:
        logger.error(f"Error during cart item creation: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during cart item creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# GET Cart
@app.get("/cart/", status_code=200)
def get_cart(request: Request, db: Session = Depends(get_db)):
    """
    Get the user's cart details.
    Parameters:
    db: The database session to interact with the database.
    Returns:
    dict: A dictionary containing a success message and retrieved cart details.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == False).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")


        logger.info(f"Cart retrieved for user: {user_data['email']}")

        return {
            "message": "Cart retrieved successfully",
            "status": "success",
            "data": cart.to_dict
        }

    except HTTPException as e:
        logger.error(f"Error during cart retrieval: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during cart retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# DELETE Cart Item
@app.delete("/cart/items/{item_id}", status_code=200)
def delete_cart_item(request: Request, item_id: int, db: Session = Depends(get_db)):
    """
    Delete a cart item from the user's cart.
    Parameters:
    item_id: The ID of the cart item to delete.
    db: The database session to interact with the database.
    Returns:
    dict: A success message confirming the deletion of the cart item.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        # Retrieve the user's cart
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        # Delete the cart item
        db.delete(cart_item)
        db.commit()

        # Recalculate the cart's total price and quantity
        cart.total_price = sum(item.quantity * item.price for item in cart.items)
        cart.total_quantity = sum(item.quantity for item in cart.items)
        
        # Commit the updated cart totals
        db.commit()
        
        logger.info(f"Cart item deleted for user: {user_data['email']}, cart totals updated.")

        return {
            "message": "Cart item deleted successfully",
            "status": "success"
        }

    except HTTPException as e:
        logger.error(f"Error during cart item deletion: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during cart item deletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# Place the order
@app.patch("/cart/place-order", status_code=201)
def place_order(request: Request, db: Session = Depends(get_db)):
    """
    Create an order from the user's cart, validate stock availability, and update stock quantities.
    Parameters:
    db: The database session to interact with the database.
    Return:
    dict: A dictionary containing a success message.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        # Checking the actice cart is present or not having is_order == False 
        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == False).first()
        if not cart or not cart.items:
            raise HTTPException(status_code=404, detail="Cart is empty or already ordered.")

        for item in cart.items:
            book_service_url = f"{settings.book_services_url}{item.book_id}"
            response = http.get(book_service_url, headers={"Authorization": request.headers.get("Authorization")})

            if response.status_code != 200:
                logger.info(f"Book with ID {item.book_id} not found in book service.")
                raise HTTPException(status_code= 400, detail=f"Book with ID {item.book_id} not found.")

            book_data = response.json()
            book_stock = book_data["data"].get("stock")

            # Cheking the order quantity is higher than the stock
            if item.quantity > book_stock:
                logger.warning(f"Insufficient stock for book ID {item.book_id}. Requested: {item.quantity}, Available: {book_stock}")
                raise HTTPException(status_code= 406, detail=f"Insufficient stock for book ID {item.book_id}")  

        # Updating the book stock in BOOK DB
        for item in cart.items:
            book_service_url = f"{settings.book_services_url}adjust_stock/{item.book_id}"
            update_response = http.patch(book_service_url, json={"quantity": item.quantity}, headers={"Authorization": request.headers.get("Authorization")})

            if update_response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to restore stock for Book ID {item.book_id}")

        # Commiting the database as true
        cart.is_ordered = True
        db.commit()
        logger.info(f"Order created successfully for user ID {user_id}")

        return {
            "message": "Order placed successfully",
            "status": "success",
            "data": cart.to_dict
        }

    except HTTPException as error:
        logger.error(f"Order creation error: {str(error.detail)}")
        raise error

    except Exception as error:
        logger.error(f"Unexpected error during order creation: {str(error)}")
        raise HTTPException(status_code= 500, detail="Unexpected error occurred")


# Get the all placed order
@app.get("/order-details", status_code=200)
def get_order_details(request: Request, db: Session = Depends(get_db)):
    """
    Retrieve the order details for the logged-in user.
    Parameters:
    db: The database session to interact with the database.
    Return:
    dict: A dictionary containing a success message and order details.
    """
    try:
        # Retrieve the authenticated user's ID
        user_data = request.state.user
        user_id = user_data["id"]

        # Query the ordered cart for the user
        carts = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == True).all()
        if not carts:
            raise HTTPException(status_code=404, detail=f'No order found for the user {user_data["email"]}')

        logger.info(f"Order details retrieved for user ID {user_id}")
            
        # Prepare order details
        order_details = []
        for cart in carts:  # Iterate through each cart
            # Prepare the cart details
            cart_data = {
                "id": cart.id,
                "total_price": cart.total_price,
                "total_quantity": cart.total_quantity,
                "is_ordered": cart.is_ordered,
                "user_id": cart.user_id,
                "items": []
            }
            for item in cart.items:  # Iterate through each item in the cart
                cart_data["items"].append(CartItem(book_id=item.book_id, id=item.id, quantity=item.quantity, price= item.price, cart_id= item.cart_id).to_dict)

            order_details.append(cart_data)
            
        # Return order details response
        return {
            "message": "Order details fetched successfully",
            "status": "success",
            "data": order_details
        }

    except HTTPException as error:
        logger.error(f"Error fetching order details: {str(error.detail)}")
        raise error
    except Exception as error:
        logger.error(f"Unexpected error while fetching order details: {str(error)}")
        raise HTTPException(status_code= 500, detail="Unexpected error occurred")


# Delete the cart, if order is not placed
@app.delete("/cancel-order/", status_code=200)
def cancel_order(request: Request, db: Session = Depends(get_db)):
    """
    Delete the entire cart and restore the stock of each item in the book database.
    Parameters:
    db: The database session to interact with the database.
    Return:
    dict: A dictionary containing order cancel message.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        # Retrieve the user's active cart
        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == True).first()
        if not cart or not cart.items:
            raise HTTPException(status_code=404, detail="Cart not found or empty")

        # Restoring the book stock in BOOK DB
        for item in cart.items:
            book_service_url = f"{settings.book_services_url}adjust_stock/{item.book_id}"
            restore_response = http.patch(book_service_url, json={"quantity": -(item.quantity)}, headers={"Authorization": request.headers.get("Authorization")})

            if restore_response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to restore stock for Book ID {item.book_id}")
        
        # Delete the cart after stock adjustment
        db.delete(cart)
        db.commit()
        logger.info(f"Cart and items deleted for user: {user_data['email']}.")

        return {
            "message": "Order cancelled and stock restored successfully",
            "status": "success"
        }

    except HTTPException as error:
        logger.error(f"Error during cart deletion: {str(error.detail)}")
        raise error
    except Exception as error:
        logger.error(f"Unexpected error during cart deletion: {str(error)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
    