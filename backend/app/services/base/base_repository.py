"""
Base Repository Pattern Implementation

Provides standardized data access patterns with:
- Generic CRUD operations
- Query building utilities  
- Transaction management
- Audit trail integration
- Performance optimization
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union

from sqlalchemy import and_, or_, select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.core.infrastructure.database import Base

# Generic model type
ModelType = TypeVar('ModelType', bound=Base)


class QueryBuilder:
    """
    Fluent query builder for constructing complex database queries
    """
    
    def __init__(self, model_class: Type[ModelType], session: AsyncSession):
        self.model_class = model_class
        self.session = session
        self.query = select(model_class)
        self._joins = []
        self._filters = []
        self._orders = []
        self._limit_value = None
        self._offset_value = None
        self._eager_loads = []
    
    def filter(self, *conditions) -> 'QueryBuilder':
        """Add WHERE conditions"""
        self._filters.extend(conditions)
        return self
    
    def filter_by(self, **kwargs) -> 'QueryBuilder':
        """Add WHERE conditions using keyword arguments"""
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                self._filters.append(getattr(self.model_class, key) == value)
        return self
    
    def order_by(self, *columns) -> 'QueryBuilder':
        """Add ORDER BY clauses"""
        self._orders.extend(columns)
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """Add LIMIT clause"""
        self._limit_value = count
        return self
    
    def offset(self, count: int) -> 'QueryBuilder':
        """Add OFFSET clause"""
        self._offset_value = count
        return self
    
    def eager_load(self, *relationships) -> 'QueryBuilder':
        """Add eager loading for relationships"""
        self._eager_loads.extend(relationships)
        return self
    
    def join_load(self, *relationships) -> 'QueryBuilder':
        """Add joined loading for relationships"""
        for relationship in relationships:
            self.query = self.query.options(joinedload(relationship))
        return self
    
    def select_load(self, *relationships) -> 'QueryBuilder':
        """Add select loading for relationships"""
        for relationship in relationships:
            self.query = self.query.options(selectinload(relationship))
        return self
    
    def build(self) -> Select:
        """Build the final query"""
        query = self.query
        
        # Apply filters
        if self._filters:
            query = query.where(and_(*self._filters))
        
        # Apply ordering
        if self._orders:
            query = query.order_by(*self._orders)
        
        # Apply limit and offset
        if self._limit_value is not None:
            query = query.limit(self._limit_value)
        if self._offset_value is not None:
            query = query.offset(self._offset_value)
        
        # Apply eager loading
        for relationship in self._eager_loads:
            query = query.options(selectinload(relationship))
        
        return query
    
    async def all(self) -> List[ModelType]:
        """Execute query and return all results"""
        result = await self.session.execute(self.build())
        return result.scalars().all()
    
    async def first(self) -> Optional[ModelType]:
        """Execute query and return first result"""
        result = await self.session.execute(self.build())
        return result.scalars().first()
    
    async def count(self) -> int:
        """Get count of results"""
        query = select(func.count()).select_from(self.model_class)
        if self._filters:
            query = query.where(and_(*self._filters))
        result = await self.session.execute(query)
        return result.scalar()
    
    async def paginate(self, page: int, per_page: int) -> Dict[str, Any]:
        """Paginate results"""
        total = await self.count()
        items = await self.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_next': page * per_page < total,
            'has_prev': page > 1
        }


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository providing standard CRUD operations
    """
    
    def __init__(self, model_class: Type[ModelType], session: AsyncSession):
        self.model_class = model_class
        self.session = session
    
    def query(self) -> QueryBuilder:
        """Create a new query builder"""
        return QueryBuilder(self.model_class, self.session)
    
    async def get_by_id(self, id: Union[uuid.UUID, int, str]) -> Optional[ModelType]:
        """Get entity by primary key"""
        return await self.session.get(self.model_class, id)
    
    async def get_by_ids(self, ids: List[Union[uuid.UUID, int, str]]) -> List[ModelType]:
        """Get multiple entities by primary keys"""
        if not ids:
            return []
        
        # Assume primary key is 'id' - adjust if different
        pk_column = getattr(self.model_class, 'id')
        result = await self.session.execute(
            select(self.model_class).where(pk_column.in_(ids))
        )
        return result.scalars().all()
    
    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        **filters
    ) -> List[ModelType]:
        """Get all entities with optional filtering and pagination"""
        query_builder = self.query()
        
        if filters:
            query_builder = query_builder.filter_by(**filters)
        
        if order_by and hasattr(self.model_class, order_by):
            query_builder = query_builder.order_by(getattr(self.model_class, order_by))
        
        if limit is not None:
            query_builder = query_builder.limit(limit)
        
        if offset is not None:
            query_builder = query_builder.offset(offset)
        
        return await query_builder.all()
    
    async def count(self, **filters) -> int:
        """Count entities with optional filtering"""
        query_builder = self.query()
        if filters:
            query_builder = query_builder.filter_by(**filters)
        return await query_builder.count()
    
    async def create(self, **data) -> ModelType:
        """Create new entity"""
        entity = self.model_class(**data)
        self.session.add(entity)
        await self.session.flush()  # Get ID without committing
        await self.session.refresh(entity)
        return entity
    
    async def create_many(self, entities_data: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple entities in batch"""
        entities = [self.model_class(**data) for data in entities_data]
        self.session.add_all(entities)
        await self.session.flush()
        
        # Refresh all entities to get generated IDs
        for entity in entities:
            await self.session.refresh(entity)
        
        return entities
    
    async def update_by_id(
        self, 
        id: Union[uuid.UUID, int, str], 
        **data
    ) -> Optional[ModelType]:
        """Update entity by primary key"""
        entity = await self.get_by_id(id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            await self.session.flush()
            await self.session.refresh(entity)
        return entity
    
    async def update_many(
        self, 
        filters: Dict[str, Any], 
        updates: Dict[str, Any]
    ) -> int:
        """Update multiple entities matching filters"""
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                conditions.append(getattr(self.model_class, key) == value)
        
        if not conditions:
            return 0
        
        stmt = update(self.model_class).where(and_(*conditions)).values(**updates)
        result = await self.session.execute(stmt)
        return result.rowcount
    
    async def delete_by_id(self, id: Union[uuid.UUID, int, str]) -> bool:
        """Delete entity by primary key"""
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            return True
        return False
    
    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """Delete multiple entities matching filters"""
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                conditions.append(getattr(self.model_class, key) == value)
        
        if not conditions:
            return 0
        
        stmt = delete(self.model_class).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.rowcount
    
    async def exists(self, **filters) -> bool:
        """Check if entity exists with given filters"""
        count = await self.count(**filters)
        return count > 0
    
    async def find_one(self, **filters) -> Optional[ModelType]:
        """Find single entity matching filters"""
        query_builder = self.query()
        if filters:
            query_builder = query_builder.filter_by(**filters)
        return await query_builder.first()
    
    async def find_many(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[str]] = None
    ) -> List[ModelType]:
        """Find multiple entities with advanced filtering"""
        query_builder = self.query()
        
        if filters:
            query_builder = query_builder.filter_by(**filters)
        
        if order_by:
            for order_field in order_by:
                if hasattr(self.model_class, order_field):
                    query_builder = query_builder.order_by(getattr(self.model_class, order_field))
        
        if limit is not None:
            query_builder = query_builder.limit(limit)
        
        if offset is not None:
            query_builder = query_builder.offset(offset)
        
        return await query_builder.all()
    
    async def paginate(
        self, 
        page: int = 1, 
        per_page: int = 20, 
        **filters
    ) -> Dict[str, Any]:
        """Paginate entities with optional filtering"""
        query_builder = self.query()
        if filters:
            query_builder = query_builder.filter_by(**filters)
        
        return await query_builder.paginate(page, per_page)
    
    async def bulk_insert(self, entities_data: List[Dict[str, Any]]) -> None:
        """Bulk insert for better performance with large datasets"""
        if not entities_data:
            return
        
        # Use SQLAlchemy core for bulk operations
        from sqlalchemy import insert
        
        stmt = insert(self.model_class).values(entities_data)
        await self.session.execute(stmt)
    
    async def bulk_update(
        self, 
        updates: List[Dict[str, Any]], 
        index_elements: Optional[List[str]] = None
    ) -> None:
        """Bulk update for better performance"""
        if not updates:
            return
        
        # Use upsert if index elements provided
        if index_elements:
            from sqlalchemy.dialects.postgresql import insert
            
            stmt = insert(self.model_class).values(updates)
            update_dict = {
                key: stmt.excluded[key] 
                for key in updates[0].keys() 
                if key not in (index_elements or [])
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict
            )
            await self.session.execute(stmt)
        else:
            # Regular bulk insert
            await self.bulk_insert(updates)


class TimescaleRepository(BaseRepository[ModelType]):
    """
    Repository specialized for TimescaleDB time-series operations
    """
    
    async def get_time_range_data(
        self,
        start_time: str,
        end_time: str,
        time_column: str = 'time',
        **filters
    ) -> List[ModelType]:
        """Get data within a time range"""
        query_builder = self.query()
        
        time_col = getattr(self.model_class, time_column)
        query_builder = query_builder.filter(
            time_col >= start_time,
            time_col <= end_time
        )
        
        if filters:
            query_builder = query_builder.filter_by(**filters)
        
        return await query_builder.order_by(time_col).all()
    
    async def get_latest(self, time_column: str = 'time', **filters) -> Optional[ModelType]:
        """Get the most recent record"""
        query_builder = self.query()
        
        if filters:
            query_builder = query_builder.filter_by(**filters)
        
        time_col = getattr(self.model_class, time_column)
        query_builder = query_builder.order_by(time_col.desc()).limit(1)
        
        return await query_builder.first()
    
    async def get_aggregated_data(
        self,
        time_bucket: str,
        aggregates: List[str],
        start_time: str,
        end_time: str,
        time_column: str = 'time',
        group_by: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get time-bucketed aggregated data"""
        # This would use TimescaleDB's time_bucket function
        # Implementation depends on specific use cases
        pass