from fastapi import APIRouter, HTTPException
from typing import List
from app.models.item import Item, ItemCreate, ItemUpdate

router = APIRouter()

# In-memory storage for demo purposes
items_db = []


@router.get("/", response_model=List[Item])
async def get_items():
    """Get all items"""
    return items_db


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get a specific item by ID"""
    item = next((item for item in items_db if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=Item, status_code=201)
async def create_item(item: ItemCreate):
    """Create a new item"""
    new_item = Item(
        id=len(items_db) + 1,
        **item.dict()
    )
    items_db.append(new_item)
    return new_item


@router.put("/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemUpdate):
    """Update an existing item"""
    item = next((item for item in items_db if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int):
    """Delete an item"""
    global items_db
    item = next((item for item in items_db if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db = [item for item in items_db if item.id != item_id]
    return None
