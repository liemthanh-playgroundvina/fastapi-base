# .ENV
setup-env:
	@touch .env
	@sed -i '/^NAME=/d' .env
	@sed -i '/^ENV=/d' .env
	@temp_file=$$(mktemp); \
	owner=$$(stat -c '%u' .env); \
	group=$$(stat -c '%g' .env); \
	echo "NAME=$(repo_name)" > $$temp_file; \
	echo "ENV=$(branch_name)" >> $$temp_file; \
	cat .env >> $$temp_file; \
	mv $$temp_file .env; \
	chmod 664 .env; \
	chown $$owner:$$group .env

load-env: setup-env
	$(eval NAME=$(shell grep -E '^NAME=' .env | cut -d '=' -f 2))
	$(eval ENV=$(shell grep -E '^ENV=' .env | cut -d '=' -f 2))
	$(eval DOCKER_HUB_URL=$(shell grep -E '^DOCKER_HUB_URL=' .env | cut -d '=' -f 2))

# Docker
build: load-env
	@docker build -t $(DOCKER_HUB_URL)/$(NAME)-app:$(ENV) -f docker/Dockerfile/app .
	@docker build -t $(DOCKER_HUB_URL)/$(NAME)-worker:$(ENV) -f docker/Dockerfile/worker .
	@docker build -t $(DOCKER_HUB_URL)/$(NAME)-llm:$(ENV) -f docker/Dockerfile/llm .

push: build
	@docker push $(DOCKER_HUB_URL)/$(NAME)-app:$(ENV)
	@docker push $(DOCKER_HUB_URL)/$(NAME)-worker:$(ENV)
	@docker push $(DOCKER_HUB_URL)/$(NAME)-llm:$(ENV)

pull: load-env
	@docker pull $(DOCKER_HUB_URL)/$(NAME)-app:$(ENV)
	@docker pull $(DOCKER_HUB_URL)/$(NAME)-worker:$(ENV)
	@docker pull $(DOCKER_HUB_URL)/$(NAME)-llm:$(ENV)

clean: load-env
	@docker rmi $(DOCKER_HUB_URL)/$(NAME)-app:$(ENV)
	@docker rmi $(DOCKER_HUB_URL)/$(NAME)-worker:$(ENV)
	@docker rmi $(DOCKER_HUB_URL)/$(NAME)-llm:$(ENV)

# Run
stop: load-env
	@cp -f .env docker/$(ENV)/.env
	@docker compose -f docker/$(ENV)/docker-compose.yml -p $(NAME)-$(ENV) down
	@docker compose -f docker/$(ENV)/docker-compose.worker.yml -p $(NAME)-$(ENV) down
	@docker compose -f docker/$(ENV)/docker-compose.services.yml -p $(NAME)-$(ENV) down

start: stop
	@docker compose -f docker/$(ENV)/docker-compose.yml -p $(NAME)-$(ENV) up -d
	@docker compose -f docker/$(ENV)/docker-compose.worker.yml -p $(NAME)-$(ENV) up -d
	@docker compose -f docker/$(ENV)/docker-compose.services.yml -p $(NAME)-$(ENV) up -d

deploy: pull start