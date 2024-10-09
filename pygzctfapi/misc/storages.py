import msgpack
import sqlite3
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


class StorageBaseClass(ABC):
    @abstractmethod
    def get(self, key: str) -> Union[Dict, List, str, int, bytes, float]:
        pass

    @abstractmethod
    def set(self, key: str, value: Union[Dict, List, str, int, bytes, float]) -> None:
        pass

    @abstractmethod
    def unset(self, key: str) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass

    @property
    @abstractmethod
    def closed(self) -> bool:
        pass

class ByteStorage(StorageBaseClass, ABC):

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

    def set(self, key: str, value: Union[Dict, List, str, int, bytes, float]) -> None:
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
            self._set(key, value)
        except Exception as e:
            raise exceptions.StorageOperationError(exception=e)
    
    @abstractmethod
    def _set(self, key: Union[str, bytes], value: bytes) -> None:
        """
        Actually store the value in the storage.
        
        Args:
            key (Union[str, bytes]): The key to store the value
            value (bytes): The value to store
        """
        pass

    def unset(self, key: str) -> None:
        """
        Removes an item from the storage based on the provided key.
        
        Args:
            key (str): The key to remove associated value for.

        Raises:
            StorageOperationError: If any error occurs while deleting the key.
        """
        key = self.prepare_key(key)
        try:
            self._unset(key)
        except Exception as e:
            raise exceptions.StorageOperationError(exception=e)
    
    @abstractmethod
    def _unset(self, key: Union[str, bytes]) -> None:
        """
        Actually removes an item from the storage based on the provided key.

        Args:
            key (Union[str, bytes]): The key to remove associated value for.
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

#TODO: Use Redis native datatypes instead of msgpack (should be more efficient)
class RedisStorage(ByteStorage):

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

    def _set(self, key: str, value: bytes) -> None:
        """
        Actually store the value in Redis.
        
        Args:
            key (str): The key to associate the value with.
            value (bytes): The value to store.
        """
        self._client.set(key, value)

    def _unset(self, key: str) -> None:
        """
        Actually removes an item from the Redis storage based on the provided key.

        Args:
            key (str): The key to remove associated value for.
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

class LevelDBStorage(ByteStorage):

    def __init__(self, db_path: str, create_if_missing: bool = True):
        """
        Initialize a PlyvelStorage (LevelDB) object with the given database path.
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

    def _set(self, key: bytes, value: bytes) -> None:
        """
        Actually store the value in Plyvel (LevelDB).

        Args:
            key (bytes): The key to associate the value with.
            value (bytes): The value to store.
        """
        with self._lock:
            self._db.put(key, value)

    def _unset(self, key: bytes) -> None:
        """
        Actually removes an item from the Plyvel (LevelDB) storage based on the provided key.

        Args:
            key (bytes): The key to remove associated value for.
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

class InMemoryStorage(StorageBaseClass):
    
    def __init__(self):
        """
        Initialize an in-memory storage using a Python dictionary.
        """
        self._store = {}
        self._lock = Lock()
        self._is_closed = False

    def get(self, key: Any) -> Optional[Any]:
        """
        Get the value from the in-memory storage.

        Args:
            key (Any): The key to retrieve the value for.

        Returns:
            Optional[Any]: The value associated with the key, or None if the key does not exist.
        """
        if not self._is_closed:
            with self._lock:
                return self._store.get(key, None)
        else:
            raise exceptions.StorageOperationError("Storage is closed.")

    def set(self, key: Any, value: Any) -> None:
        """
        Store the value in the in-memory storage.

        Args:
            key (Any): The key to associate the value with.
            value (Any): The value to store.
        """
        if not self._is_closed:
            with self._lock:
                self._store[key] = deepcopy(value)
        else:
            raise exceptions.StorageOperationError("Storage is closed.")

    def unset(self, key: Any) -> None:
        """
        Removes an item from the in-memory storage based on the provided key.

        Args:
            key (Any): The key to remove associated value for.
        """
        if not self._is_closed:
            with self._lock:
                if key in self._store:
                    del self._store[key]
        else:
            raise exceptions.StorageOperationError("Storage is closed.")
    
    def exists(self, key: Any) -> bool:
        """
        Check if the key exists in the in-memory storage.

        Args:
            key (Any): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        if not self._is_closed:
            with self._lock:
                return key in self._store
        else:
            raise exceptions.StorageOperationError("Storage is closed.")

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
        if not self._is_closed:
            with self._lock:
                self._store.clear()
                self._is_closed = True
                del self._lock
                del self._store
        else:
            raise exceptions.StorageOperationError("Storage is already closed.")
    
    @property
    def closed(self) -> bool:
        """
        Check if the in-memory storage is closed. Simply checks if the store is empty.

        Returns:
            bool: True if the storage is closed, False otherwise.
        """
        return self._is_closed

class SQLiteStorage(ByteStorage):
    
    def __init__(self, db_path: str):
        """
        Initialize an SQLiteStorage object with the given database path.
        Hint: If you want to store DB in memory, use 'db_path' = '/dev/shm/...' (Linux)

        Args:
            db_path (str): The path to the SQLite database file.

        Raises:
            StorageOperationError: If the connection to the database fails.
        """
        try:
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._cursor = self._connection.cursor()
            self._lock = Lock()
            self._initialize_db()
        except Exception as e:
            raise exceptions.StorageOperationError("Failed to connect to SQLite database: {exception}.", exception=e)

    def _initialize_db(self) -> None:
        """
        Initialize the database table for storing key-value pairs.
        """
        with self._lock:
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS storage (
                    key TEXT PRIMARY KEY,
                    value BLOB
                )
            """)
            self._connection.commit()

    def _get(self, key: str) -> Optional[bytes]:
        """
        Actually get the value from the SQLite database.

        Args:
            key (str): The key to retrieve the value for.

        Returns:
            Optional[bytes]: The value associated with the key, or None if the key does not exist.
        """
        with self._lock:
            self._cursor.execute("SELECT value FROM storage WHERE key = ?", (key,))
            row = self._cursor.fetchone()
            return row[0] if row else None

    def _set(self, key: str, value: bytes) -> None:
        """
        Actually store the value in the SQLite database.

        Args:
            key (str): The key to associate the value with.
            value (bytes): The value to store.
        """
        with self._lock:
            self._cursor.execute("REPLACE INTO storage (key, value) VALUES (?, ?)", (key, value))
            self._connection.commit()

    def _unset(self, key: str) -> None:
        """
        Actually removes an item from the SQLite storage based on the provided key.

        Args:
            key (str): The key to remove associated value for.
        """
        with self._lock:
            self._cursor.execute("DELETE FROM storage WHERE key = ?", (key,))
            self._connection.commit()

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
        Close the connection to the database.
        """
        with self._lock:
            self._connection.close()
    
    @property
    def closed(self) -> bool:
        """
        Check if the connection to the database is closed.

        Returns:
            bool: True if the connection is closed, False otherwise.
        """
        try:
            self._connection.execute("SELECT 1")
            return False
        except sqlite3.ProgrammingError:
            return True
    
    def vacuum(self) -> None:
        """
        Perform a VACUUM operation to optimize the database by reclaiming unused space.

        Raises:
            StorageOperationError: If the VACUUM operation fails.
        """
        try:
            with self._lock:
                self._cursor.execute("VACUUM")
                self._connection.commit()
        except Exception as e:
            raise exceptions.StorageOperationError("Failed to vacuum the SQLite database: {exception}.", exception=e)