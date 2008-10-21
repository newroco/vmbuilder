#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2008 Canonical
#    
#    See AUTHORS for list of contributors
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Tests, tests, tests, and more tests
import unittest
import VMBuilder.disk

class TestSequenceFunctions(unittest.TestCase):
    def test_parse_size(self):
        self.assertEqual(VMBuilder.disk.parse_size(10), 10)
        self.assertEqual(VMBuilder.disk.parse_size('10'), 10)
        self.assertEqual(VMBuilder.disk.parse_size('10m'), 10)
        self.assertEqual(VMBuilder.disk.parse_size('10M'), 10)
        self.assertEqual(VMBuilder.disk.parse_size('10G'), 10240)
        self.assertEqual(VMBuilder.disk.parse_size('10g'), 10240)
        self.assertEqual(VMBuilder.disk.parse_size('10240K'), 10)
        self.assertEqual(VMBuilder.disk.parse_size('10240k'), 10)
        self.assertEqual(VMBuilder.disk.parse_size('10250K'), 10)

    def test_index_to_devname(self):
        self.assertEqual(VMBuilder.disk.index_to_devname(0), 'a')
        self.assertEqual(VMBuilder.disk.index_to_devname(26), 'aa')
        self.assertEqual(VMBuilder.disk.index_to_devname(18277), 'zzz')

    def test_devname_to_index(self):
        self.assertEqual(VMBuilder.disk.devname_to_index('a'), 0)
        self.assertEqual(VMBuilder.disk.devname_to_index('b'), 1)
        self.assertEqual(VMBuilder.disk.devname_to_index('aa'), 26)
        self.assertEqual(VMBuilder.disk.devname_to_index('z'), 25)
        self.assertEqual(VMBuilder.disk.devname_to_index('zz'), 701)
        self.assertEqual(VMBuilder.disk.devname_to_index('zzz'), 18277)

class TestUbuntuPlugin(unittest.TestCase):
    def test_preflight_check_failed(self):
        import VMBuilder
        from VMBuilder.plugins.ubuntu.distro import Ubuntu
        from VMBuilder.exception import VMBuilderUserError

        vm = VMBuilder.VM()
        vm.suite = 'foo'
        ubuntu = Ubuntu(vm)
        self.assertRaises(VMBuilderUserError, ubuntu.preflight_check)

if __name__ == '__main__':
    unittest.main()

