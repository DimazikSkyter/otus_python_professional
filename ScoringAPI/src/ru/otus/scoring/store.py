from typing import Generic, Protocol, TypeVar

K = TypeVar("K", contravariant=True)
V = TypeVar("V")


class Store(Protocol[K, V]):
    def cache_get(self, key: K) -> V:
        """Get data from cache"""
        pass

    def get(self, key: K) -> V:
        """Same as cache get"""
        pass

    def cache_set(self, key: K, value: V, duration: int):
        """Set value to cache for duration"""
        pass


class CacheStore(Store[K, V], Generic[K, V]):

    def __init__(self, client, map_name: str):
        self.client = client
        self.map_name = map_name

    def cache_get(self, key: K) -> V:
        return self.client.get_map(self.map_name).blocking().get(key)

    def get(self, key: K) -> V:
        return self.cache_get(key)

    def cache_set(self, key: K, value: V, duration: int) -> None:
        self.client.get_map(self.map_name).put(key, value, ttl=duration)
