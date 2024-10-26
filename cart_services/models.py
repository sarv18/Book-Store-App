from sqlalchemy import Column, Integer, Boolean, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from settings import settings, logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Base class for all models
Base = declarative_base()

# Engine and session for the database
engine = create_engine(settings.carts_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the DB session
def get_db():
    '''
    Description:
    This function provides a database session to be used for each request. 
    It ensures that the session is properly closed after the request.
    Yields:
    SessionLocal: The database session for querying and interacting with the database.
    Raises:
    Logs any unexpected database connection issues.
    '''
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        raise HTTPException(status_code=500, detail="Internal database error")
    finally:
        try:
            db.close()
            logger.info("Database session closed.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to close the database session: {e}")


class Cart(Base):
    __tablename__ = "carts"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement= True)
    total_price = Column(Integer, default=0)
    total_quantity = Column(Integer, default=0)
    is_ordered = Column(Boolean, default=False)
    user_id = Column(BigInteger, nullable=False)

    items = relationship("CartItem", back_populates="cart")

    @property
    def to_dict(self):
        """
        Converts the `books` object to a dictionary format.
        Returns:
        dict: A dictionary containing all the User attributes.
        """
        try:
            cart_dict = {col.name: getattr(self, col.name) for col in self.__table__.columns}
            # Adding related items to the dictionary
            cart_dict["items"] = [item.to_dict for item in self.items] 
            return cart_dict
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing cart data")


class CartItem(Base):
    __tablename__ = "cart_items"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement= True)
    book_id = Column(BigInteger, nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Integer, default=0)
    cart_id = Column(BigInteger, ForeignKey("carts.id", ondelete='CASCADE'))

    cart = relationship("Cart", back_populates="items")

    @property
    def to_dict(self):
        """
        Converts the `books` object to a dictionary format.
        Returns:
        dict: A dictionary containing all the User attributes.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing cart item data")