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

        saved_hypervisor_plugins = VMBuilder._hypervisor_plugins
        VMBuilder._hypervisor_plugins = []
        VMBuilder.register_hypervisor_plugin(PluginA)
        VMBuilder.register_hypervisor_plugin(PluginB)
        VMBuilder.register_hypervisor_plugin(PluginC)
        self.assertEqual(VMBuilder._hypervisor_plugins[0], PluginB)
        self.assertEqual(VMBuilder._hypervisor_plugins[1], PluginA)
        self.assertEqual(VMBuilder._hypervisor_plugins[2], PluginC)
        VMBuilder._hypervisor_plugins = saved_hypervisor_plugins
