from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from kafka import KafkaProducer
import json
from typing import Optional, List
import uuid
from datetime import datetime

app = FastAPI(title="Task Service")

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
TASK_TOPIC = "tasks"
TASK_EVENTS_TOPIC = "task_events" 

tasks_db = []

_producer: Optional[KafkaProducer] = None

def get_producer() -> KafkaProducer:
    """Ленивая инициализация продюсера Kafka"""
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=3,
            retry_backoff_ms=500
        )
    return _producer

class TaskBase(BaseModel):
    title: str
    description: str
    priority: str = "medium"

class TaskCreate(TaskBase):
    """Модель для создания задачи"""
    pass

class TaskUpdate(BaseModel):
    """Модель для обновления задачи (все поля опциональны)"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class Task(TaskBase):
    """Модель для отдачи задачи (с системными полями)"""
    id: str
    status: str = "pending" 
    created_at: str
    updated_at: str

def send_to_kafka(topic: str, event_type: str, task_data: dict):
    """Отправка события в Kafka"""
    producer = get_producer()
    event = {
        "event_type": event_type,
        "event_time": datetime.now().isoformat(),
        "data": task_data
    }
    producer.send(topic, value=event)
    producer.flush()

def find_task_index(task_id: str) -> int:
    """Найти индекс задачи по ID"""
    for idx, task in enumerate(tasks_db):
        if task["id"] == task_id:
            return idx
    return -1

@app.post("/tasks/", response_model=Task)
async def create_task(task_create: TaskCreate, background_tasks: BackgroundTasks):
    """Создать новую задачу"""
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    task_data = {
        "id": task_id,
        "title": task_create.title,
        "description": task_create.description,
        "priority": task_create.priority,
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }
    
    tasks_db.append(task_data)
    
    send_to_kafka(TASK_TOPIC, "task_created", task_data)
    
    background_tasks.add_task(process_task, task_data)
    
    return task_data

@app.get("/tasks/", response_model=List[Task])
async def get_all_tasks(status: Optional[str] = None, priority: Optional[str] = None):
    """Получить все задачи с возможностью фильтрации"""
    filtered_tasks = tasks_db
    
    if status:
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
    
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
    
    return filtered_tasks

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Получить задачу по ID"""
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[idx]

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate):
    """Обновить задачу"""
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[idx]
    
    if task_update.title is not None:
        task["title"] = task_update.title
    
    if task_update.description is not None:
        task["description"] = task_update.description
    
    if task_update.priority is not None:
        task["priority"] = task_update.priority
    
    if task_update.status is not None:
        task["status"] = task_update.status
    
    task["updated_at"] = datetime.now().isoformat()
    
    send_to_kafka(TASK_EVENTS_TOPIC, "task_updated", task)
    
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Удалить задачу"""
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db.pop(idx)
    
    send_to_kafka(TASK_EVENTS_TOPIC, "task_deleted", task)
    
    return {"message": "Task deleted", "task_id": task_id}

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Получить статус задачи"""
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": tasks_db[idx]["status"],
        "updated_at": tasks_db[idx]["updated_at"]
    }

@app.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Отметить задачу как выполненную"""
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[idx]
    task["status"] = "completed"
    task["updated_at"] = datetime.now().isoformat()
    
    send_to_kafka(TASK_EVENTS_TOPIC, "task_completed", task)
    
    return {"message": "Task marked as completed", "task_id": task_id}

def process_task(task_data: dict):
    """Имитация обработки задачи"""
    print(f"[PROCESSING] Task {task_data['id']}: {task_data['title']}")
    print(f"[COMPLETED] Task {task_data['id']} processed")

@app.get("/health")
async def health():
    try:
        producer = get_producer()
        return {
            "status": "healthy",
            "kafka": "connected",
            "total_tasks": len(tasks_db),
            "service": "task-service"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "kafka": "disconnected",
            "error": str(e)[:100],
            "total_tasks": len(tasks_db)
        }

@app.on_event("startup")
async def startup_event():
    """Действия при запуске сервиса"""
    print("Task Service starting up...")
    get_producer()
    print(f"Kafka producer initialized. Topic: {TASK_TOPIC}")

@app.get("/debug")
async def debug():
    return {
        "service": "task-service",
        "kafka_topic": TASK_TOPIC,
        "total_tasks": len(tasks_db),
        "tasks": tasks_db[:5] if tasks_db else []
    }