.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: venvcheck ## Check if venv is active
venvcheck:
ifeq ("$(VIRTUAL_ENV)","")
	@echo "Venv is not activated!"
	@echo "Activate venv first."
	@echo
	exit 1
endif

.PHONY: run_redis         ## Run the local redis messenger
run_redis: venvcheck
	docker-compose up -d

.PHONY: run_workers		  ## Spawn the workers
run_workers: venvcheck
	gnome-terminal --tab -- bash -ic "celery -A calc worker -Q default --loglevel=INFO --concurrency=1 "
	gnome-terminal --tab -- bash -ic "celery -A calc worker -Q q1 --loglevel=INFO --concurrency=1"
