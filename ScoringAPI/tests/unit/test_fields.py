import functools
import re
import unittest

from ru.otus.scoring.api import *


class TestObject:
    name = CharField(required=True, nullable=False)
    argument = ArgumentsField(required=True, nullable=False)
    email = EmailField(required=True, nullable=False)
    phone = PhoneField(required=True, nullable=False)
    date = DateField(required=True, nullable=False)
    birthDay = BirthDayField(required=True, nullable=False)
    gender = GenderField(required=True, nullable=False)
    clientIds = ClientIDsField(required=True, nullable=False)


def cases(case_list):
    def decorator(f):
        f._param_cases = case_list
        return f

    return decorator


def sanitize(val):
    return re.sub(r"\W|^(?=\d)", "_", str(val))[:40]


def generate_test_cases(cls):
    for attr in dir(cls):
        if not attr.startswith("test_"):
            continue
        func = getattr(cls, attr)

        if not hasattr(func, "_param_cases"):
            continue
        base_name = attr

        for i, case in enumerate(func._param_cases):
            case_data = case if isinstance(case, tuple) else (case,)

            def make_test_func(func, case_data):
                def test_func(self):
                    return func(self, *case_data)

                return test_func

            case_name = case_data[0].get("real_test_name", None)
            prefix = f"test_{case_name}" if case_name else f"{base_name}_{i}"
            test_name = prefix
            setattr(cls, test_name, make_test_func(func, case_data))
        delattr(cls, base_name)
    return cls


@generate_test_cases
class TestFieldsSuite(unittest.TestCase):

    @cases(
        [
            {
                "name": "test1",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
            },
        ]
    )
    def test_fields_positive(self, data):
        test_object = TestObject()
        test_object.name = data["name"]
        test_object.argument = data["argument"]
        test_object.email = data["email"]
        test_object.phone = data["phone"]
        test_object.date = data["date"]
        test_object.birthDay = data["birthDay"]
        test_object.gender = data["gender"]
        test_object.clientIds = data["clientIds"]
        assert test_object

    @cases(
        [
            {
                "name": 123,
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
                "error_string": "Must be a string",
                "real_test_name": "Wrong name format",
            },
            {
                "name": "name 1",
                "argument": 123,
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
                "error_string": "Must be a dictionary",
                "real_test_name": "Wrong argument format",
            },
            {
                "name": "name 2",
                "argument": {"key": "value"},
                "email": "userexample.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
                "error_string": "Must contain '@'",
                "real_test_name": "Email without @",
            },
            {
                "name": "name 3",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "asd123as",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
                "error_string": "Phone must be digits only",
                "real_test_name": "Phone no digits only",
            },
            {
                "name": "name 4",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "-01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
                "error_string": "Invalid date format, expected DD.MM.YYYY",
                "real_test_name": "Corrupted date format",
            },
            {
                "name": "name 5",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "44.01.2000",
                "gender": 1,
                "clientIds": [1, 2, 3],
                "error_string": "Invalid date format, expected DD.MM.YYYY",
                "real_test_name": "Corrupted birthday format",
            },
            {
                "name": "name 6",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": "male",
                "clientIds": [1, 2, 3],
                "error_string": "Gender must be 0, 1, or 2",
                "real_test_name": "Gender out of waiting values",
            },
            {
                "name": "name 7",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 0,
                "clientIds": ["a", 2, 3],
                "error_string": "All items must be int",
                "real_test_name": "ClientsIds is is list, but not only ints",
            },
            {
                "name": "name 7",
                "argument": {"key": "value"},
                "email": "user@example.com",
                "phone": "71234567890",
                "date": "01.01.2000",
                "birthDay": "01.01.2000",
                "gender": 0,
                "clientIds": 2,
                "error_string": "Must be a list",
                "real_test_name": "ClientsIds must be a list",
            },
        ]
    )
    def test_fields_negative(self, data):
        try:
            test_object = TestObject()
            test_object.name = data["name"]
            test_object.argument = data["argument"]
            test_object.email = data["email"]
            test_object.phone = data["phone"]
            test_object.date = data["date"]
            test_object.birthDay = data["birthDay"]
            test_object.gender = data["gender"]
            test_object.clientIds = data["clientIds"]
            print(test_object)
        except ValueError as e:
            assert data["error_string"] in e.args[0]


@generate_test_cases
class TestRequestsSuite(unittest.TestCase):

    @cases(
        [
            {
                "first_name": "!firstName",
                "last_name": "lastName",
                "email": "user@example.com",
                "phone": "71234567890",
                "birthDay": "01.01.2000",
                "gender": 1,
            },
        ]
    )
    def test_positive_online_score_request(self, data):
        req = OnlineScoreRequest(data)
        req.validate_logic()
        assert req.is_valid()

    @cases(
        [
            {
                "first_name": "firstName",
                "last_name": None,
                "email": "user@example.com",
                "phone": None,
                "birthday": "01.01.2000",
                "gender": None,
            },
        ]
    )
    def test_validate_logic_failed(self, data):
        try:
            req = OnlineScoreRequest(data)
            req.validate_logic()
            assert False
        except ValueError as e:
            assert "At least one pair of fields must be not empty" in str(e)
