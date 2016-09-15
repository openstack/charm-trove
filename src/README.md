# Overview

This charm provides the Trove (DBaaS) for an OpenStack Cloud.


# Usage

Designate relies on services from the mysql, rabbitmq-server and keystone
charms:

    juju deploy trove
    juju deploy mysql
    juju deploy rabbitmq-server
    juju deploy keystone
    juju deploy heat
    juju deploy cinder
    juju add-relation trove mysql
    juju add-relation trove rabbitmq-server
    juju add-relation trove keystone

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/charm-designate/+filebug).

For general questions please refer to the OpenStack [Charm Guide](http://docs.openstack.org/developer/charm-guide/).
