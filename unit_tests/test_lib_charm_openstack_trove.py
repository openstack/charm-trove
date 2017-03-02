# Copyright 2016 Canonical Ltd
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

from __future__ import absolute_import
from __future__ import print_function

import mock

import charmhelpers

import charm.openstack.trove as trove

import charms_openstack.test_utils as test_utils


class Helper(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(trove.TroveCharm.release)


class TestOpenStackTrove(Helper):

    def _patch_config_and_charm(self, config):
        self.patch_object(charmhelpers.core.hookenv, 'config')

        def cf(key=None):
            if key is not None:
                return config[key]
            return config

        self.config.side_effect = cf
        c = trove.TroveCharm()
        return c

    def test_install(self):
        self.patch_object(trove.TroveCharm.singleton, 'install')
        trove.install()
        self.install.assert_called_once_with()

    def test_setup_endpoint(self):
        self.patch_object(trove.TroveCharm, 'service_name',
                          new_callable=mock.PropertyMock)
        self.patch_object(trove.TroveCharm, 'region',
                          new_callable=mock.PropertyMock)
        self.patch_object(trove.TroveCharm, 'public_url',
                          new_callable=mock.PropertyMock)
        self.patch_object(trove.TroveCharm, 'internal_url',
                          new_callable=mock.PropertyMock)
        self.patch_object(trove.TroveCharm, 'admin_url',
                          new_callable=mock.PropertyMock)
        self.service_name.return_value = 'type1'
        self.region.return_value = 'region1'
        self.public_url.return_value = 'public_url'
        self.internal_url.return_value = 'internal_url'
        self.admin_url.return_value = 'admin_url'
        keystone = mock.MagicMock()
        trove.setup_endpoint(keystone)
        keystone.register_endpoints.assert_called_once_with(
            'trove', 'region1', 'public_url/v1.0/%(tenant_id)s',
            'internal_url/v1.0/%(tenant_id)s',
            'admin_url/v1.0/%(tenant_id)s')

    def test_render_configs(self):
        self.patch_object(trove.TroveCharm.singleton, 'render_with_interfaces')
        trove.render_configs('interfaces-list')
        self.render_with_interfaces.assert_called_once_with(
            'interfaces-list')

    def test_db_sync_done(self):
        self.patch_object(trove.TroveCharm, 'db_sync_done')
        trove.db_sync_done()
        self.db_sync_done.assert_called_once_with()

    def test_db_sync(self):
        self.patch_object(trove.TroveCharm.singleton, 'db_sync')
        trove.db_sync()
        self.db_sync.assert_called_once_with()

    def test_configure_ha_resources(self):
        self.patch_object(trove.TroveCharm.singleton, 'db_sync')
        trove.db_sync()
        self.db_sync.assert_called_once_with()

    def test_restart_all(self):
        self.patch_object(trove.TroveCharm.singleton, 'restart_all')
        trove.restart_all()
        self.restart_all.assert_called_once_with()

    def test_configure_ssl(self):
        self.patch_object(trove.TroveCharm.singleton, 'configure_ssl')
        trove.configure_ssl()
        self.configure_ssl.assert_called_once_with(None)

    def test_update_peers(self):
        self.patch_object(trove.TroveCharm.singleton, 'update_peers')
        trove.update_peers('cluster')
        self.update_peers.assert_called_once_with('cluster')

    def test_assess_status(self):
        self.patch_object(trove.TroveCharm.singleton, 'assess_status')
        trove.assess_status()
        self.assess_status.assert_called_once_with()

    def test_get_amqp_credentials(self):
        config = {
            'rabbit-user': 'rabbit1',
            'rabbit-vhost': 'password'
        }
        c = self._patch_config_and_charm(config)
        self.assertEqual(c.get_amqp_credentials(), ('rabbit1', 'password'))

    def test_get_database_setup(self):
        self.patch_object(charmhelpers.core.hookenv,
                          'network_get_primary_address')
        self.network_get_primary_address.return_value = 'private_ip'
        config = {
            'database': 'db1',
            'database-user': 'user1',
        }
        c = self._patch_config_and_charm(config)
        self.assertEqual(
            c.get_database_setup(),
            [dict(database='db1', username='user1', hostname='private_ip')])
