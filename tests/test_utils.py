import pytest
from tests.conftest import assert_equal_objects, assert_not_equal_objects
from saana_lib.connectMongo import client


"""
Tests in this file are meant to test utilities used in other tests
"""


class TestAssertEqualObjects(object):

    def test_integers_1(self):
        assert_equal_objects(1, 1)
    
    def test_integers_2(self):
        assert_not_equal_objects(1, 0)
    
    def test_strings_1(self):
        assert_not_equal_objects('bbaa', 'aabb')
    
    def test_strings_2(self):
        assert_equal_objects('aa', 'aa')
    
    def test_lists_1(self):
        assert_not_equal_objects([1, 2, 4], [1, 2])
    
    def test_list_2(self):
        assert_equal_objects([1, 2], [2, 1])
    
    def test_lists_3(self):
        assert_equal_objects([{'a': [0, 1]}], [{'a': [1, 0]}])
    
    def test_lists_4(self):
        assert_not_equal_objects([{'a': 1}], [{'a': 2}])

    def test_dicts_1(self):
        assert_not_equal_objects({
            'name': 'Rob',
            'age': 20
        }, {
            'name': 'Anthony',
            'age': 20
        })
    
    def test_dicts_2(self):
        assert_equal_objects({
            'list': [3, 2],
            'age': 20
        }, {
            'list': [2, 3],
            'age': 20
        })
    
    def test_dicts_3(self):
        assert_not_equal_objects({
            'list': [3, 2, 4],
            'age': 20
        }, {
            'list': [2, 3, 1],
            'age': 20
        })
    
    def test_dicts_4(self):
        assert_equal_objects({
            'k1': {
                'list': [3, 2, 4]
            },
            'k2': {
                'name': 'Bob'
            }
        }, {
            'k1': {
                'list': [4, 3, 2]
            },
            'k2': {
                'name': 'Bob'
            }
        })
    
    def test_dict_5(self):
        assert_equal_objects({
            'dict': {
                'nested': {
                    'val': 1
                }
            }
        }, {
            'dict': {
                'nested': {
                    'val': 1
                }
            }
        })
    
    def test_dict_6(self):
        assert_not_equal_objects({
            'dict': {
                'nested': {
                    'vael': 1
                }
            }
        }, {
            'dict': {
                'nested': {
                    'val': 1
                }
            }
        })
    
    def test_dict_7(self):
        base = {'a': 1, 'b': 2, 'c': 3}
        assert_equal_objects(
            [1, 2, 3],
            [v for k, v in base.items()]
        )
    
    def test_bytes_1(self):
        assert_not_equal_objects(b'test', b'TEST')



