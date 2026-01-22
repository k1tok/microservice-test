from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_item():
    """Тест создания элемента"""
    item_data = {
        "name": "Test Item",
        "description": "Test Description"
    }
    
    response = client.post("/items/", json=item_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "Test Description"
    assert "id" in data
    return data["id"] 

def test_get_all_items():
    """Тест получения всех элементов"""
    response = client.get("/items/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"Found {len(data)} items")