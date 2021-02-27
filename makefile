.PHONY: all
all: run_rabbit run_app

.PHONY: help
help:
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

.PHONY: venvcheck ## Check if venv is active
venvcheck:
ifeq ("$(VIRTUAL_ENV)","")
	@echo "Venv is not activated!"
	@echo "Activate venv first."
	@echo
	exit 1
endif

.PHONY: run_rabbit         ## Run the local redis messenger
run_rabbit: venvcheck
	@docker-compose down
	@docker-compose up -d

.PHONY: run_app		  ## Spawn the workers and the tasks
run_app: venvcheck
	@chmod +x run.sh
	@./run.sh
