from pygzctfapi.misc import storages


def test_storages():
    RedisStorage = storages.RedisStorage()
    PlyvelStorage = storages.PlyvelStorage("/dev/shm/pygzctfapi_test.plyvel")
    InMemoryStorage = storages.InMemoryStorage()
    
    test_dict = {123: 456, "hello": "world", "list": [4, 5, 6], "dict": {"key": "value"}}
    test_list = [1, 2, 334, "qwerty", ["hello", "world"], {"key": "value"}]
    test_string = "hello world!"
    test_int = 1239003
    test_float = 3.1415926
    test_bytes = b"goodbye world :("
    
    RedisStorage.put("test_dict", test_dict)
    RedisStorage.put("test_list", test_list)
    RedisStorage.put("test_string", test_string)
    RedisStorage.put("test_int", test_int)
    RedisStorage.put("test_float", test_float)
    RedisStorage.put("test_bytes", test_bytes)
    
    assert RedisStorage.get("test_dict") == test_dict
    assert RedisStorage.get("test_list") == test_list
    assert RedisStorage.get("test_string") == test_string
    assert RedisStorage.get("test_int") == test_int
    assert RedisStorage.get("test_float") == test_float
    assert RedisStorage.get("test_bytes") == test_bytes
    
    RedisStorage.delete("test_dict")
    RedisStorage.delete("test_list")
    RedisStorage.delete("test_string")
    RedisStorage.delete("test_int")
    RedisStorage.delete("test_float")
    RedisStorage.delete("test_bytes")
    
    assert RedisStorage.get("test_dict") is None
    assert RedisStorage.get("test_list") is None
    assert RedisStorage.get("test_string") is None
    assert RedisStorage.get("test_int") is None
    assert RedisStorage.get("test_float") is None
    assert RedisStorage.get("test_bytes") is None
    
    RedisStorage.close()
    assert RedisStorage.closed
    
    PlyvelStorage.put("test_dict", test_dict)
    PlyvelStorage.put("test_list", test_list)
    PlyvelStorage.put("test_string", test_string)
    PlyvelStorage.put("test_int", test_int)
    PlyvelStorage.put("test_float", test_float)
    PlyvelStorage.put("test_bytes", test_bytes)
    
    assert PlyvelStorage.get("test_dict") == test_dict
    assert PlyvelStorage.get("test_list") == test_list
    assert PlyvelStorage.get("test_string") == test_string
    assert PlyvelStorage.get("test_int") == test_int
    assert PlyvelStorage.get("test_float") == test_float
    assert PlyvelStorage.get("test_bytes") == test_bytes
    
    PlyvelStorage.delete("test_dict")
    PlyvelStorage.delete("test_list")
    PlyvelStorage.delete("test_string")
    PlyvelStorage.delete("test_int")
    PlyvelStorage.delete("test_float")
    PlyvelStorage.delete("test_bytes")
    
    assert PlyvelStorage.get("test_dict") is None    
    assert PlyvelStorage.get("test_list") is None
    assert PlyvelStorage.get("test_string") is None
    assert PlyvelStorage.get("test_int") is None
    assert PlyvelStorage.get("test_float") is None
    assert PlyvelStorage.get("test_bytes") is None

    PlyvelStorage.close()
    assert PlyvelStorage.closed
    
    InMemoryStorage.put("test_dict", test_dict)
    InMemoryStorage.put("test_list", test_list)
    InMemoryStorage.put("test_string", test_string)
    InMemoryStorage.put("test_int", test_int)
    InMemoryStorage.put("test_float", test_float)
    InMemoryStorage.put("test_bytes", test_bytes)
    
    assert InMemoryStorage.get("test_dict") == test_dict
    assert InMemoryStorage.get("test_list") == test_list
    assert InMemoryStorage.get("test_string") == test_string
    assert InMemoryStorage.get("test_int") == test_int
    assert InMemoryStorage.get("test_float") == test_float
    assert InMemoryStorage.get("test_bytes") == test_bytes
    
    InMemoryStorage.delete("test_dict")
    InMemoryStorage.delete("test_list")
    InMemoryStorage.delete("test_string")
    InMemoryStorage.delete("test_int")
    InMemoryStorage.delete("test_float")
    InMemoryStorage.delete("test_bytes")
    
    assert InMemoryStorage.get("test_dict") is None    
    assert InMemoryStorage.get("test_list") is None
    assert InMemoryStorage.get("test_string") is None
    assert InMemoryStorage.get("test_int") is None
    assert InMemoryStorage.get("test_float") is None
    assert InMemoryStorage.get("test_bytes") is None

    InMemoryStorage.close()
    assert InMemoryStorage.closed