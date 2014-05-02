#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Jorge Niedbalski R. <jorge.niedbalski@canonical.com>'

import os
import sys

from shutil import copyfile

_HERE = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(_HERE, 'charmhelpers'))

from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers import fetch

from model import Server, session
from utils import get_template_dir, get_template, __die

required_packages = [
    'rsyslog',
    'python-jinja2',
    'python-sqlalchemy'
]


LOGS_TEMPLATE = 'keep_local.template'
LOGS_SYSTEM_FILE = '/etc/rsyslog.d/81-local.conf'
REPLICATION_FILE = '/etc/rsyslog.d/80-rsyslog-replication.conf'


hooks = hookenv.Hooks()


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
                'master': master,
                'slaves': slaves
            }))


def update_fanout_replication(servers):
    """
    Set the configuration file to fanout replication
    """
    with open(REPLICATION_FILE, 'w') as fd:
        fd.write(get_template('fanout').render(
            **{
                'servers': servers
            }))


def update_replication():
    servers = session.query(Server).all()

    if not len(servers):
        hookenv.log("Ready for add rsyslog relations to this forwarder")
        sys.exit(0)

    mode = hookenv.config('replication-mode')

    if mode not in ('fanout', 'failover', ):
        __die("Invalid provided replication mode: %s" % mode)

    if mode == 'failover':
        if not len(servers) >= 2:
            hookenv.log(
                "Cannot use failover replication without a secondary server,"
                " switching to fanout")
            update_fanout_replication(servers)
        else:
            update_failover_replication(servers)
    else:
        update_fanout_replication(servers)

    host.service_restart("rsyslog")


@hooks.hook()
def start():
    host.service_start("rsyslog")


@hooks.hook()
def stop():
    host.service_stop("rsyslog")


@hooks.hook()
def install():
    for package in required_packages:
        fetch.apt_install(package, fatal=True)

    update_local_logs(
        keep=hookenv.config('log-locally'))


@hooks.hook()
def syslog_relation_joined():
    relation_id = hookenv.relation_id()

    if Server.has_relation(relation_id):
        __die("Relation %s already exists" % relation_id)

    server = Server(relation_id=relation_id,
                    remote_unit=hookenv.remote_unit(),
                    private_address=hookenv.relation_get('private-address'))
    try:
        session.add(server)
        session.commit()
    except Exception:
        session.rollback()
        __die("Cannot create server relation")

    update_replication()


@hooks.hook()
def syslog_relation_departed():
    Server.remove(hookenv.relation_id())
    update_replication()


@hooks.hook()
def syslog_relation_broken():
    Server.remove(hookenv.relation_id())
    update_replication()


@hooks.hook()
def config_changed():
    update_local_logs(hookenv.config("log-locally"))
    update_replication()


if __name__ == "__main__":
    hooks.execute(sys.argv)
