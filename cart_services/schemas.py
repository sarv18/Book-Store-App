from pydantic import BaseModel
from typing import List


class CreateCartItemSchema(BaseModel):
    """
    This schema is used for creating a new cart item. It defines the fields required 
    for creating a cart item.
    """
    book_id: int
    quantity: int


class ResponseCartSchema(BaseModel):
    """
    This schema is used for creating a new cart. It defines the fields required 
    for creating a cart.
    """
    id: int
    total_price: int
    total_quantity: int
    user_id: int
    is_ordered: bool
    items: List[CreateCartItemSchema]
