import pytest
import torch
from multiprocessing import Process
import os
import sys
import syft
from syft.grid.clients.dynamic_fl_client import DynamicFLClient
from syft.grid.public_grid import PublicGridNetwork
import gridnode

from . import IDS, PORTS
import time
import requests
import json

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler


@pytest.fixture()
def start_proc():  # pragma: no cover
    """ helper function for spinning up a websocket participant """

    def _start_proc(participant, kwargs):
        def target():
            server = participant(**kwargs)
            server.start()

        p = Process(target=target)
        p.start()
        return p

    return _start_proc


@pytest.fixture(scope="session", autouse=True)
def node_infos():
    return zip(IDS, PORTS)


@pytest.fixture(scope="session", autouse=True)
def init_nodes(node_infos):
    BASEDIR = os.path.dirname(os.path.dirname(__file__))

    def setUpNode(port, node_id):
        from gridnode import create_app as ws_create_app

        app = ws_create_app(node_id, debug=False, database_url=None)
        server = pywsgi.WSGIServer(("", int(port)), app, handler_class=WebSocketHandler)
        server.serve_forever()

    jobs = []
    # Init Grid Nodes
    for (node_id, port) in node_infos:
        p = Process(target=setUpNode, args=(port, node_id))
        p.start()
        jobs.append(p)
    time.sleep(5)

    yield

    for job in jobs:
        job.terminate()


def create_websocket_client(hook, port, id):
    node = DynamicFLClient(hook, "http://localhost:" + port + "/", id=id)
    return node


@pytest.fixture(scope="function")
def connected_node(hook):
    nodes = {}
    for (node_id, port) in zip(IDS, PORTS):
        node = create_websocket_client(hook, port, node_id)
        nodes[node_id] = node

    yield nodes

    for node in nodes:
        nodes[node].close()
        time.sleep(0.1)


@pytest.fixture(scope="session", autouse=True)
def hook():
    hook = syft.TorchHook(torch)
    return hook
