from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Base as SQLAlchemyBase

# Define generic type variables
ModelType = TypeVar("ModelType", bound=SQLAlchemyBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository with CRUD operations for SQLAlchemy models.
    
    Uses the Repository pattern to abstract database operations.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the repository with a SQLAlchemy model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            db: Database session
            id: ID of the record
            
        Returns:
            Record or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[ModelType]:
        """
        Get a record by a field value.
        
        Args:
            db: Database session
            field: Field name
            value: Field value
            
        Returns:
            Record or None if not found
        """
        return db.query(self.model).filter(getattr(self.model, field) == value).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_filtered(
        self, db: Session, *, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get records with filters.
        
        Args:
            db: Database session
            filters: Dictionary of field names and values
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of filtered records
        """
        query = db.query(self.model)
        
        for field, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic model with record data
            
        Returns:
            Created record
        """
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Record to update
            obj_in: Pydantic model or dict with fields to update
            
        Returns:
            Updated record
        """
        obj_data = db_obj.__dict__
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data and field != "id":
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Delete a record.
        
        Args:
            db: Database session
            id: ID of the record to delete
            
        Returns:
            Deleted record
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj