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

import subprocess

import charmhelpers.contrib.openstack.utils as ch_utils
import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.unitdata as unitdata
import charmhelpers.fetch

import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip

PACKAGES = ['python-trove', 'python-troveclient', 'trove-common', 'trove-api', 'trove-taskmanager','trove-conductor']

TROVE_DIR = '/etc/trove/'
TROVE_CONF = TROVE_DIR + "trove.conf"
TROVE_API_PASTE_CONF = TROVE_DIR + "api-paste.ini"
TROVE_CONDUCTOR = TROVE_DIR + "trove-conductor.conf"
TROVE_GUEST_AGENT = TROVE_DIR + "trove-guestagent.conf"
TROVE_TASK_MANAGER = TROVE_DIR + "trove-taskmanager.conf"

OPENSTACK_RELEASE_KEY = 'trove-charm.openstack-release-version'


###
# Handler functions for events that are interesting to the Trove charms

def install():
    """Use the singleton from the TroveCharm to install the packages on the
    unit
    """
    #unitdata.kv().unset(OPENSTACK_RELEASE_KEY)
    TroveCharm.singleton.install()


def setup_endpoint(keystone):
    """When the keystone interface connects, register this unit in the keystone
    catalogue.

    :param keystone: instance of KeystoneRequires() class from i/f
    """
    charm = TroveCharm.singleton
    keystone.register_endpoints(charm.service_type,
                                charm.region,
                                charm.public_url,
                                charm.internal_url,
                                charm.admin_url)


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


###
# Implementation of the Trove Charm classes

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

    @property
    def trove_api_keystone_pipeline(self):
        if self.keystone_api_version == "2":
            return 'cors keystone_authtoken context apiapp'
        else:
            return 'cors keystone_v3_authtoken context apiapp'

    @property
    def trove_api_pipeline(self):
        return {
            "2": "cors keystone_authtoken context apiapp",
            "3": "cors keystone_v3_authtoken context apiapp",
            "none": "cors unauthenticated-context apiapp"
        }[self.keystone_api_version]

    @property
    def trove_api_keystone_audit_pipeline(self):
        if self.keystone_api_version == "2":
            return 'keystone_authtoken context audit apiapp'
        else:
            return 'keystone_v3_authtoken context audit apiapp'


class TroveAdapters(charms_openstack.adapters.OpenStackAPIRelationAdapters):
    def __init__(self, relations):
        super(TroveAdapters, self).__init__(
            relations,
            options_instance=TroveConfigurationAdapter(
                port_map=TroveCharm.api_ports))


class TroveCharm(charms_openstack.charm.HAOpenStackCharm):
    release = 'mitaka'
    name = 'trove'
    packages = PACKAGES
    api_ports = {
        'trove-worker': {
            os_ip.PUBLIC: 8779,
            os_ip.ADMIN: 8779,
            os_ip.INTERNAL: 8779,
        }
    }
    service_type = 'trove'
    default_service = 'trove-worker'
    services = ['trove-api', 'trove-taskmanager', 'trove-conductor']

    # Note that the hsm interface is optional - defined in config.yaml
    #required_relations = ['shared-db', 'amqp', 'identity-service', 'image-service', 'cloud-compute', 'cluster',cinder heat swift]
    required_relations = ['shared-db', 'amqp', 'identity-service', 'image-service', 'cloud-compute', 'cinder-volume-service']

    restart_map = {
        TROVE_CONF: services,
        TROVE_API_PASTE_CONF: services,
        TROVE_CONDUCTOR: services,
        TROVE_TASK_MANAGER: services
    }

    adapters_class = TroveAdapters
    ha_resources = ['vips', 'haproxy']

    def install(self):
        """Customise the installation, configure the source and then call the
        parent install() method to install the packages
        """
        self.configure_source()
        # and do the actual install
        super(TroveCharm, self).install()


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