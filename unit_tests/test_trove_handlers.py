from __future__ import absolute_import
from __future__ import print_function

import unittest

import mock

import reactive.trove_handlers as handlers


_when_args = {}
_when_not_args = {}


def mock_hook_factory(d):

    def mock_hook(*args, **kwargs):

        def inner(f):
            # remember what we were passed.  Note that we can't actually
            # determine the class we're attached to, as the decorator only gets
            # the function.
            try:
                d[f.__name__].append(dict(args=args, kwargs=kwargs))
            except KeyError:
                d[f.__name__] = [dict(args=args, kwargs=kwargs)]
            return f
        return inner
    return mock_hook


class TestTroveHandlers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._patched_when = mock.patch('charms.reactive.when',
                                       mock_hook_factory(_when_args))
        cls._patched_when_started = cls._patched_when.start()
        cls._patched_when_not = mock.patch('charms.reactive.when_not',
                                           mock_hook_factory(_when_not_args))
        cls._patched_when_not_started = cls._patched_when_not.start()
        # force requires to rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(handlers)
        except NameError:
            import importlib
            importlib.reload(handlers)

    @classmethod
    def tearDownClass(cls):
        cls._patched_when.stop()
        cls._patched_when_started = None
        cls._patched_when = None
        cls._patched_when_not.stop()
        cls._patched_when_not_started = None
        cls._patched_when_not = None
        # and fix any breakage we did to the module
        try:
            reload(handlers)
        except NameError:
            import importlib
            importlib.reload(handlers)

    def setUp(self):
        self._patches = {}
        self._patches_start = {}

    def tearDown(self):
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch(self, obj, attr, return_value=None):
        mocked = mock.patch.object(obj, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def test_registered_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        when_patterns = {
            'setup_amqp_req': [('amqp.connected', )],
            'setup_database': [('shared-db.connected', )],
            'setup_endpoint': [('identity-service.connected', )],
            'configure_ssl': [('identity-service.available', )],
            'update_peers': [('cluster.available', )],
            'config_changed': [('config.changed', )],
            'cluster_connected': [('ha.connected', )],
            'render_stuff': [('amqp.available',),
                             ('identity-service.available',),
                             ('shared-db.available',)],
            'run_db_migration': [('config.complete',)]
        }
        when_not_patterns = {
            'install_packages': [('charm.installed', )],
            'run_db_migration': [('db.synced',)],
        }
        # check the when hooks are attached to the expected functions
        for t, p in [(_when_args, when_patterns),
                     (_when_not_args, when_not_patterns)]:
            for f, args in t.items():
                # check that function is in patterns
                print('f: {}'.format(f))
                self.assertTrue(f in p.keys())
                # check that the lists are equal
                l = [a['args'] for a in args]
                self.assertEqual(l, p[f])

    def test_install_packages(self):
        self.patch(handlers.trove, 'install')
        self.patch(handlers.reactive, 'set_state')
        handlers.install_packages()
        self.install.assert_called_once_with()
        self.set_state.assert_called_once_with('charm.installed')

    def test_setup_amqp_req(self):
        self.patch(handlers.trove, 'assess_status')
        amqp = mock.MagicMock()
        handlers.setup_amqp_req(amqp)
        amqp.request_access.assert_called_once_with(
            username='trove', vhost='openstack')
        self.assess_status.assert_called_once_with()

    def test_database(self):
        self.patch(handlers.trove, 'assess_status')
        database = mock.MagicMock()
        self.patch(handlers.hookenv, 'unit_private_ip', 'private_ip')
        handlers.setup_database(database)
        calls = [
            mock.call(
                'trove',
                'trove',
                'private_ip',
                prefix='trove'),
        ]
        database.configure.has_calls(calls)
        self.assess_status.assert_called_once_with()

    def test_setup_endpoint(self):
        self.patch(handlers.trove, 'assess_status')
        self.patch(handlers.trove, 'setup_endpoint')
        handlers.setup_endpoint('endpoint_object')
        self.setup_endpoint.assert_called_once_with('endpoint_object')
        self.assess_status.assert_called_once_with()

    def test_update_peers(self):
        cluster = mock.MagicMock()
        self.patch(handlers.trove, 'update_peers')
        handlers.update_peers(cluster)
        self.update_peers.assert_called_once_with(cluster)

    def test_config_changed(self):
        self.patch(handlers.trove, 'assess_status')
        handlers.config_changed()
        self.assess_status.assert_called_once_with()
