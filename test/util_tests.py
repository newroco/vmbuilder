import unittest

import VMBuilder
from VMBuilder.util import run_cmd

class TestUtils(unittest.TestCase):
    def test_run_cmd(self):
        self.assertTrue("foobarbaztest" in run_cmd("env", env={'foobarbaztest' : 'bar' }))

    def test_plugin_priority(self):
        class Plugin(object):
            priority = 10

        class PluginA(Plugin):
            pass

        class PluginB(Plugin):
            priority = 5

        class PluginC(Plugin):
            priority = 15

        saved_plugins = VMBuilder._plugins
        VMBuilder._plugins = []
        VMBuilder.register_plugin(PluginA)
        VMBuilder.register_plugin(PluginB)
        VMBuilder.register_plugin(PluginC)
        self.assertEqual(VMBuilder._plugins[0], PluginB)
        self.assertEqual(VMBuilder._plugins[1], PluginA)
        self.assertEqual(VMBuilder._plugins[2], PluginC)
        VMBuilder._plugins = saved_plugins
