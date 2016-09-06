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


import charmhelpers.core.hookenv as hookenv
import charms.reactive as reactive
import charms_openstack.charm as openstack_charm

import charm.openstack.trove as trove


COMPLETE_INTERFACE_STATES = [
    'shared-db.available',
    'identity-service.available',
    'amqp.available',
]


# wire in defaults for various interfaces and default states
openstack_charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'shared-db.connected',
    'identity-service.connected',
    'identity-service.available',  # Enables the SSL handler
    'config.changed',
    'update-status')


@reactive.when_not('base-config.rendered')
@reactive.when(*COMPLETE_INTERFACE_STATES)
@openstack_charm.optional_interface('cluster.available')
@openstack_charm.provide_charm_instance
def configure_designate_basic(designate_charm, *args):
    """Configure the minimum to boostrap designate"""
    designate_charm.render_base_config(args)
    reactive.set_state('base-config.rendered')


@reactive.when_not('db.synched')
@reactive.when('base-config.rendered')
@reactive.when(*COMPLETE_INTERFACE_STATES)
@openstack_charm.provide_charm_instance
def run_db_migration(*args):
    """Run database migrations"""
    designate.db_sync()
    if designate.db_sync_done():
        reactive.set_state('db.synched')


@reactive.when('cluster.available')
@openstack_charm.provide_charm_instance
def update_peers(designate_charm, cluster):
    """Inform designate peers about this unit"""
    designate_charm.update_peers(cluster)


@reactive.when('db.synched')
@reactive.when(*COMPLETE_INTERFACE_STATES)
@openstack_charm.optional_interface('cluster.available')
@openstack_charm.provide_charm_instance
def configure_designate_full(designate_charm, *args):
    """Write out all designate config include bootstrap domain info"""
    designate_charm.configure_ssl()
    designate_charm.render_full_config(args)
    designate_charm.create_initial_servers_and_domains()
    designate.render_sink_configs(args)  # Not on the charm class!
    designate_charm.render_rndc_keys()
    designate_charm.update_pools()


@reactive.when('ha.connected')
@openstack_charm.provide_charm_instance
def cluster_connected(designate_charm, hacluster):
    """Configure HA resources in corosync"""
    designate_charm.configure_ha_resources(hacluster)
    designate_charm.assess_status()