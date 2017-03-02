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
import charms_openstack.charm as charm

# This charm's library contains all of the handler code associated with trove
import charm.openstack.trove as trove

charm.use_defaults(
    'config.changed',
    'amqp.connected',
    'identity-service.available',
    'charm.installed',
    'upgrade-charm',
    'update-status',
    'shared-db.connected',
)


# this is to check if ha is running
@reactive.when('ha.connected')
def cluster_connected(hacluster):
    trove.configure_ha_resources(hacluster)


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    trove.setup_endpoint(keystone)
    trove.assess_status()


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_stuff(*args):
    # Get the optional hsm relation, if it is available for rendering.
    trove.render_configs(args)
    reactive.set_state('config.complete')
    trove.assess_status()


@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    trove.db_sync()
    trove.restart_all()
    reactive.set_state('db.synced')
    trove.assess_status()


@reactive.when('cluster.available')
def update_peers(cluster):
    """Inform designate peers about this unit"""
    trove.update_peers(cluster)
