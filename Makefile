#!/usr/bin/make
PYTHON := /usr/bin/env python

.PHONY: build
build: sync-charm-helpers lint

.PHONY: clean
clean:
	@rm -rf .tox

.PHONY: apt_prereqs
apt_prereqs:
	@# Need tox, but don't install the apt version unless we have to (don't want to conflict with pip)
	@which tox >/dev/null || (sudo apt-get install -y python-pip && sudo pip install tox)

.PHONY: lint
lint: apt_prereqs
	@tox --notest
	@PATH=.tox/py34/bin:.tox/py35/bin flake8 --exclude hooks/charmhelpers hooks
	@charm proof

.PHONY: test
test: apt_prereqs
	@tox

bin/charm_helpers_sync.py:
	@bzr cat lp:charm-helpers/tools/charm_helpers_sync/charm_helpers_sync.py > bin/charm_helpers_sync.py

sync-charm-helpers: bin/charm_helpers_sync.py
	@$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml

.PHONY: deploy
deploy:
	@echo Deploying rsyslog-forwarder-ha
	@juju deploy .
	@echo See the README for explorations after deploying.
