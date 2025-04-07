# PP-CGA-BE

## FastAPI Backend for User and Game Management

### Local Setup

- Install Python 3.12
- Install all requirements from `requirements.txt`
- Start the application with `python app.py`
- Open `http://localhost:8070/` in your browser

If there are errors during the installation of the dependencies, you may need to create a local virtual environment.

## API Documentation

FastAPI provides interactive API documentation at:

- Swagger UI: `http://localhost:8070/docs`
- ReDoc: `http://localhost:8070/redoc`

---

## Key Endpoints

### Users

| Method | Endpoint | Description        |
|--------|----------|--------------------|
| GET    | `/user`  | List all users.    |
| POST   | `/user`  | Create a new user. |

### Games

| Method    | Endpoint                       | Description                |
|-----------|--------------------------------|----------------------------|
| GET       | `/game/{code}`                 | List all games.            |
| POST      | `/game`                        | Create a new game.         |
| WebSocket | `/game/ws/{game_id}/{user_id}` | Join a game via WebSocket. |

---

## Overview

This repository contains a FastAPI-based backend for managing users and games, including WebSocket support for real-time
game interactions. The application uses SQLAlchemy for database interactions and is containerized with **Docker**.

Key features of this backend:

1. API endpoints for user management (create, retrieve, list users).
2. API endpoints for game management (create, retrieve, list games).
3. Real-time communication for multiplayer games using WebSockets.

---

## Features

### User Management

- Create users with unique usernames.
- List all users.
- Retrieve details of a specific user.

### Game Management

- Create new games with unique codes.
- List all games.
- Retrieve details of a specific game.
- Manage game states, players, and actions.

### Real-Time Game Logic

- WebSocket endpoints to allow players to join and interact in a game.
- Core game logic for **Mau Mau** card game (implemented in `logic/maumau.py`).

### Database

- PostgreSQL database using SQLAlchemy ORM.
- Automatic database schema creation via SQLAlchemy models.

### Containerization

- Docker setup with PostgreSQL database and backend service.
- Support for `docker-compose` for easy multi-container deployments.

### Continuous Integration

- CI workflow using GitHub Actions to build and publish Docker images.

---

## Project Structure

```plaintext
.
├── app.py                      # Entry point for the FastAPI application.
├── routers/                    # API route definitions for users and games.
│   ├── user.py                 # User endpoints.
│   └── game.py                 # Game endpoints and WebSocket logic.
├── models/                     # SQLAlchemy models for database entities.
│   ├── custom_types.py         # Custom data types for SQLAlchemy.
│   ├── base.py                 # Base model with common fields.
│   ├── user.py                 # User model.
│   └── game.py                 # Game model.
├── schemas/                    # Pydantic schemas for validation and serialization.
│   ├── base.py                 # Base schemas with common fields.
│   ├── user.py                 # User schemas.
│   └── game.py                 # Game schemas.
├── logic/                      # Game logic for supported game types.
│   └── maumau.py               # Mau Mau card game logic.
├── utilities.py                # Helper functions for game logic and WebSocket management.
├── database.py                 # Database connection using SQLAlchemy.
├── dependencies.py             # Shared dependencies for routes.
├── requirements.txt            # Python dependencies.
├── Dockerfile                  # Dockerfile for building the backend image.
├── docker-compose.yml          # Docker Compose configuration for production.
├── docker-compose.override.yml # Docker Compose override for local development.
├── .github/workflows/ci.yml    # CI workflow for Docker image building.
├── .gitignore                  # Files and folders to ignore.
└── README.md                   # Documentation (this file).
```

---

## Development Notes

- **Database Initialization**:
  Database tables are automatically created at application startup using the SQLAlchemy models.

- **Error Handling**:
  Custom exception handlers are included for common errors like `KeyError`, `ValueError`, and `IntegrityError`.
