# Tasflou API (Task Tracker Backend)

![FastAPI](https://img.shields.io/badge/FastAPI-0.128-05998b?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D00000?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2%20%26%20Cognito-232F3E?logo=amazon-aws&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.5-37814A?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-28-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

This is the backend API for **Tasflou**, a modern task management system designed for high performance and smooth user experience.


## 🎯 Project Goals
Tasflou was built as a comprehensive portfolio project to demonstrate mastery over the entire software development lifecycle—from architectural design and frontend optimization to cloud deployment and CI/CD automation. The focus was on creating a production-ready, accessible, and performant application that mirrors industry-standard engineering practices.

🚀 **Live Demo:** [gauchoscript.dev/projects/tasflou](https://www.gauchoscript.dev/projects/tasflou)  
💻 **Frontend Repository:** [Tasflou Web](https://github.com/gauchoscript/tasflou)


## 🛠 Technical Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python) for high-performance, asynchronous endpoints.
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) with `asyncpg` for non-blocking database operations.
- **Database**: [PostgreSQL](https://www.postgresql.org/) for reliable relational data storage.
- **Auth**: [AWS Cognito](https://aws.amazon.com/cognito/) for secure, scalable user authentication.
- **Background Tasks**: [Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/) for processing notifications and stale task checks.
- **Push Notifications**: [Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging) to keep users engaged across devices.
- **Deployment**: Dockerized services (API, Worker, Beat, DB, Redis) with automated CI/CD via GitHub Actions to AWS.


## 🏗 Key Technical Highlights
### 1. Efficient Custom Ordering (Gap-based Algorithm)
Instead of a simple integer index that requires O(n) updates on every reorder, Tasflou implements a **gap-based positioning algorithm**.
- **The Logic**: Each task has a `position` (integer). When moving a task between position $A$ and $B$, the new position is calculated as `(A + B) // 2`.
- **Benefit**: Reordering is an **O(1) operation** in most cases, requiring only a single row update. Large initial gaps (1000) minimize the frequency of re-gapping operations.

### 2. Fully Asynchronous Architecture
The entire request-response lifecycle is non-blocking. This ensures high concurrency and low latency, especially for I/O bound operations like database queries and external service calls (Cognito, FCM).

### 3. Scalable Notification System
Using Celery Beat for scheduling and Celery Workers for execution, the system handles:
- **Proactive Stale Task Detection**: Identifying tasks that haven't been updated in 7 days.
- **Due Date Reminders**: Sending push notifications via FCM before tasks are due.
- **Quiet Hours**: Respecting user-defined quiet hours to ensure a non-intrusive experience.

### 4. Enterprise-Grade Auth Integration
Offloading authentication to **AWS Cognito** provides production-ready security features like MFA, password recovery, and secure session management without adding complexity to the application core.


## 📂 Project Structure
```text
app/
├── api/            # Route handlers (FastAPI)
├── core/           # Configuration and database setup
├── middleware/     # Custom middlewares (CloudFront, Auth)
├── models/         # SQLAlchemy 2.0 models
├── schemas/        # Pydantic V2 schemas
├── services/       # Business logic layer
└── workers/        # Celery app and task definitions
```


## 🚀 Getting Started
### Prerequisites
- Docker & Docker Compose

### Fast Track (Docker)
1. Clone the repository:
   ```bash
   git clone https://github.com/gauchoscript/task-tracker-api.git
   cd task-tracker-api
   ```
2. Create a `.env` file (see `.env.example`).
3. Run the stack:
   ```bash
   docker compose up -d
   ```
4. Access the API documentation (Swagger UI) at `http://localhost:8000/docs`.


## 📄 License
Project developed for portfolio purposes. Use for learning or reference.
