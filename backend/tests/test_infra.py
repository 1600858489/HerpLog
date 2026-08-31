import inspect

from backend.app.infra.cache.base import CacheClient
from backend.app.infra.storage.base import FileStorage


def test_cache_contract_is_async_abstract_interface() -> None:
    assert inspect.isabstract(CacheClient)
    assert inspect.iscoroutinefunction(CacheClient.get)
    assert inspect.iscoroutinefunction(CacheClient.set)


def test_storage_contract_is_async_abstract_interface() -> None:
    assert inspect.isabstract(FileStorage)
    assert inspect.iscoroutinefunction(FileStorage.save)
    assert inspect.iscoroutinefunction(FileStorage.get_url)
