BACKEND_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(abspath $(BACKEND_DIR)/..)

build-DivingAPI:
	cp -r $(PROJECT_ROOT)/frontend $(ARTIFACTS_DIR)/frontend
	cp $(BACKEND_DIR)*.py $(ARTIFACTS_DIR)/
	pip install -r $(BACKEND_DIR)requirements.txt -t $(ARTIFACTS_DIR)/ --upgrade
