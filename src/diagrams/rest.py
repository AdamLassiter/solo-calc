#! /usr/bin/env python3

from types import MethodType

from flask import Flask, request, Response, make_response
from flask.json import dumps, loads
from flask_restful import Api, Resource
from flask_cors import CORS

from diagrams import Diagram
from tests import big_diagram

app = Flask(__name__)
CORS(app)
api = Api(app)


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper
api.route = MethodType(api_route, api)



@api.route('/')
class ReduceRequestHandler(Resource):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


    def get(self) -> Response:
        return make_response(dumps(big_diagram().json), 200)


    def post(self):
        diagram = Diagram.from_json(loads(request.data))
        reduction = diagram.reduce()
        return make_response(dumps(reduction.json), 200)



if __name__ == '__main__':
    from os import getenv
    app.run(debug=False, host=getenv('IP', '0.0.0.0'), port=int(getenv('PORT', 8001)))
