import msgpack
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, Optional
from threading import Lock
from pygzctfapi import exceptions
from copy import deepcopy

try:
    import redis
except ImportError:
    redis = None
try:
    import plyvel
except ImportError:
    plyvel = None

class BytesStorageBase(ABC):

    def get(self, key: str) -> Union[Dict, List, str, int, bytes, float]:
        """
        Retrieve the value associated with the given key from the storage.

        Args:
            key (str): The key to retrieve the value for.

        Returns:
            Union[Dict, List, str, int, bytes, float]: The value associated with the key, or None if the key does not exist.

        Raises:
            StorageOperationError: If any error occurs while retrieving the key.
        """
        key = self.prepare_key(key)
        try:
            value = self._get(key)
            if value is None:
                return None
            return msgpack.unpackb(value, strict_map_key=False)
        except Exception as e:
            raise exceptions.StorageOperationError(exception=e)
    
    @abstractmethod
    def _get(self, key: Union[str, bytes]) -> bytes:
        """
        Actually retrieve the value from the storage.
        
        Args:
            key (Union[str, bytes]): The key to retrieve the value for.
        
        Returns:
            bytes: The stored value associated with the key.
        """
        pass

    def put(self, key: str, value: Union[Dict, List, str, int, bytes, float]) -> None:
        """
        Store a value based on the key in the storage.
        
        Args:
            key (str): The key to associate the value with.
            value (Union[Dict, List, str, int, bytes, float]): The value to store.
        
        Raises:
            StorageOperationError: If any error occurs while storing the value.
        """
        key = self.prepare_key(key)
        value = self.prepare_data(value)
        try:
            self._put(key, value)
        except Exception as e:
            raise exceptions.StorageOperationError(exception=e)
    
    @abstractmethod
    def _put(self, key: Union[str, bytes], value: bytes) -> None:
        """
        Actually store the value in the storage.
        
        Args:
            key (Union[str, bytes]): The key to store the value
            value (bytes): The value to store
        """
        pass

    def delete(self, key: str) -> None:
        """
        Delete a key from the storage.
        
        Args:
            key (str): The key to delete.

        Raises:
            StorageOperationError: If any error occurs while deleting the key.
        """
        key = self.prepare_key(key)
        try:
            self._delete(key)
        except Exception as e:
            raise exceptions.StorageOperationError(exception=e)
    
    @abstractmethod
    def _delete(self, key: Union[str, bytes]) -> None:
        """
        Actually delete the key from the storage.

        Args:
            key (Union[str, bytes]): The key to delete.
        """
        pass

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the storage.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.

        Raises:
            StorageOperationError: If any error occurs while checking the key.
        """
        key = self.prepare_key(key)
        try:
            return self._get(key) is not None
        except Exception as e:
            raise exceptions.StorageOperationError(exception=e)
    
    def prepare_data(self, data: Union[Dict, List, str, int, bytes, float]) -> bytes:
        """
        Serialize the given data to bytes.

        Args:
            data (Union[Dict, List, str, int, bytes, float]): The data to serialize.

        Returns:
            bytes: The serialized data.

        Raises:
            ValueError: If the data cannot be serialized.
        """
        try:
            binary_data = msgpack.packb(data)
            return binary_data
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}")
    
    @abstractmethod
    def prepare_key(self, key: str) -> Union[str, bytes]:
        """
        Prepare and convert the key to a consistent format (e.g., bytes).

        Args:
            key (str): The key to convert.

        Returns:
            Union[str, bytes]: The converted key.
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close the storage connection.
        """
        pass
    
    @property
    @abstractmethod
    def closed(self) -> bool:
        """
        Check if the storage connection is closed.

        Returns:
            bool: True if the storage connection is closed, False otherwise.
        """
        pass

class RedisStorage(BytesStorageBase):

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        Initialize a RedisStorage object with the given connection parameters.

        Args:
            host (str, optional): The hostname of the Redis instance. Defaults to 'localhost'.
            port (int, optional): The port of the Redis instance. Defaults to 6379.
            db (int, optional): The database number to use. Defaults to 0.
            password (str, optional): The password to use for authentication. Defaults to None.

        Raises:
            ModuleNotFoundError: If the 'redis' module is not installed.
            StorageOperationError: If the connection to Redis fails.
        """
        if not redis:
            raise ModuleNotFoundError("Redis addon is not installed. Install it with 'pip install pygzctfapi[redis]'.")
        try:
            self._client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=False)
        except Exception as e:
            raise exceptions.StorageOperationError("Failed to connect to Redis: {exception}.", exception=e)

    def _get(self, key: str) -> Optional[bytes]:
        """
        Actually get the value from Redis.
        
        Args:
            key (str): The key to retrieve the value for.
        
        Returns:
            Optional[bytes]: The value associated with the key, or None if the key does not exist.
        """
        value = self._client.get(key)
        return value

    def _put(self, key: str, value: bytes) -> None:
        """
        Actually store the value in Redis.
        
        Args:
            key (str): The key to associate the value with.
            value (bytes): The value to store.
        """
        self._client.set(key, value)

    def _delete(self, key: str) -> None:
        """
        Actually delete the key from Redis.
        
        Args:
            key (str): The key to delete.
        """
        self._client.delete(key)

    def prepare_key(self, key: str) -> str:
        """
        Prepare and convert the key to a consistent format (string).
        
        Args:
            key (str): The key to convert.
        
        Returns:
            str: The converted key.
        """
        return str(key)
    
    def close(self) -> None:
        """
        Close the connection to Redis.
        """
        self._client.close()
    
    @property
    def closed(self) -> bool:
        """
        Check if the connection to Redis is closed.
        
        Returns:
            bool: True if the connection is closed, False otherwise.
        """
        try:
            self._client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False

