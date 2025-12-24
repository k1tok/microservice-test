## Микросервисная архитектура на FastAPI, Kafka и Docker
Полноценная микросервисная архитектура с API Gateway, двумя сервисами (CRUD и обработчик задач) и брокером сообщений Kafka.
## Стек технологий
- FastAPI - современный веб-фреймворк для Python
- Apache Kafka - распределенный брокер сообщений для асинхронной коммуникации
- Docker & Docker Compose - контейнеризация и оркестрация
- Apache ZooKeeper - координация и управление кластером Kafka
- Pydantic - валидация данных и сериализация
- Uvicorn - ASGI сервер для FastAPI
- Kafka UI - веб-интерфейс для мониторинга Kafka
## Структура проекта
```text
project-root/
├── docker-compose.yml          # Конфигурация всех сервисов
├── services/
│   ├── core-service/          # API Gateway
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       └── main.py
│   ├── dict-service/          # CRUD сервис
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       └── main.py
│   └── task-service/          # Сервис задач с Kafka
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app/
│           └── main.py
├── postman/                   # Коллекция Postman
│   └── microservice-collection.json
└── README.md                  # Эта документация
```
## Установка и запуск
1. Клонирование репозитория 
```bash
git clone https://github.com/k1tok/microservice-test.git
cd project-root
```
2. Запуск сервисов/остановка
```bash
docker-compose up --build 
# или
docker-compose down
```
## Доступные сервисы
После запуска будут доступны(Сервис	URL	Описание	Порт):

- API Gateway	http://localhost:8000	Единая точка входа	8000
- dict-service	http://localhost:8001	Прямой доступ к CRUD API	8001
- task-service	http://localhost:8002	Прямой доступ к Kafka API	8002
- Kafka UI	http://localhost:8080	Мониторинг Kafka	8080
- Zookeeper	http://localhost:2181	Для Kafka (внутренний)	2181
- Kafka Broker	http://localhost:9092	Брокер сообщений (внутренний)	9092

## API Endpoints
#### dict-service (CRUD операции)
```bash
GET    /dict/items/           # Получить все items
GET    /dict/items/{id}       # Получить item по ID
POST   /dict/items/           # Создать новый item
PUT    /dict/items/{id}       # Обновить item
DELETE /dict/items/{id}       # Удалить item
```
#### task-service (Kafka + задачи)
```bash
GET    /tasks/tasks/          # Получить все задачи
GET    /tasks/tasks/{id}      # Получить задачу по ID
POST   /tasks/tasks/          # Создать задачу (отправляет в Kafka)
PUT    /tasks/tasks/{id}      # Обновить задачу
DELETE /tasks/tasks/{id}      # Удалить задачу
GET    /tasks/health          # Проверка здоровья
```
### core-service (GATEWAY)
```bash
GET   /health                # Здоровье GATEWAY
GET   /debug                 # Ошибки GATEWAY
```
