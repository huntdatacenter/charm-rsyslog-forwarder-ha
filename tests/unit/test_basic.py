#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Jorge Niedbalski R. <jorge.niedbalski@canonical.com>'

import os

_HERE = os.path.abspath(os.path.dirname(__file__))

try:
    import unittest
    import mock
except ImportError as ex:
    raise ImportError("Please install unittest and mock modules")


from hooks import hooks


TO_PATCH = [
    "apt_install",
    "install",
    "session",
    "die",
    "relation_id",
    "relation_get",
    "service_restart",
    "remote_unit",
    "service_start",
    "service_restart",
    "juju_log",
    "Server",
    "update_local_logs",
    "config_get",
    "get_template_dir",
    "sys",
    "update_imfile",
]


class HooksTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.patch_all()

        self.juju_log.return_value = True
        self.apt_install.return_value = True
        self.update_local_logs.return_value = True
        self.update_imfile.return_value = True
        self.get_template_dir.return_value = True

    def patch(self, method):
        _m = mock.patch.object(hooks, method)
        _mock = _m.start()
        self.addCleanup(_m.stop)
        return _mock

    def patch_all(self):
        for method in TO_PATCH:
            setattr(self, method, self.patch(method))

    def test_install_hook(self):
        """Check if install hooks is correctly executed
        """
        hooks.hooks.execute(['install'])

        expected = [
            mock.call("rsyslog", fatal=True),
            mock.call("rsyslog-relp", fatal=True),
            mock.call("python-jinja2", fatal=True),
            mock.call("python-sqlalchemy", fatal=True),
            mock.call("rsyslog-gnutls", fatal=True),
        ]

        self.assertEquals(sorted(self.apt_install.call_args_list),
                          sorted(expected))

    def test_upgrade_charm(self):
        """Check if charm upgrade hooks is correctly executed
        """
        hooks.hooks.execute(['upgrade-charm'])
        self.install.assert_called_once()

    def test_start_charm(self):
        """Check if start hook is correctly executed
        """
        hooks.hooks.execute(['start'])
        self.service_start.assert_called_with("rsyslog")

    def test_stop_charm(self):
        """Check if rsyslog is returned to default config and restart executed
        """
        hooks.hooks.execute(['stop'])
        self.service_restart.assert_called_with("rsyslog")

    @mock.patch("hooks.hooks.update_replication")
    def test_syslog_relation_joined(self, replication):
        """Check if syslog_relation_joined works"""

        self.relation_id.return_value = 0
        self.Server.has_relation.return_value = False

        hooks.hooks.execute(["syslog-relation-joined"])

        self.Server.has_relation.assert_called_once()
        replication.assert_called_once()

        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

    @mock.patch("hooks.hooks.update_replication")
    def test_syslog_relation_departed(self, replication):
        """check if syslog_relation_departed works"""
        self.relation_id.return_value = 0

        self.Server.remove.assert_called_once()
        replication.assert_called_once()

    @mock.patch("hooks.hooks.update_replication")
    def test_syslog_relation_broken(self, replication):
        """check if syslog_relation_broken works"""
        self.relation_id.return_value = 0

        self.Server.remove.assert_called_once()
        replication.assert_called_once()

    @mock.patch("hooks.hooks.update_replication")
    def test_config_changed(self, replication):
        """check if config_changed hook works"""
        self.update_local_logs.assert_called_once()
        self.update_imfile.assert_called_once()
        replication.assert_called_once()

    @mock.patch("hooks.hooks.update_failover_replication")
    @mock.patch("hooks.hooks.update_fanout_replication")
    def test_update_replication_no_servers(self, failover, fanout):
        """check if update_replication works with no servers given"""
        class DummyServer(object):
            @classmethod
            def all(self, *args, **kwargs):
                return []

        self.session.query.return_value = DummyServer()

        hooks.update_replication()

        self.juju_log.assert_called_once()
        self.sys.exit.assert_called_once()
        self.service_restart.assert_called_once_with("rsyslog")

    @mock.patch("hooks.hooks.update_failover_replication")
    @mock.patch("hooks.hooks.update_fanout_replication")
    def test_update_replication_failover(self, fanout, failover):
        """check if update_replication works with 2 servers in failover
        replication mode"""

        class DummyServer(object):
            @classmethod
            def all(self, *args, **kwargs):
                return [{}, {}]

        self.session.query.return_value = DummyServer()
        self.config_get.return_value = 'failover'

        hooks.update_replication()
        failover.assert_called_once()

        self.service_restart.assert_called_once_with("rsyslog")

    @mock.patch("hooks.hooks.update_failover_replication")
    @mock.patch("hooks.hooks.update_fanout_replication")
    def test_update_replication_fanout(self, fanout, failover):
        """check if update_replication works with fanout replication mode"""

        class DummyServer(object):
            @classmethod
            def all(self, *args, **kwargs):
                return [{}, {}]

        self.session.query.return_value = DummyServer()
        self.config_get.return_value = 'fanout'

        hooks.update_replication()
        fanout.assert_called_once()

        self.service_restart.assert_called_once_with("rsyslog")
