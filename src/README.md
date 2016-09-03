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
    juju deploy nova-cloud-controller
    juju deploy nova-compute
    juju deploy cinder
    juju deploy swift-proxy
    juju add-relation trove mysql
    juju add-relation trove rabbitmq-server
    juju add-relation trove keystone

To add support for auto-generated records when guests are booted the charm 
needs a relation with nova-compute:

    juju deploy nova-compute
    juju add-relation trove nova-compute

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/charm-designate/+filebug).

For general questions please refer to the OpenStack [Charm Guide](http://docs.openstack.org/developer/charm-guide/).
