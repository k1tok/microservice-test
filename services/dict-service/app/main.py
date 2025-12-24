from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI(title="Dictionary Service")

items_db = []

class Item(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    item.id = str(uuid.uuid4())
    items_db.append(item.dict())
    return item

@app.get("/items/", response_model=List[Item])
def read_items():
    return items_db

@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: str):
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: str, item_update: ItemUpdate):
    for item in items_db:
        if item["id"] == item_id:
            if item_update.name is not None:
                item["name"] = item_update.name
            if item_update.description is not None:
                item["description"] = item_update.description
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    for idx, item in enumerate(items_db):
        if item["id"] == item_id:
            items_db.pop(idx)
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")