# General

This Charm provides support for adding a [rsyslog](http://www.rsyslog.org) forwarder listener to any service.
In addition, this charm allows to have multiple rsyslog aggregators servers using two different replication
modes ( fanout, failover ).

By default the 'fanout' replication mode is going to be used, which means that all the
syslog messages will be forwarder to all aggregator servers.

Failover mode will forward all the syslog messages to the primary rsyslog server and
in case of failure will use the secondary rsyslog server.

In you want to choose to failover mode, this will require that your current
rsyslog server is binded to TCP port 514.

The charm can also optionally watch log files from apps which don't use syslog and forward those
log entries also. By default it will watch apt and dpkg log files.

# Usage method

This is a subordinate charm, which means it requires to have a service to hook in. On this
example we are going to deploy mysql

    juju deploy mysql

Then you must deploy this charm

    juju deploy rsyslog-forwarder-ha

Once your service is running, you can relate this charm:

    juju add-relation rsyslog-forwarder-ha mysql

Then you can deploy your rsyslog aggregators servers:

    juju deploy rsyslog primary
    juju deploy rsyslog secondary

Once your rsyslog aggregators are ready, you can relate them with your forwarder.

    juju add-relation rsyslog-forwarder-ha primary
    juju add-relation rsyslog-forwarder-ha secondary


Once you have your rsyslog ports opened. You can change the replication-mode variable
on your rsyslog-forwarder-ha charm.

    juju set rsyslog-forwarder-ha replication-mode="failover"

# Contact Information

    Mantainer: rsyslog-charmers@lists.launchpad.net
    Bugs: https://bugs.launchpad.net/rsyslog-charm
