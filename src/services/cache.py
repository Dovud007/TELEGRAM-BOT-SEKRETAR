import uuid
from typing import Any, Dict

class SimpleCache:
    """
    A simple in-memory cache using a dictionary.
    This is not persistent and will be cleared on bot restart.
    Perfect for storing temporary data for callbacks.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def set(self, value: Any) -> str:
        """
        Stores a value in the cache and returns a unique key.
        :param value: The data to store.
        :return: A unique string key (UUID).
        """
        key = str(uuid.uuid4())
        self._cache[key] = value
        return key

    def get(self, key: str) -> Any | None:
        """
        Retrieves a value from the cache by its key and deletes it.
        Returns None if the key is not found.
        :param key: The unique key.
        :return: The stored data or None.
        """
        return self._cache.pop(key, None)

# Create a single, global instance of the cache to be used by all handlers.
temp_data_cache = SimpleCache()
