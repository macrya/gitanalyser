.PHONY: help build up down logs clean install migrate

help:
	@echo "GitHub Technical Debt Analyzer - Development Commands"
	@echo ""
	@echo "  make build       - Build Docker containers"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make clean       - Remove all containers and volumes"
	@echo "  make migrate     - Run database migrations"
	@echo "  make shell-be    - Open backend shell"
	@echo "  make shell-fe    - Open frontend shell"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	@echo "All containers and volumes removed"

migrate:
	docker-compose exec backend alembic upgrade head

shell-be:
	docker-compose exec backend /bin/bash

shell-fe:
	docker-compose exec frontend /bin/sh

install:
	@echo "Setting up GitHub Technical Debt Analyzer..."
	@cp .env.example .env || echo ".env already exists"
	@cp frontend/.env.example frontend/.env.local || echo "frontend/.env.local already exists"
	@echo "Please edit .env and frontend/.env.local with your configuration"
	@echo "Then run: make build && make up && make migrate"
