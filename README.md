# Fastapi Base
- CRUD Fastapi - Postgres - Alembic - Worker NVIDIA - Redis - RabbitMQ - Services - Nginx
- Services (LLM - EmbeddingModel - VectorDB)

# Requirements:
- docker 
- Nvidia GPU (testing in 3090ti)
- App port: 8888 


# LLM
- config host llm: static/files/app/chatbot.json
- config local llm: static/files/llm/config.json

# Run
git clone https://github.com/liemthanh-playgroundvina/fastapi-base.git ai-gpt-services
cd ai-gpt-services
make build repo_name=ai-gpt-services branch_name=dev
make start repo_name=ai-gpt-services branch_name=dev