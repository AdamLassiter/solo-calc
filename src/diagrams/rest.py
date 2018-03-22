#! /usr/bin/env python3

from datetime import timedelta
from functools import update_wrapper
from json import dumps
from types import MethodType

from flask import Flask, request, Response, make_response, current_app
from flask_restful import Api, Resource

from diagrams import Diagram
from tests import big_diagram

app = Flask(__name__)
api = Api(app)


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper
api.route = MethodType(api_route, api)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods
        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


diagram = big_diagram()


@api.route('/')
class ReduceRequestHandler(Resource):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


    @crossdomain(origin='*')
    def get(self) -> Response:
        global diagram
        reduce = int(request.args.get('reduce'))
        if reduce:
            diagram = diagram.reduce()
        return make_response(dumps(diagram.json), 200)


    @crossdomain(origin='*')
    def put(self):
        global diagram
        diagram = Diagram.from_json(request.json)
        return make_response('ok', 200)



if __name__ == '__main__':
    from os import getenv
    app.run(debug=False, host=getenv('IP', '0.0.0.0'), port=int(getenv('PORT', 8001)))
