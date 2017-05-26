# Copyright 2016 TransCirrus Inc.
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
# The trove handlers class

# bare functions are provided to the reactive handlers to perform the functions
# needed on the class.
from __future__ import absolute_import

import collections

import charmhelpers.contrib.openstack.utils as ch_utils
import charmhelpers.core.unitdata as unitdata
import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip

TROVE_DIR = '/etc/trove/'
TROVE_CONF = TROVE_DIR + "trove.conf"
TROVE_API_PASTE_CONF = TROVE_DIR + "api-paste.ini"
TROVE_CONDUCTOR = TROVE_DIR + "trove-conductor.conf"
TROVE_GUEST_AGENT = TROVE_DIR + "trove-guestagent.conf"
TROVE_LOGGING_GUEST_AGENT = TROVE_DIR + "trove-logging-guestagent.conf"
TROVE_TASK_MANAGER = TROVE_DIR + "trove-taskmanager.conf"

OPENSTACK_RELEASE_KEY = 'trove-charm.openstack-release-version'


###
# Handler functions for events that are interesting to the Trove charms

# Copied from the Congress example charm
# https://github.com/openstack/charm-guide/blob/master/doc/source/new-charm.rst
def install():
    """Use the singleton from the TroveCharm to install the packages on the
    unit
    """
    TroveCharm.singleton.install()


def db_sync_done():
    """Use the singleton from the TroveCharm to check if db migration has
    been run

    @returns: str or None. Str if sync has been done otherwise None
    """
    return TroveCharm.singleton.db_sync_done()


def restart_all():
    """Use the singleton from the TroveCharm to restart services on the
    unit
    """
    TroveCharm.singleton.restart_all()


def db_sync():
    """Use the singleton from the TroveCharm to run db migration
    """
    TroveCharm.singleton.db_sync()


def configure_ha_resources(hacluster):
    """Use the singleton from the TroveCharm to run configure_ha_resources
    """
    TroveCharm.singleton.configure_ha_resources(hacluster)


def setup_endpoint(keystone):
    """When the keystone interface connects, register this unit in the keystone
    catalogue.

    :param keystone: instance of KeystoneRequires() class from i/f
    """
    charm = TroveCharm.singleton
    public_ep = '{}/v1.0/%(tenant_id)s'.format(charm.public_url)
    internal_ep = '{}/v1.0/%(tenant_id)s'.format(charm.internal_url)
    admin_ep = '{}/v1.0/%(tenant_id)s'.format(charm.admin_url)
    keystone.register_endpoints(charm.service_type,
                                charm.region,
                                public_ep,
                                internal_ep,
                                admin_ep)


def render_configs(interfaces_list):
    """Using a list of interfaces, render the configs and, if they have
    changes, restart the services on the unit.

    :param interfaces_list: [RelationBase] interfaces from reactive
    """
    TroveCharm.singleton.render_with_interfaces(interfaces_list)


def assess_status():
    """Just call the TroveCharm.singleton.assess_status() command to update
    status on the unit.
    """
    TroveCharm.singleton.assess_status()


def configure_ssl(keystone=None):
    """Use the singleton from the TroveCharm to configure ssl

    :param keystone: KeystoneRequires() interface class
    """
    TroveCharm.singleton.configure_ssl(keystone)


def update_peers(hacluster):
    """Use the singleton from the TroveCharm to update peers with details
    of this unit.

    @param hacluster: OpenstackHAPeers() interface class
    @returns: None
    """
    TroveCharm.singleton.update_peers(hacluster)


class TroveConfigurationAdapter(
        charms_openstack.adapters.APIConfigurationAdapter):

    def __init__(self, port_map=None):
        super(TroveConfigurationAdapter, self).__init__(
            service_name='trove',
            port_map=port_map)
        if self.keystone_api_version not in ['2', '3', 'none']:
            raise ValueError(
                "Unsupported keystone-api-version ({}). It should be 2 or 3"
                .format(self.keystone_api_version))


class TroveAdapters(charms_openstack.adapters.OpenStackAPIRelationAdapters):
    def __init__(self, relations):
        super(TroveAdapters, self).__init__(
            relations,
            options_instance=TroveConfigurationAdapter(
                port_map=TroveCharm.api_ports))


class TroveCharm(charms_openstack.charm.HAOpenStackCharm):
    service_name = name = 'trove'

    release = 'mitaka'

    packages = ['python-trove', 'python-troveclient', 'trove-common',
                'trove-api', 'trove-taskmanager', 'trove-conductor']

    services = ['trove-api', 'trove-taskmanager', 'trove-conductor']

    adapters_class = TroveAdapters

    default_service = 'trove-api'

    api_ports = {
        'trove-api': {
            os_ip.PUBLIC: 8779,
            os_ip.ADMIN: 8779,
            os_ip.INTERNAL: 8779,
        }
    }

    sync_cmd = ['trove-manage', 'db_sync']

    service_type = 'trove'

    required_relations = ['shared-db', 'amqp', 'identity-service']

    restart_map = {
        TROVE_CONF: services,
        TROVE_API_PASTE_CONF: services,
        TROVE_CONDUCTOR: services,
        TROVE_TASK_MANAGER: services,
        TROVE_GUEST_AGENT: services,
        TROVE_LOGGING_GUEST_AGENT: services
    }

    ha_resources = ['vips', 'haproxy']

    release_pkg = 'trove-common'
    package_codenames = {
        'trove-common': collections.OrderedDict([
            ('2', 'mitaka'),
            ('3', 'newton'),
            ('4', 'ocata'),
            ('5', 'pike'),
            ('6', 'queens'),
            ('7', 'rocky'),
        ]),
    }

    def install(self):
        """Customise the installation, configure the source and then call the
        parent install() method to install the packages
        """
        self.configure_source()
        # and do the actual install
        super(TroveCharm, self).install()

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.

        :returns (username, host): two strings to send to the amqp provider.
        """
        return (self.config['rabbit-user'], self.config['rabbit-vhost'])

    def get_database_setup(self):
        """Provide the default database credentials as a list of 3-tuples

        returns a structure of:
        [
            {'database': <database>,
             'username': <username>,
             'hostname': <hostname of this unit>
             'prefix': <the optional prefix for the database>, },
        ]

        :returns [{'database': ...}, ...]: credentials for multiple databases
        """
        host = None
        try:
            host = hookenv.network_get_primary_address('shared-db')
        except NotImplementedError:
            host = hookenv.unit_get('private-address')

        return [
            dict(
                database=self.config['database'],
                username=self.config['database-user'],
                hostname=host, )
        ]


# Determine the charm class by the supported release
@charms_openstack.charm.register_os_release_selector
def select_release():
    """Determine the release based on the python-keystonemiddleware that is
    installed.

    Note that this function caches the release after the first install so that
    it doesn't need to keep going and getting it from the package information.
    """
    release_version = unitdata.kv().get(OPENSTACK_RELEASE_KEY, None)
    if release_version is None:
        release_version = ch_utils.os_release('python-keystonemiddleware')
        unitdata.kv().set(OPENSTACK_RELEASE_KEY, release_version)
    return release_version
