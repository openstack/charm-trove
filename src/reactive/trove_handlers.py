# Copyright 2016 TransCirrus Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# this is just for the reactive handlers and calls into the charm.
from __future__ import absolute_import

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

# This charm's library contains all of the handler code associated with trove
import charm.openstack.trove as trove


# use a synthetic state to ensure that it get it to be installed independent of
# the install hook.
@reactive.when_not('charm.installed')
def install_packages():
    trove.install()
    reactive.set_state('charm.installed')


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username=hookenv.config('rabbit-user'),
                        vhost=hookenv.config('rabbit-vhost'))
    trove.assess_status()


@reactive.when('shared-db.connected')
def setup_database(database):
    """On receiving database credentials, configure the database on the
    interface.
    """
    database.configure(hookenv.config('database'),
                       hookenv.config('database-user'),
                       hookenv.unit_private_ip())
    trove.assess_status()

#This is for the HA cluster DB for the HA requeroment. I think we need to use this and not shared-db
#@reactive.when('cluster.available')

#this is to check if ha is running
#@reactive.when('ha.connected')

@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    trove.setup_endpoint(keystone)
    trove.assess_status()


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_stuff(*args):
    """Render the configuration for Barbican when all the interfaces are
    available.

    Note that the HSM interface is optional (hence the @when_any) and thus is
    only used if it is available.
    """
    # Get the optional hsm relation, if it is available for rendering.
    trove.render_configs(args)
    trove.assess_status()


@reactive.when('config.changed')
def config_changed():
    """When the configuration changes, assess the unit's status to update any
    juju state required"""
    trove.assess_status()


@reactive.when('identity-service.available')
def configure_ssl(keystone):
    """Configure SSL access to Barbican if requested"""
    trove.configure_ssl(keystone)


#when cloud-compute.available

#when image-service.available

#when cinder - I need to find out what juju calls this

#when heat - I need to find out what juju calls this

#when ceph.available
