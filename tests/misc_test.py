import time
from pygzctfapi.misc import storages, trackers
from pygzctfapi import GZAPI
from icecream import ic

url = "https://games.nullbyte.pro/"
login = 'TEST'
password = 'T3STacc0UNT_j0Kkw3U!'

storage_test_data = {
    #Previous test data
    "test_dict": {123: 456, "hello": "world", "list": [4, 5, 6], "dict": {"key": "value"}},
    "test_list": [1, 2, 334, "qwerty", ["hello", "world"], {"key": "value"}],
    "test_string": "hello world!",
    "test_int": 1239003,
    "test_float": 3.1415926,
    "test_bytes": b"goodbye world :(",
    
    # Simple Data
    "simple_string": "simple text",
    "simple_int": 42,
    "simple_float": 2.718,
    "simple_bool_true": True,
    "simple_bool_false": False,
    "simple_bytes": b"binary data",
    "empty_dict": {},
    "empty_list": [],
    
    # Complex Data
    "complex_dict": {
        "nested_dict": {
            "level_2_key": {
                "level_3_key": "deep value",
                "another_level_3_key": [1, 2, {"final_key": "final_value"}]
            }
        },
        "nested_list": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "skills": ["Python", "SQL"]},
            [123, 456, [789, {"nested_key": "nested_value"}]]
        ],
        "mixed_types": [True, None, "string", 3.14, b"bytes data"]
    },
    "complex_list": [
        "text",
        12345,
        678.90,
        [1, 2, 3, [4, 5, {"key": "value"}]],
        {"username": "user1", "password": "secret", "details": {"email": "user1@example.com"}},
        b"\x00\x01\x02\x03",
        True,
        False,
        None
    ],
    "complex_string": "This is a string with special characters: ~!@#$%^&*()_+`-=[]\\{}|;':\",./<>?",
    "large_number": 10**18,
    "negative_int": -987654,
    "negative_float": -0.123456,
    
    # Nested and Multi-type Data
    "nested_dict_with_lists": {
        "users": [
            {"name": "Charlie", "age": 25, "active": True},
            {"name": "Daisy", "age": 28, "active": False, "tags": ["admin", "editor"]},
        ],
        "settings": {
            "theme": "dark",
            "notifications": True,
            "languages": ["Python", "JavaScript", "Rust"]
        },
        "projects": {
            "project_1": {
                "title": "Research",
                "status": "ongoing",
                "data_points": [10, 20, 30, {"additional_info": ["info1", "info2"]}]
            },
            "project_2": {
                "title": "Web Development",
                "status": "completed",
                "details": {"framework": "React", "backend": "Django", "deployed": True}
            }
        }
    },
    "deeply_nested_list": [
        [
            [1, 2, [3, 4, [5, 6, [7, 8, [9, {"final": "end"}]]]]]
        ],
        [b"\xDE\xAD\xBE\xEF", "more nested data", [{"key1": "value1"}, {"key2": "value2"}]],
    ],
    "large_text_block": (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
    ),
    "unicode_string": "こんにちは世界 🌏 (Hello World in Japanese with emoji)",
    
    # Binary and Encoded Data
    "utf8_encoded_text": "UTF-8 encoded".encode('utf-8'),
    "hexadecimal_bytes": bytes.fromhex('deadbeefcafebabe'),
    "binary_data": b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09",
    "multiline_bytes": b"""
        Multiline bytes example:
        Line 1
        Line 2
        Line 3
    """
}

def storage_tst(storage: storages.StorageBaseClass):
    #If storage is not empty due to previous tests, delete all keys:
    #for key in storage_test_data:
    #    storage.delete(key)
    
    for key in storage_test_data:
        assert storage.get(key) is None
    
    for key in storage_test_data:
        storage.set(key, storage_test_data[key])
    
    for key in storage_test_data:
        assert storage.get(key) == storage_test_data[key]
    
    for key in storage_test_data:
        storage.unset(key)
    
    for key in storage_test_data:
        assert storage.get(key) is None

def storage_close(storage: storages.StorageBaseClass):
    storage.close()
    assert storage.closed


def test_storages():
    print()
    RedisStorage = storages.RedisStorage()
    PlyvelStorage = storages.LevelDBStorage("/dev/shm/pygzctfapi_test.plyvel")
    InMemoryStorage = storages.InMemoryStorage()
    SQLiteStorage = storages.SQLiteStorage("/dev/shm/pygzctfapi_test.sqlite")
    
    storage_tst(RedisStorage)
    storage_close(RedisStorage)
    ic("RedisStorage: OK")
    
    storage_tst(PlyvelStorage)
    storage_close(PlyvelStorage)
    ic("PlyvelStorage: OK")
    
    storage_tst(InMemoryStorage)
    storage_close(InMemoryStorage)
    ic("InMemoryStorage: OK")
    
    storage_tst(SQLiteStorage)
    SQLiteStorage.vacuum()
    storage_close(SQLiteStorage)
    ic("SQLiteStorage: OK")

def test_notices_tracker():
    print()
    gzapi = GZAPI(url)
    game = gzapi.game.get(1)
    storage = storages.InMemoryStorage()
    tracker = trackers.NoticesTracker(game=game, storage=storage, ignore_old_notices=True)
    while True:
        ic(tracker.get_updates())
        time.sleep(1)