class PlyvelStorage(BytesStorageBase):

    def __init__(self, db_path: str, create_if_missing: bool = True):
        """
        Initialize a PlyvelStorage object with the given database path.
        Hint: If you want to store DB in memory, use 'db_path' = '/dev/shm/...' (Linux)

        Args:
            db_path (str): The path to the LevelDB database.
            create_if_missing (bool, optional): Whether to create the database if it does not exist. Defaults to True.

        Raises:
            ModuleNotFoundError: If the 'plyvel' module is not installed.
            StorageOperationError: If the connection to the database fails.
        """
        if not plyvel:
            raise ModuleNotFoundError("Plyvel addon is not installed. Install it with 'pip install pygzctfapi[plyvel]'.")
        try:
            self._db = plyvel.DB(db_path, create_if_missing=create_if_missing)
            self._lock = Lock()  # To synchronize write operations
        except Exception as e:
            raise exceptions.StorageOperationError("Failed to connect to Plyvel database: {exception}.", exception=e)

    def _get(self, key: bytes) -> Optional[bytes]:
        """
        Actually get the value from Plyvel (LevelDB).

        Args:
            key (bytes): The key to retrieve the value for.

        Returns:
            Optional[bytes]: The value associated with the key, or None if the key does not exist.
        """
        return self._db.get(key)

    def _put(self, key: bytes, value: bytes) -> None:
        """
        Actually store the value in Plyvel (LevelDB).

        Args:
            key (bytes): The key to associate the value with.
            value (bytes): The value to store.
        """
        with self._lock:
            self._db.put(key, value)

    def _delete(self, key: bytes) -> None:
        """
        Actually delete the key from Plyvel (LevelDB).

        Args:
            key (bytes): The key to delete.
        """
        with self._lock:
            self._db.delete(key)

    def prepare_key(self, key: str) -> bytes:
        """
        Prepare and convert the key to a consistent format (bytes).

        Args:
            key (str): The key to convert.

        Returns:
            bytes: The converted key.
        """
        return key.encode('utf-8')
    
    def close(self) -> None:
        """
        Close the connection to the database.
        """
        self._db.close()
    
    @property
    def closed(self) -> bool:
        """
        Check if the connection to the database is closed.

        Returns:
            bool: True if the connection is closed, False otherwise.
        """
        return self._db.closed

class InMemoryStorage:
    
    def __init__(self):
        """
        Initialize an in-memory storage using a Python dictionary.
        """
        self._store = {}
        self._lock = Lock()
    
    def _get(self, key: Any) -> Optional[Any]:
        """
        Get the value from the in-memory storage. Left for backward compatibility.
        """
        return self.get(key)
    
    def _put(self, key: Any, value: Any) -> None:
        """
        Store the value in the in-memory storage. Left for backward compatibility.
        """
        self.put(key, value)
    
    def _delete(self, key: Any) -> None:
        """
        Delete the key from the in-memory storage. Left for backward compatibility.
        """
        self.delete(key)

    def get(self, key: Any) -> Optional[Any]:
        """
        Get the value from the in-memory storage.

        Args:
            key (Any): The key to retrieve the value for.

        Returns:
            Optional[Any]: The value associated with the key, or None if the key does not exist.
        """
        with self._lock:
            return self._store.get(key, None)

    def put(self, key: Any, value: Any) -> None:
        """
        Store the value in the in-memory storage.

        Args:
            key (Any): The key to associate the value with.
            value (Any): The value to store.
        """
        with self._lock:
            self._store[key] = deepcopy(value)

    def delete(self, key: Any) -> None:
        """
        Delete the key from the in-memory storage.

        Args:
            key (Any): The key to delete.
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
    
    def exists(self, key: Any) -> bool:
        """
        Check if the key exists in the in-memory storage.

        Args:
            key (Any): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        with self._lock:
            return key in self._store

    def prepare_key(self, key: Any) -> Any:
        """
        Just return the key as-is. This is a no-op for in-memory storage.
        """
        return key

    def prepare_value(self, value: Any) -> Any:
        """
        Just return the value as-is. This is a no-op for in-memory storage.
        """
        return value
    
    def close(self) -> None:
        """
        Close the in-memory storage. Simply clears the store.
        """
        with self._lock:
            self._store.clear()
    
    @property
    def closed(self) -> bool:
        """
        Check if the in-memory storage is closed. Simply checks if the store is empty.

        Returns:
            bool: True if the storage is closed, False otherwise.
        """
        with self._lock:
            return not bool(self._store)