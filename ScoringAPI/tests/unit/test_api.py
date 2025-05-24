import datetime
import functools
import hashlib
import http.client
import json
import os
import sys
import threading
import unittest
from http.server import HTTPServer
from unittest.mock import patch

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src"))
)
from ru.otus.scoring import api


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)

        return wrapper

    return decorator


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}

        class MockStore:
            def cache_get(self, key):
                return 5

            def cache_set(self, key, value, ttl=None):
                pass

        self.settings = MockStore()

    def get_response(self, request):
        return api.method_handler(
            {"body": request, "headers": self.headers}, self.context, self.settings
        )

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode(
                    "utf-8"
                )
            ).hexdigest()
        else:
            msg = (
                request.get("account", "") + request.get("login", "") + api.SALT
            ).encode("utf-8")
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases(
        [
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "sdd",
                "arguments": {},
            },
            {
                "account": "horns&hoofs",
                "login": "admin",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
        ]
    )
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases(
        [
            {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
            {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
            {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
        ]
    )
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases(
        [
            {},
            {"phone": "79175002040"},
            {"phone": "89175002040", "email": "stupnikov@otus.ru"},
            {"phone": "79175002040", "email": "stupnikovotus.ru"},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.1890",
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "XXX",
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": 1,
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": "s",
                "last_name": 2,
            },
            {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
            {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
        ]
    )
    def test_invalid_score_request(self, arguments):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases(
        [
            {"phone": "79175002040", "email": "stupnikov@otus.ru"},
            {
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": "a",
                "last_name": "b",
            },
            {"gender": 0, "birthday": "01.01.2000"},
            {"gender": 2, "birthday": "01.01.2000"},
            {"first_name": "a", "last_name": "b"},
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": "a",
                "last_name": "b",
            },
        ]
    )
    def test_ok_score_request(self, arguments):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)

        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)

        expected_keys = [k for k, v in arguments.items() if v is not None]
        self.assertEqual(sorted(self.context["has"]), sorted(expected_keys))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {
            "account": "horns&hoofs",
            "login": "admin",
            "method": "online_score",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases(
        [
            {},
            {"date": "20.07.2017"},
            {"client_ids": [], "date": "20.07.2017"},
            {"client_ids": {1: 2}, "date": "20.07.2017"},
            {"client_ids": ["1", "2"], "date": "20.07.2017"},
            {"client_ids": [1, 2], "date": "XXX"},
        ]
    )
    def test_invalid_interests_request(self, arguments):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases(
        [
            {
                "client_ids": [1, 2, 3],
                "date": datetime.datetime.today().strftime("%d.%m.%Y"),
            },
            {"client_ids": [1, 2], "date": "19.07.2017"},
            {"client_ids": [0]},
        ]
    )
    @patch("ru.otus.scoring.api.get_interests", lambda store, cid: ["cars", "books"])
    def test_ok_interests_request(self, arguments):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(
            all(
                v
                and isinstance(v, list)
                and all(isinstance(i, (bytes, str)) for i in v)
                for v in response.values()
            )
        )
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))

    @cases(
        [
            {
                "body": {
                    "account": "horns&hoofs",
                    "login": "h&f",
                    "method": "online_score",
                    "token": hashlib.sha512(
                        "horns&hoofsh&fOtus".encode("utf-8")
                    ).hexdigest(),
                    "arguments": {"phone": "79175002011", "email": "user@example.com"},
                },
                "expected_code": 200,
                "expect_score": True,
            },
            {
                "body": {
                    "account": "horns&hoofs",
                    "login": "admin",
                    "method": "online_score",
                    "token": hashlib.sha512(
                        (
                            datetime.datetime.now().strftime("%Y%m%d%H")
                            + api.ADMIN_SALT
                        ).encode("utf-8")
                    ).hexdigest(),
                    "arguments": {"phone": "79175002012", "email": "admin@example.com"},
                },
                "expected_code": 200,
                "expect_score": True,
            },
            {
                "body": {
                    "account": "horns&hoofs",
                    "login": "h&f",
                    "method": "online_score",
                    "token": "badtoken",
                    "arguments": {"phone": "79175002013", "email": "user@example.com"},
                },
                "expected_code": 403,
                "expect_score": False,
            },
        ]
    )
    def test_do_POST(self, case):
        class MockStore:
            def cache_get(self, key):
                return 5

            def cache_set(self, key, value, ttl=None):
                pass

        handler_class = type(
            "CustomHandler", (api.MainHTTPHandler,), {"store": MockStore()}
        )

        server = HTTPServer(("localhost", 0), handler_class)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        try:
            conn = http.client.HTTPConnection("localhost", port)
            conn.request(
                "POST",
                "/method",
                body=json.dumps(case["body"]),
                headers={"Content-Type": "application/json"},
            )
            response = conn.getresponse()
            data = json.loads(response.read())

            self.assertEqual(response.status, case["expected_code"])
            if case["expect_score"]:
                self.assertIn("score", data.get("response", {}))
            else:
                self.assertNotIn("score", data.get("response", {}))
        finally:
            server.shutdown()
            server.server_close()

    @cases(
        [
            {
                "account": "any",
                "login": api.ADMIN_LOGIN,
                "token": hashlib.sha512(
                    (
                        datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
                    ).encode("utf-8")
                ).hexdigest(),
                "expected": True,
            },
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "token": hashlib.sha512(
                    "horns&hoofsh&fOtus".encode("utf-8")
                ).hexdigest(),
                "expected": True,
            },
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "token": "invalidtoken",
                "expected": False,
            },
        ]
    )
    def test_check_auth(self, case):
        request = api.MethodRequest(
            {
                "account": case["account"],
                "login": case["login"],
                "token": case["token"],
                "arguments": {},
                "method": "online_score",
            }
        )
        self.assertEqual(api.check_auth(request), case["expected"])


if __name__ == "__main__":
    unittest.main()
