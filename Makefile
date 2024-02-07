SHELL=/bin/bash

makefile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
makefile_dir := $(dir $(mkfile_path))

help: ## show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%s\033[0m|%s\n", $$1, $$2}' \
	| column -t -s '|'


install-requirements:
	pip install -r src/aoai-simulated-api/requirements.txt
	pip install -r src/test-client/requirements.txt

erase-cassettes:
	rm -rf src/aoai-simulated-api/.cassettes

run-simulated-api:
	set -a && \
	[ -f .env ] && echo "sourcing .env values" && source .env || echo "No .env file found, using shell env vars" && \
	set +a && \
	cd src/aoai-simulated-api && \
	uvicorn main:app --reload --port 8000


run-test-client:
	set -a && \
	source .env && \
	set +a && \
	cd src/test-client && \
	python app.py

run-test-client-simulator:
	set -a && \
	source .env && \
	set +a && \
	cd src/test-client && \
	AZURE_OPENAI_ENDPOINT=http://localhost:8000 python app.py


docker-build-simulated-api:
	# TODO should set a tag!
	cd src/aoai-simulated-api && \
	docker build -t aoai-simulated-api .

docker-run-simulated-api:
	set -a && \
	[ -f .env ] && echo "sourcing .env values" && source .env || echo "No .env file found, using shell env vars" && \
	set +a && \
	docker run --rm \
		-p 8000:8000 \
		-v /mnt/cassettes:"${makefile_dir}/src/aoai-simulated-api/.cassettes" \
		-e CASSETTE_DIR=/mnt/cassettes \
		-e SIMULATOR_MODE \
		-e AZURE_OPENAI_ENDPOINT \
		-e AZURE_OPENAI_KEY \
		-e AZURE_OPENAI_DEPLOYMENT \
		aoai-simulated-api