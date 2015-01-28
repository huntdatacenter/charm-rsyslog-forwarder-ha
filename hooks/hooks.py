#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Jorge Niedbalski R. <jorge.niedbalski@canonical.com>'

import os
import sys

from shutil import copyfile

_HERE = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(_HERE, 'charmhelpers'))

from charmhelpers.core.host import (
    service_start,
    service_stop,
    service_restart,
)

from charmhelpers.core.hookenv import (
    Hooks,
    relation_id,
    config as config_get,
    log as juju_log,
    remote_unit,
    relation_get,
)

from charmhelpers.fetch import (
    apt_install
)

try:
    import sqlalchemy
except ImportError:
    try:
        apt_install("python-sqlalchemy")
    except:
        pass

from model import Server, session
from utils import get_template_dir, get_template
from utils import __die as die

required_packages = [
    'rsyslog',
    'rsyslog-relp',
    'python-jinja2',
    'python-sqlalchemy'
]


LOGS_TEMPLATE = 'keep_local.template'
LOGS_SYSTEM_FILE = '/etc/rsyslog.d/81-local.conf'
REPLICATION_FILE = '/etc/rsyslog.d/80-rsyslog-replication.conf'


hooks = Hooks()


def update_local_logs(keep=True):
    if keep:
        copyfile(
            os.path.join(get_template_dir(), LOGS_TEMPLATE),
            LOGS_SYSTEM_FILE)
    else:
        if os.path.exists(LOGS_SYSTEM_FILE):
            os.remove(LOGS_SYSTEM_FILE)


def update_failover_replication(servers):
    """
    Set the configuration file to failover
    """
    def _master_selection(servers):
        return servers[0], servers[1:]

    master, slaves = _master_selection(servers)
    with open(REPLICATION_FILE, 'w') as fd:
        fd.write(get_template('failover').render(
            **{
                'protocol': config_get('protocol'),
                'master': master,
                'slaves': slaves,
            }))


def update_fanout_replication(servers):
    """
    Set the configuration file to fanout replication
    """
    with open(REPLICATION_FILE, 'w') as fd:
        fd.write(get_template('fanout').render(
            **{
                'protocol': config_get('protocol'),
                'servers': servers,
            }))


def update_replication():
    servers = session.query(Server).all()

    if not len(servers):
        juju_log("Ready for add rsyslog relations to this forwarder")
        sys.exit(0)

    mode = config_get('replication-mode')

    if mode not in ('fanout', 'failover', ):
        die("Invalid provided replication mode: %s" % mode)

    if mode == 'failover':
        if not len(servers) >= 2:
            juju_log(
                "Cannot use failover replication without a secondary server,"
                " switching to fanout")
            update_fanout_replication(servers)
        else:
            update_failover_replication(servers)
    else:
        update_fanout_replication(servers)

    service_restart("rsyslog")


@hooks.hook()
def start():
    service_start("rsyslog")


@hooks.hook()
def stop():
    service_stop("rsyslog")


@hooks.hook()
def install():
    for package in required_packages:
        apt_install(package, fatal=True)

    update_local_logs(
        keep=config_get('log-locally'))


@hooks.hook()
def syslog_relation_joined():
    try:
        relation = relation_id()
    except Exception as ex:
        die("Cannot get syslog relation id: %s" % ex.message)

    if Server.has_relation(relation):
        die("Relation %s already exists" % relation)

    server = Server(relation_id=relation,
                    remote_unit=remote_unit(),
                    private_address=relation_get('private-address'))
    try:
        session.add(server)
        session.commit()
    except Exception:
        session.rollback()
        die("Cannot create server relation")

    update_replication()


@hooks.hook()
def syslog_relation_departed():
    Server.remove(relation_id())
    update_replication()


@hooks.hook()
def syslog_relation_broken():
    Server.remove(relation_id())
    update_replication()


@hooks.hook()
def upgrade_charm():
    install()


@hooks.hook()
def config_changed():
    update_local_logs(config_get("log-locally"))
    update_replication()


if __name__ == "__main__":
    hooks.execute(sys.argv)
