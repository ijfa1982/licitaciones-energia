"""Sustituto mínimo del SDK de Apify para probar main() sin conexión."""
import logging


class _KVS:
    def __init__(self, store):
        self.store = store

    async def get_value(self, key):
        return self.store.get(key)

    async def set_value(self, key, value):
        self.store[key] = value


class _Actor:
    def __init__(self):
        self.input = {}
        self.dataset = []
        self.kvs = {}
        self.status = None
        self.log = logging.getLogger("actor")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get_input(self):
        return self.input

    async def push_data(self, data):
        self.dataset.extend(data if isinstance(data, list) else [data])

    async def open_key_value_store(self, name=None):
        return _KVS(self.kvs.setdefault(name, {}))

    async def set_status_message(self, msg):
        self.status = msg


Actor = _Actor()
