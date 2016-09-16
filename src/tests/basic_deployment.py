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


import amulet
import json
import subprocess
import time


import troveclient.client as trove_client

import charmhelpers.contrib.openstack.amulet.deployment as amulet_deployment
import charmhelpers.contrib.openstack.amulet.utils as os_amulet_utils

# Use DEBUG to turn on debug logging
u = os_amulet_utils.OpenStackAmuletUtils(os_amulet_utils.DEBUG)


class TroveBasicDeployment(amulet_deployment.OpenStackAmuletDeployment):
    """Amulet tests on a basic trove deployment."""

    def __init__(self, series, openstack=None, source=None, stable=False):
        """Deploy the entire test environment."""
        super(TroveBasicDeployment, self).__init__(series, openstack,
                                                       source, stable)
        self._add_services()
        self._add_relations()
        self._configure_services()
        self._deploy()

        u.log.info('Waiting on extended status checks...')
        exclude_services = ['mysql', 'mongodb']
        self._auto_wait_for_status(exclude_services=exclude_services)

        self._initialize_tests()

    def _add_services(self):
        """Add services

           Add the services that we're testing, where trove is local,
           and the rest of the service are from lp branches that are
           compatible with the local charm (e.g. stable or next).
           """
        this_service = {'name': 'trove'}
        other_services = [{'name': 'mysql'},
                          {'name': 'rabbitmq-server'},
                          {'name': 'keystone'},]
        super(TroveBasicDeployment, self)._add_services(this_service,
                                                            other_services)

    def _add_relations(self):
        """Add all of the relations for the services."""
        relations = {
            'trove:shared-db': 'mysql:shared-db',
            'trove:amqp': 'rabbitmq-server:amqp',
            'trove:identity-service': 'keystone:identity-service',
            'keystone:shared-db': 'mysql:shared-db',
        }
        super(TroveBasicDeployment, self)._add_relations(relations)

    def _configure_services(self):
        """Configure all of the services."""
        keystone_config = {'admin-password': 'openstack',
                           'admin-token': 'ubuntutesting'}
        configs = {'keystone': keystone_config}
        super(TroveBasicDeployment, self)._configure_services(configs)

    def _get_token(self):
        return self.keystone.service_catalog.catalog['token']['id']

    def _initialize_tests(self):
        """Perform final initialization before tests get run."""
        # Access the sentries for inspecting service units
        self.trove_sentry = self.d.sentry['trove'][0]
        self.mysql_sentry = self.d.sentry['mysql'][0]
        self.keystone_sentry = self.d.sentry['keystone'][0]
        self.rabbitmq_sentry = self.d.sentry['rabbitmq-server'][0]
        u.log.debug('openstack release val: {}'.format(
            self._get_openstack_release()))
        u.log.debug('openstack release str: {}'.format(
            self._get_openstack_release_string()))
        self.trove_svcs = ['trove-api', 'trove-taskmanager', 'trove-conductor',]

        # Authenticate admin with keystone endpoint
        self.keystone = u.authenticate_keystone_admin(self.keystone_sentry,
                                                      user='admin',
                                                      password='openstack',
                                                      tenant='admin')

        # Authenticate admin with trove endpoint
        trove_ep = self.keystone.service_catalog.url_for(
            service_type='trove',
            endpoint_type='publicURL')
        keystone_ep = self.keystone.service_catalog.url_for(
            service_type='identity',
            endpoint_type='publicURL')
        self.trove = trove_client.Client(
            version='1',
            auth_url=keystone_ep,
            username="admin",
            password="openstack",
            tenant_name="admin",
            endpoint=trove_ep)

    def check_and_wait(self, check_command, interval=2, max_wait=200,
                       desc=None):
        waited = 0
        while not check_command() or waited > max_wait:
            if desc:
                u.log.debug(desc)
            time.sleep(interval)
            waited = waited + interval
        if waited > max_wait:
            raise Exception('cmd failed {}'.format(check_command))

    def _run_action(self, unit_id, action, *args):
        command = ["juju", "action", "do", "--format=json", unit_id, action]
        command.extend(args)
        print("Running command: %s\n" % " ".join(command))
        output = subprocess.check_output(command)
        output_json = output.decode(encoding="UTF-8")
        data = json.loads(output_json)
        action_id = data[u'Action queued with id']
        return action_id

    def _wait_on_action(self, action_id):
        command = ["juju", "action", "fetch", "--format=json", action_id]
        while True:
            try:
                output = subprocess.check_output(command)
            except Exception as e:
                print(e)
                return False
            output_json = output.decode(encoding="UTF-8")
            data = json.loads(output_json)
            if data[u"status"] == "completed":
                return True
            elif data[u"status"] == "failed":
                return False
            time.sleep(2)

    def test_100_services(self):
        """Verify the expected services are running on the corresponding
           service units."""
        u.log.debug('Checking system services on units...')

        service_names = {
            self.trove_sentry: self.trove_svcs,
        }

        ret = u.validate_services_by_name(service_names)
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

        u.log.debug('OK')

    def test_110_service_catalog(self):
        """Verify that the service catalog endpoint data is valid."""
        u.log.debug('Checking keystone service catalog data...')
        endpoint_check = {
            'adminURL': u.valid_url,
            'id': u.not_null,
            'region': 'RegionOne',
            'publicURL': u.valid_url,
            'internalURL': u.valid_url
        }
        expected = {
            'dns': [endpoint_check],
        }
        actual = self.keystone.service_catalog.get_endpoints()

        ret = u.validate_svc_catalog_endpoint_data(expected, actual)
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

        u.log.debug('OK')

    def test_114_trove_api_endpoint(self):
        """Verify the trove api endpoint data."""
        u.log.debug('Checking trove api endpoint data...')
        endpoints = self.keystone.endpoints.list()
        u.log.debug(endpoints)
        admin_port = internal_port = public_port = '9001'
        expected = {'id': u.not_null,
                    'region': 'RegionOne',
                    'adminurl': u.valid_url,
                    'internalurl': u.valid_url,
                    'publicurl': u.valid_url,
                    'service_id': u.not_null}

        ret = u.validate_endpoint_data(endpoints, admin_port, internal_port,
                                       public_port, expected)
        if ret:
            message = 'Trove endpoint: {}'.format(ret)
            amulet.raise_status(amulet.FAIL, msg=message)

        u.log.debug('OK')

    def test_200_trove_identity_relation(self):
        """Verify the trove to keystone identity-service relation data"""
        u.log.debug('Checking trove to keystone identity-service '
                    'relation data...')
        unit = self.trove_sentry
        relation = ['identity-service', 'keystone:identity-service']
        trove_ip = unit.relation(
            'identity-service',
            'keystone:identity-service')['private-address']
        trove_endpoint = "http://%s:8779" % (trove_ip)

        expected = {
            'admin_url': trove_endpoint,
            'internal_url': trove_endpoint,
            'private-address': trove_ip,
            'public_url': trove_endpoint,
            'region': 'RegionOne',
            'service': 'trove',
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('trove identity-service', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

        u.log.debug('OK')

    def test_201_keystone_trove_identity_relation(self):
        """Verify the keystone to trove identity-service relation data"""
        u.log.debug('Checking keystone:trove identity relation data...')
        unit = self.keystone_sentry
        relation = ['identity-service', 'trove:identity-service']
        id_relation = unit.relation('identity-service',
                                    'trove:identity-service')
        id_ip = id_relation['private-address']
        expected = {
            'admin_token': 'ubuntutesting',
            'auth_host': id_ip,
            'auth_port': "35357",
            'auth_protocol': 'http',
            'private-address': id_ip,
            'service_host': id_ip,
            'service_password': u.not_null,
            'service_port': "5000",
            'service_protocol': 'http',
            'service_tenant': 'services',
            'service_tenant_id': u.not_null,
            'service_username': 'trove',
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('keystone identity-service', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

        u.log.debug('OK')

    def test_203_trove_amqp_relation(self):
        """Verify the trove to rabbitmq-server amqp relation data"""
        u.log.debug('Checking trove:rabbitmq amqp relation data...')
        unit = self.trove_sentry
        relation = ['amqp', 'rabbitmq-server:amqp']
        expected = {
            'username': 'trove',
            'private-address': u.valid_ip,
            'vhost': 'openstack'
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('trove amqp', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

        u.log.debug('OK')

    def test_204_amqp_trove_relation(self):
        """Verify the rabbitmq-server to trove amqp relation data"""
        u.log.debug('Checking rabbitmq:trove amqp relation data...')
        unit = self.rabbitmq_sentry
        relation = ['amqp', 'trove:amqp']
        expected = {
            'hostname': u.valid_ip,
            'private-address': u.valid_ip,
            'password': u.not_null,
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('rabbitmq amqp', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

        u.log.debug('OK')

    def test_900_restart_on_config_change(self):
        """Verify that the specified services are restarted when the config
           is changed.
           """
        sentry = self.trove_sentry
        juju_service = 'trove'

        # Expected default and alternate values
        set_default = {'debug': 'False'}
        set_alternate = {'debug': 'True'}

        # Services which are expected to restart upon config change,
        # and corresponding config files affected by the change
        conf_file = '/etc/trove/trove.conf'
        services = {svc: conf_file for svc in self.trove_svcs}

        # Make config change, check for service restarts
        u.log.debug('Making config change on {}...'.format(juju_service))
        mtime = u.get_sentry_time(sentry)
        self.d.configure(juju_service, set_alternate)

        sleep_time = 50
        for s, conf_file in services.iteritems():
            u.log.debug("Checking that service restarted: {}".format(s))
            if not u.validate_service_config_changed(sentry, mtime, s,
                                                     conf_file,
                                                     retry_count=4,
                                                     retry_sleep_time=20,
                                                     sleep_time=sleep_time):
                self.d.configure(juju_service, set_default)
                msg = "service {} didn't restart after config change".format(s)
                amulet.raise_status(amulet.FAIL, msg=msg)
            sleep_time = 0

        self.d.configure(juju_service, set_default)
        u.log.debug('OK')
