# Overview

This charm provides the Trove (DBaaS) for an OpenStack Cloud.


# Usage

As described in the installation guide,

http://docs.openstack.org/developer/trove/dev/manual_install.html

a running OpenStack environment is required to use Trove, including
the following components:

    - Compute (Nova)
    - Image Service (Glance)
    - Identity (Keystone)
    - Neutron or Nova-Network
    - Cinder, if you want to provision datastores on block-storage volumes
    - Swift, if you want to do backup/restore and replication
    - AMQP service (RabbitMQ or QPID)
    - MySQL (SQLite, PostgreSQL) database for Trove's internal needs
    - Certain OpenStack services must be accessible from VMs:
        - Swift

OpenStack services must be accessible directly from the environment where
Trove is deployed:
        - Nova
        - Cinder
        - Swift
        - Heat


A basic setup with using charms would look like the following:

    juju deploy trove
    juju deploy mysql
    juju deploy rabbitmq-server
    juju deploy keystone
    juju deploy cinder
    juju deploy glance
    juju deploy nova-compute
    juju deploy nova-cloud-controller
    juju deploy neutron
    juju deploy neutron-openvswitch
    juju deploy neutron-gateway

    juju add-relation trove mysql
    juju add-relation trove rabbitmq-server
    juju add-relation trove keystone

    juju add-relation nova-compute rabbitmq-server
    juju add-relation nova-compute glance

    juju add-relation cinder keystone
    juju add-relation cinder mysql
    juju add-relation cinder rabbitmq-server

    juju add-relation glance keystone
    juju add-relation glance mysql

    juju add-relation neutron-gateway mysql
    juju add-relation neutron-gateway rabbitmq-server
    juju add-relation neutron-gateway:amqp rabbitmq-server:amqp
    juju add-relation neutron-openvswitch nova-compute
    juju add-relation neutron-openvswitch neutron-api
    juju add-relation neutron-openvswitch rabbitmq-server
    juju add-relation neutron-api mysql
    juju add-relation neutron-api keystone
    juju add-relation neutron-api rabbitmq-server

    juju add-relation nova-cloud-controller keystone
    juju add-relation nova-cloud-controller rabbitmq-server
    juju add-relation nova-cloud-controller nova-compute
    juju add-relation nova-cloud-controller mysql
    juju add-relation nova-cloud-controller glance
    juju add-relation nova-cloud-controller cinder
    juju add-relation nova-cloud-controller neutron-api

This will get the necessary services deployed, however, you will still need
to create images, flavors and data stores for your specific needs.

http://docs.openstack.org/admin-guide/database.html

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/charm-trove/+filebug).

For general questions please refer to the OpenStack [Charm Guide](http://docs.openstack.org/developer/charm-guide/).
