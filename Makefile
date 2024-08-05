# Use one shell for all commands in a target recipe
.ONESHELL:
# Commands
.PHONY: help build name list launch mount umount bootstrap up down ssh destroy lint upgrade force-upgrade recreate-default-model node_exporter node_exporter-amd64 node_exporter-arm64
# Set default goal
.DEFAULT_GOAL := help
# Use bash shell in Make instead of sh
SHELL := /bin/bash
# Charm variables
CHARM_NAME := rsyslog-forwarder-ha
CHARM_BUILD := $(CHARM_NAME)_amd64.charm
CHARM_BUILD_AMD64 := $(CHARM_NAME)_amd64.charm
CHARM_BUILD_ARM64 := $(CHARM_NAME)_arm64.charm
CHARMHUB_NAME := huntdatacenter-$(CHARM_NAME)
CHARM_STORE_URL := cs:~huntdatacenter/$(CHARM_NAME)
CHARM_HOMEPAGE := https://github.com/huntdatacenter/$(CHARM_NAME)/
CHARM_BUGS_URL := https://github.com/huntdatacenter/$(CHARM_NAME)/issues

UBUNTU_VERSION = noble
MOUNT_TARGET = /home/ubuntu/vagrant
DIR_NAME = "$(shell basename $(shell pwd))"
VM_NAME = juju-dev--$(DIR_NAME)

name:  ## Print name of the VM
	echo "$(VM_NAME)"

list:  ## List existing VMs
	multipass list

launch:
	multipass launch $(UBUNTU_VERSION) -v --timeout 3600 --name $(VM_NAME) --memory 4G --cpus 4 --disk 20G --cloud-init juju.yaml \
	&& multipass exec $(VM_NAME) -- cloud-init status

# MacOS: Assure allowed in System settings > Privacy > Full disk access for multipassd
mount:
	multipass mount --type 'classic' --uid-map $(shell id -u):1000 --gid-map $(shell id -g):1000 $(PWD) $(VM_NAME):$(MOUNT_TARGET)

umount:
	multipass umount $(VM_NAME):$(MOUNT_TARGET)

recreate-default-model:
	juju destroy-model --no-prompt default --destroy-storage --force
	@sleep 2
	juju add-model default --config enable-os-upgrade=false

bootstrap:
	multipass exec -d $(MOUNT_TARGET) $(VM_NAME) -- bash --login bin/tmux.sh

# bootstrap:
# 	$(eval ARCH := $(shell multipass exec $(VM_NAME) -- dpkg --print-architecture))
# 	multipass exec $(VM_NAME) -- juju bootstrap localhost lxd --bootstrap-constraints arch=$(ARCH) \
# 	&& multipass exec $(VM_NAME) -- juju add-model default --config enable-os-upgrade=false

up: launch mount bootstrap ssh  ## Start a VM

down:  ## Stop the VM
	multipass down $(VM_NAME)

ssh:  ## Connect into the VM
	multipass exec -d $(MOUNT_TARGET) $(VM_NAME) -- bash

destroy:  ## Destroy the VM
	multipass delete -v --purge $(VM_NAME)

login:
	@bash -c "test -s ~/.charmcraft-auth || charmcraft login --export ~/.charmcraft-auth"

release: ## Release charm:
release: ##    make channel=latest/stable arch=amd64 release
release: ##    make channel=latest/edge arch=arm64 release
	@echo "# -- Releasing charm: https://charmhub.io/$(CHARMHUB_NAME)"
	$(eval CHARMCRAFT_AUTH := $(shell cat ~/.charmcraft-auth))
	charmcraft upload --name $(CHARMHUB_NAME) --release $(channel) $(CHARM_NAME)_$(arch).charm


lint: ## Run linter
	tox -e lint

remove-builds:
	rm -vf $(CHARM_BUILD) $(CHARM_BUILD_AMD64) $(CHARM_BUILD_ARM64)

clean: remove-builds  ## Remove build cache and artifacts
	charmcraft clean --verbose

$(CHARM_BUILD):
	charmcraft pack --verbose

build: remove-builds $(CHARM_BUILD)  ## Build charm

clean-build: clean build  ## Build charm from scratch

deploy: ## Deploy charm
	juju deploy ./$(CHARM_BUILD_AMD64)

upgrade: ## Upgrade charm
	juju upgrade-charm $(CHARM_NAME) --path ./$(CHARM_BUILD_AMD64)

force-upgrade: ## Force upgrade charm
	juju upgrade-charm $(CHARM_NAME) --path ./$(CHARM_BUILD_AMD64) --force-units


deploy-focal-bundle: ## Deploy Focal test bundle
	juju deploy ./tests/bundles/focal.yaml

deploy-jammy-bundle: ## Deploy Jammy test bundle
	juju deploy ./tests/bundles/jammy.yaml

deploy-noble-bundle: ## Deploy Noble test bundle
	juju deploy ./tests/bundles/noble.yaml


# Internal targets
clean-repo:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo '!!! Hard resetting repo and removing untracked files !!!'; \
		git reset --hard; \
		git clean -fdx; \
	fi


# Display target comments in 'make help'
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {sub("\\\\n",sprintf("\n%22c"," "), $$2);printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
