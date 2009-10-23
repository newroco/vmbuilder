#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2009 Canonical Ltd.
#    
#    See AUTHORS for list of contributors
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest

from VMBuilder.disk import parse_size, index_to_devname, devname_to_index

class TestSizeParser(unittest.TestCase):
    def test_suffixesAreCaseInsensitive(self):
        "Suffixes in size strings are case-insensitive"
        
        for letter in ['K', 'M', 'G']:
            self.assertEqual(parse_size('1%s' % letter), parse_size('1%s' % letter.lower()))
            
    def test_suffixless_counts_as_megabytes(self):
        "Suffix-less size string are counted as megabytes"
        self.assertEqual(parse_size(10), 10)
        self.assertEqual(parse_size('10'), 10)
    
    def test_M_suffix_counts_as_megabytes(self):
        "Sizes with M suffix are counted as megabytes"
        self.assertEqual(parse_size('10M'), 10)
    
    def test_G_suffix_counts_as_gigabytes(self):
        "1G is counted as 1024 megabytes"
        self.assertEqual(parse_size('1G'), 1024)
        
    def test_K_suffix_counts_as_kilobytes(self):
        "1024K is counted as 1 megabyte"
        self.assertEqual(parse_size('1024K'), 1)
        
    def test_rounds_size_to_nearest_megabyte(self):
        "parse_size rounds to nearest MB"
        self.assertEqual(parse_size('1025K'), 1)
        self.assertEqual(parse_size('10250K'), 10)

class TestSequenceFunctions(unittest.TestCase):
    def test_index_to_devname(self):
        self.assertEqual(index_to_devname(0), 'a')
        self.assertEqual(index_to_devname(26), 'aa')
        self.assertEqual(index_to_devname(18277), 'zzz')

    def test_devname_to_index(self):
        self.assertEqual(devname_to_index('a'), 0)
        self.assertEqual(devname_to_index('b'), 1)
        self.assertEqual(devname_to_index('aa'), 26)
        self.assertEqual(devname_to_index('ab'), 27)
        self.assertEqual(devname_to_index('z'), 25)
        self.assertEqual(devname_to_index('zz'), 701)
        self.assertEqual(devname_to_index('zzz'), 18277)

    def test_index_to_devname_and_back(self):
        for i in range(18277):
            self.assertEqual(i, devname_to_index(index_to_devname(i)))


