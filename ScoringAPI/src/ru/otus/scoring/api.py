#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import datetime
import hashlib
import json
import logging
import re
import sys
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

from ru.otus.scoring.scoring import get_interests, get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
)


class Field(abc.ABC):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.value = None

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            return
        if not self.nullable and value in ("", [], {}, None):
            raise ValueError("Field can't be empty")
        self._validate(value)

    @abc.abstractmethod
    def _validate(self, value):
        pass

    def __set__(self, instance, value):
        self.validate(value)
        self.value = value

    def __get__(self, instance, owner):
        return self.value


class CharField(Field):
    def _validate(self, value):
        if not isinstance(value, str):
            raise ValueError("Must be a string")


class ArgumentsField(Field):
    def _validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Must be a dictionary")


class EmailField(CharField):
    def _validate(self, value):
        super()._validate(value)
        if "@" not in value:
            raise ValueError("Must contain '@'")


class PhoneField(Field):
    def _validate(self, value):
        if isinstance(value, str):
            if not value.isdigit():
                raise ValueError("Phone must be digits only")
            value = int(value)
        if not isinstance(value, int):
            raise ValueError("Must be int")
        if len(str(value)) != 11 or not str(value).startswith("7"):
            raise ValueError("Must start with 7 and be 11 digits")


class DateField(Field):
    def _validate(self, value):
        try:
            datetime.datetime.strptime(value, "%d.%m.%Y")
        except Exception:
            raise ValueError("Invalid date format, expected DD.MM.YYYY")


class BirthDayField(DateField):
    def _validate(self, value):
        super()._validate(value)
        date = datetime.datetime.strptime(value, "%d.%m.%Y")
        if (datetime.datetime.today() - date).days / 365.25 > 70:
            raise ValueError("Birthday must be less than 70 years ago")


class GenderField(Field):
    def _validate(self, value):
        if value not in (0, 1, 2):
            raise ValueError("Gender must be 0, 1, or 2")


class ClientIDsField(Field):
    def _validate(self, value):
        if not isinstance(value, list):
            raise ValueError("Must be a list")
        if not value:
            raise ValueError("List must not be empty")
        if not all(isinstance(i, int) for i in value):
            raise ValueError("All items must be int")


class MetaRequest(type):
    def __new__(msc, name, bases, attrs):
        fields = {}
        for key, val in attrs.items():
            if isinstance(val, Field):
                fields[key] = val
        cls = super().__new__(msc, name, bases, attrs)
        cls._fields = fields
        return cls


class BaseRequest(metaclass=MetaRequest):
    def __init__(self, data):
        self.errors = {}
        self.cleaned_data = {}
        for name, field in self._fields.items():
            value = data.get(name)
            try:
                setattr(self, name, value)
                self.cleaned_data[name] = value
            except Exception as e:
                self.errors[name] = str(e)

    def is_valid(self):
        return not self.errors


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate_logic(self):
        pairs = [
            (self.phone, self.email),
            (self.first_name, self.last_name),
            (self.gender, self.birthday),
        ]
        if not any(a is not None and b is not None for a, b in pairs):
            raise ValueError(
                "At least one pair of fields must be not empty: (phone, email), (first_name, last_name), (gender, birthday)"
            )


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + SALT).encode("utf-8")
        ).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    method_request = MethodRequest(request["body"])
    if not method_request.is_valid():
        logging.info("Invalid method request: %s", method_request.errors)
        return method_request.errors, 422

    if not check_auth(method_request):
        logging.info("Forbidden for user: %s", method_request.login)
        return "Forbidden", 403

    arguments = method_request.cleaned_data["arguments"] or {}
    ctx["has"] = []

    if method_request.cleaned_data["method"] == "online_score":
        req = OnlineScoreRequest(arguments)
        if not req.is_valid():
            logging.info("Invalid online_score arguments: %s", req.errors)
            return req.errors, 422
        try:
            req.validate_logic()
        except ValueError as e:
            logging.info("Logic validation error: %s", str(e))
            return {"error": str(e)}, 422
        ctx["has"] = [k for k in req.cleaned_data if req.cleaned_data[k] is not None]
        score = 42 if method_request.is_admin else get_score(store, **req.cleaned_data)
        logging.info("Score calculated: %s", score)
        return {"score": score}, 200

    elif method_request.cleaned_data["method"] == "clients_interests":
        req = ClientsInterestsRequest(arguments)
        if not req.is_valid():
            logging.info("Invalid clients_interests arguments: %s", req.errors)
            return req.errors, 422
        client_ids = req.cleaned_data["client_ids"]
        ctx["nclients"] = len(client_ids)
        interests = {str(cid): get_interests(store, cid) for cid in client_ids}
        logging.info("Interests returned for %d clients", len(client_ids))
        return interests, 200

    else:
        logging.info("Unknown method: %s", method_request.cleaned_data["method"])
        return "Unknown method", 422


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
