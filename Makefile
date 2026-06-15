# =============================================================================
#  Atajos de gestión — Blog Tecnológico
#  Uso: make <target>
# =============================================================================
COMPOSE = docker compose
EXEC_WEB = $(COMPOSE) exec web

.DEFAULT_GOAL := help
.PHONY: help build up down restart logs ps shell dbshell migrate makemigrations \
        superuser collectstatic css css-watch test lint check restart-web

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

build: ## Construye las imágenes
	$(COMPOSE) build

up: ## Levanta todos los servicios en segundo plano
	$(COMPOSE) up -d

down: ## Detiene y elimina los contenedores
	$(COMPOSE) down

restart: ## Reinicia todos los servicios
	$(COMPOSE) restart

restart-web: ## Reinicia solo el servicio web
	$(COMPOSE) restart web

logs: ## Sigue los logs (make logs s=web)
	$(COMPOSE) logs -f $(s)

ps: ## Lista el estado de los servicios
	$(COMPOSE) ps

shell: ## Abre un shell de Django (shell_plus si está disponible)
	$(EXEC_WEB) python manage.py shell

dbshell: ## Abre psql en la base de datos
	$(EXEC_WEB) python manage.py dbshell

migrate: ## Aplica migraciones
	$(EXEC_WEB) python manage.py migrate

makemigrations: ## Genera migraciones
	$(EXEC_WEB) python manage.py makemigrations

superuser: ## Crea un superusuario interactivo
	$(EXEC_WEB) python manage.py createsuperuser

collectstatic: ## Recolecta estáticos
	$(EXEC_WEB) python manage.py collectstatic --noinput

css: ## Compila Tailwind una vez en el host (producción, minificado)
	cd tailwind && npm run build:local

css-watch: ## Compila Tailwind en modo watch (desarrollo)
	cd tailwind && npm run watch

test: ## Ejecuta la suite de tests
	$(EXEC_WEB) python manage.py test

check: ## Ejecuta los checks de Django (incluye --deploy)
	$(EXEC_WEB) python manage.py check --deploy
