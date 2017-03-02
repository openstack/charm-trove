from __future__ import absolute_import
from __future__ import print_function

import charms_openstack.test_utils as test_utils

import reactive.trove_handlers as handlers


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'amqp.connected',
            'shared-db.connected',
            'identity-service.connected',
            'identity-service.available',  # enables SSL support
            'config.changed',
            'config.complete',
            'db.synced']
        hook_set = {
            'when': {
                'render_stuff': ('shared-db.available',
                                 'identity-service.available',
                                 'amqp.available',),
                'update_peers': ('cluster.available',),
                'setup_endpoint': ('identity-service.connected',),
                'cluster_connected': ('ha.connected',),
                'run_db_migration': ('config.complete',),
            },
            'when_not': {
                'run_db_migration': ('db.synced',),
            },
        }
        # test that the hooks were registered via the
        # reactive.trove_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)
