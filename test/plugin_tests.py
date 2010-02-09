import unittest

import VMBuilder.plugins
from   VMBuilder.exception import VMBuilderException

class TestPluginsSettings(unittest.TestCase):
    class VM(VMBuilder.plugins.Plugin):
        def __init__(self, *args, **kwargs):
            self._config = {}
            self.vm = self

    class TestPlugin(VMBuilder.plugins.Plugin):
        pass

    def setUp(self):
        self.vm = self.VM()
        self.plugin = self.TestPlugin(self.vm)

    def test_add_setting_group_and_setting(self):
        setting_group = self.plugin.setting_group('Test Setting Group')
        self.assertTrue(setting_group in self.plugin._setting_groups, "Setting not added correctly to plugin's registry of setting groups.")

        setting_group.add_setting('testsetting')
        self.assertEqual(self.vm.get_setting('testsetting'), None, "Setting's default value is not None.")

        self.vm.set_setting_default('testsetting', 'newdefault')
        self.assertEqual(self.vm.get_setting('testsetting'), 'newdefault', "Setting does not return custom default value when no value is set.")
        self.assertEqual(self.vm.get_setting_default('testsetting'), 'newdefault', "Setting does not return custom default value through get_setting_default().")

        self.vm.set_setting('testsetting', 'foo')
        self.assertEqual(self.vm.get_setting('testsetting'), 'foo', "Setting does not return set value.")

        self.vm.set_setting_default('testsetting', 'newerdefault')
        self.assertEqual(self.vm.get_setting('testsetting'), 'foo', "Setting does not return set value after setting new default value.")

    def test_invalid_type_raises_exception(self):
        setting_group = self.plugin.setting_group('Test Setting Group')
        self.assertRaises(VMBuilderException, setting_group.add_setting, 'oddsetting', type='odd')

    def test_valid_options(self):
        setting_group = self.plugin.setting_group('Test Setting Group')

        setting_group.add_setting('strsetting')
        self.assertRaises(VMBuilderException, self.vm.set_setting_valid_options, 'strsetting', '')
        self.vm.set_setting_valid_options('strsetting', ['foo', 'bar'])
        self.assertEqual(self.vm.get_setting_valid_options('strsetting'), ['foo', 'bar'])
        self.vm.set_setting('strsetting', 'foo')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'strsetting', 'baz')
        self.vm.set_setting_valid_options('strsetting', None)
        self.vm.set_setting('strsetting', 'baz')
        
    def test_invalid_type_setting_raises_exception(self):
        setting_group = self.plugin.setting_group('Test Setting Group')

        setting_group.add_setting('strsetting')
        self.vm.set_setting('strsetting', '')
        self.vm.set_setting_default('strsetting', '')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'strsetting', 0)
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'strsetting', 0)
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'strsetting', True)
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'strsetting', True)
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'strsetting', [])
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'strsetting', [])

        setting_group.add_setting('intsetting', type='int')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'intsetting', '')
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'intsetting', '')
        self.vm.set_setting('intsetting', 0)
        self.vm.set_setting_default('intsetting', 0)
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'intsetting', True)
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'intsetting', True)
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'intsetting', [])
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'intsetting', [])

        setting_group.add_setting('boolsetting', type='bool')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'boolsetting', '')
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'boolsetting', '')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'boolsetting', 0)
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'boolsetting', 0)
        self.vm.set_setting('boolsetting', True)
        self.vm.set_setting_default('boolsetting', True)
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'boolsetting', [])
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'boolsetting', [])

        setting_group.add_setting('listsetting', type='list')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'listsetting', '')
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'listsetting', '')
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'listsetting', 0)
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'listsetting', 0)
        self.assertRaises(VMBuilderException, self.vm.set_setting, 'listsetting', True)
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'listsetting', True)
        self.vm.set_setting('listsetting', [])
        self.vm.set_setting_default('listsetting', [])

    def test_set_setting_raises_exception_on_invalid_setting(self):
        self.assertRaises(VMBuilderException, self.vm.set_setting_default, 'testsetting', 'newdefault')

    def test_add_setting(self):
        setting_group = self.plugin.setting_group('Test Setting Group')
