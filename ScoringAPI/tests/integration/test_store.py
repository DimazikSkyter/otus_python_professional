import functools
import json
import os
import unittest
from time import sleep, time
from typing import Any

import docker
import hazelcast
import pytest
from ru.otus.scoring.store import *


class TestHazelcastStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        current_dir = os.path.dirname(__file__)
        fixture_path = os.path.join(current_dir, "fixtures", "test_basic.json")
        with open(fixture_path) as f:
            config = json.load(f).get("hazelcast", {})
            cls.TEST_TIMEOUT = config["TEST_TIMEOUT"]
            cls.HAZELCAST_IMAGE = config["HAZELCAST_IMAGE"]
            cls.MAP_NAME = config["MAP_NAME"]

        cls.docker_client = docker.from_env()
        cls.container = cls.docker_client.containers.run(
            cls.HAZELCAST_IMAGE,
            detach=True,
            ports={"5701/tcp": 5701},
            environment={"HZ_CLUSTERNAME": "test"},
            remove=True,
        )
        cls._wait_for_hazelcast()
        cls.hazelcast_client = hazelcast.HazelcastClient(
            cluster_name="test",
            cluster_members=["127.0.0.1:5701"],
            connection_timeout=5.0,
        )

    @classmethod
    def tearDownClass(cls):
        cls.hazelcast_client.shutdown()
        cls.container.stop()

    @classmethod
    def _wait_for_hazelcast(cls, timeout=30):
        start = time()
        while True:
            logs = cls.container.logs().decode()
            if "STARTED" in logs:
                return
            if time() - start > timeout:
                raise TimeoutError("Hazelcast container failed to start")
            sleep(0.5)

    def setUp(self):
        self.store = CacheStore(self.hazelcast_client, self.MAP_NAME)
        self.map = self.hazelcast_client.get_map(self.MAP_NAME).blocking()
        self.map.clear()

    def test_basic_cache_operations(self):
        self.store.cache_set("key1", "value1", duration=0)
        self.assertEqual(self.store.cache_get("key1"), "value1")

    def test_ttl_expiration(self):
        self.store.cache_set("temp", "data", duration=2)
        self.assertEqual(self.store.cache_get("temp"), "data")

        sleep(2.5)
        self.assertIsNone(self.store.cache_get("temp"))

    def test_zero_ttl(self):
        self.store.cache_set("perm", "data", duration=0)
        sleep(1)
        self.assertEqual(self.store.cache_get("perm"), "data")

    def test_non_existing_key(self):
        self.assertIsNone(self.store.cache_get("missing"))


if __name__ == "__main__":
    unittest.main()
