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
	@mkdir -p bin
	@curl -o bin/charm_helpers_sync.py https://raw.githubusercontent.com/juju/charm-helpers/master/tools/charm_helpers_sync/charm_helpers_sync.py

sync: bin/charm_helpers_sync.py
	@$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml
