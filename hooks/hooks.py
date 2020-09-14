#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Implement hooks for rsyslog-forwarder-ha charm."""

import base64
import os
import subprocess
import sys
from shutil import copyfile

_HERE = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(_HERE, "charmhelpers"))

from charmhelpers.contrib.charmsupport import nrpe  # noqa:E402
from charmhelpers.core.hookenv import (  # noqa:E402
    Hooks,
    config as config_get,
    log as juju_log,
    relation_get,
    relation_id,
    remote_unit,
    status_set,
)
from charmhelpers.core.host import (  # noqa: E402
    service_restart,
    service_start,
)
from charmhelpers.fetch import apt_install  # noqa:E402

from model import Server, session  # noqa:E402
from utils import get_template_dir, get_template  # noqa:E402
from utils import __die as die  # noqa:E402


required_packages = [
    "rsyslog",
    "rsyslog-relp",
    "python3-jinja2",
    "python3-sqlalchemy",
    "rsyslog-gnutls",
]


IMFILE_FILE = "/etc/rsyslog.d/40-rsyslog-imfile.conf"
LOGS_TEMPLATE = "keep_local.template"
LOGS_SYSTEM_FILE = "/etc/rsyslog.d/50-default.conf"
REPLICATION_FILE = "/etc/rsyslog.d/45-rsyslog-replication.conf"
CERT_FILE = "/etc/rsyslog.d/42-cert-rsyslog.conf"

hooks = Hooks()


def update_certfile():
    # Check:
    # https://www.rsyslog.com/doc/master/tutorials/tls.html?highlight=defaultnetstreamdrivercafile
    if config_get("cert"):
        if len(config_get("cert")) > 0:
            subprocess.check_output(["mkdir", "-pv", "/etc/rsyslog.d/keys/ca.d"])
            encoded_cert = config_get("cert")
            cert = base64.b64decode(encoded_cert)
            with open("/etc/rsyslog.d/keys/ca.d/rsyslog.crt", "w") as c:
                c.write(cert)
                c.close()

    if not config_get("cert"):
        if os.path.exists(CERT_FILE):
            os.remove(CERT_FILE)
        return
    if len(config_get("cert")) == 0:
        if os.path.exists(CERT_FILE):
            os.remove(CERT_FILE)
        return

    with open(CERT_FILE, "w") as fd:
        fd.write(get_template("certificate").render())


def update_imfile(imfiles):
    if not imfiles:
        if os.path.exists(IMFILE_FILE):
            os.remove(IMFILE_FILE)
        return

    with open(IMFILE_FILE, "w") as fd:
        fd.write(get_template("imfile").render(imfiles=imfiles))


def update_local_logs(keep=True):
    if keep:
        copyfile(os.path.join(get_template_dir(), LOGS_TEMPLATE), LOGS_SYSTEM_FILE)
    else:
        if os.path.exists(LOGS_SYSTEM_FILE):
            os.remove(LOGS_SYSTEM_FILE)


@hooks.hook("nrpe-external-master-relation-changed")
@hooks.hook("local-monitors-relation-changed")
def update_nrpe_config():
    nrpe_compat = nrpe.NRPE()
    nrpe_compat.add_check(
        shortname="rsyslog",
        description="Check rsyslog is running",
        check_cmd="check_procs -c 1: -C rsyslogd",
    )
    nrpe_compat.write()


def update_failover_replication(servers):
    """Set the configuration file to failover."""

    def _master_selection(servers):
        return servers[0], servers[1:]

    master, slaves = _master_selection(servers)
    with open(REPLICATION_FILE, "w") as fd:
        fd.write(
            get_template("failover").render(
                **{
                    "protocol": config_get("protocol"),
                    "master": master,
                    "slaves": slaves,
                    "message_filter": config_get("message-filter"),
                }
            )
        )


def update_fanout_replication(servers):
    """Set the configuration file to fanout replication."""
    with open(REPLICATION_FILE, "w") as fd:
        fd.write(
            get_template("fanout").render(
                **{
                    "protocol": config_get("protocol"),
                    "servers": servers,
                    "message_filter": config_get("message-filter"),
                }
            )
        )


def update_replication():
    server_list = config_get("forward_hosts")
    servers = session.query(Server).all()
    for server in servers:
        if not server.port:
            server.port = "2514" if config_get("protocol") == "relp" else "514"

    if server_list:
        for server_pair in server_list.split(","):
            if len(server_pair.split("=")) != 2:
                juju_log(
                    "Wrong forward_hosts option, missing "
                    "hostname=address format, found: {}".format(server_pair)
                )
                continue
            server = Server()
            [server.remote_unit, uri] = server_pair.split("=")
            server.private_address = uri.split(":")[0]
            if len(uri.split(":")) > 1:
                server.port = uri.split(":")[1]
            else:
                if config_get("protocol") == "relp":
                    server.port = "2514"
                else:
                    server.port = "514"
            servers.append(server)

    if not len(servers):
        juju_log("Ready for add rsyslog relations to this forwarder")
        sys.exit(0)

    mode = config_get("replication-mode")

    if mode not in ["fanout", "failover"]:
        die("Invalid provided replication mode: %s" % mode)

    update_replication_by_mode(mode, servers)
    service_restart("rsyslog")


def update_replication_by_mode(mode, servers):
    if mode == "failover":
        if not len(servers) >= 2:
            juju_log(
                "Cannot use failover replication without a secondary server,"
                " switching to fanout"
            )
            update_fanout_replication(servers)
        else:
            update_failover_replication(servers)
    else:
        update_fanout_replication(servers)


@hooks.hook()
def start():
    service_start("rsyslog")


@hooks.hook()
def stop():
    # Remove any specific logfiles
    for conf_file in (IMFILE_FILE, REPLICATION_FILE):
        if os.path.exists(conf_file):
            os.remove(conf_file)

    # Unfortunately rsyslog reconfigure does not restore the default config
    # so just put ours in place
    update_local_logs(True)
    service_restart("rsyslog")


@hooks.hook()
def install():
    for package in required_packages:
        apt_install(package, fatal=True)

    update_certfile()
    update_local_logs(keep=config_get("log-locally"))


@hooks.hook()
def syslog_relation_joined():
    try:
        relation = relation_id()
    except Exception as ex:
        die("Cannot get syslog relation id: %s" % ex.message)

    if Server.has_relation(relation):
        # If multiple principal apps are colocated on a single machine,
        # log it and return. There is no need to reconfigure rsyslogd if it
        # has already been done by another principal application.
        # NB: if colocated principal apps are to be connected to *different*
        # rsyslog aggregators, we will have a problem since we are skipping
        # any rsyslogd configuration after the 1st syslog relation is joined.
        juju_log("Relation %s already exists" % relation)
        return

    server = Server(
        relation_id=relation,
        remote_unit=remote_unit(),
        private_address=relation_get("private-address"),
    )
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
    update_imfile(config_get("watch-files").split())
    update_certfile()
    update_replication()
    update_nrpe_config()
    status_set("active", "Unit is ready")


if __name__ == "__main__":
    if sys.argv[0].split("/")[-1] == "hooks.py":
        del sys.argv[0]
    hooks.execute(sys.argv)
