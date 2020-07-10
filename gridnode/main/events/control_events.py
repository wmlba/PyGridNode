import json
from syft.grid.clients.dynamic_fl_client import DynamicFLClient
from syft.codes import RESPONSE_MSG
from syft.grid.authentication.account import AccountCredential
from ..codes import GRID
from flask_login import login_user

from .. import local_worker, hook, sy
from ..auth import authenticated_only, get_session


def get_node_infos(message: dict) -> str:
    """ Returns node id.

        Returns:
            response (str) : Response message containing node id.
    """
    return json.dumps(
        {
            RESPONSE_MSG.NODE_ID: local_worker.id,
            GRID.SYFT_VERSION: sy.version.__version__,
        }
    )


def authentication(message: dict) -> str:
    """ Receive user credentials and performs user authentication.

        Args:
            message (dict) : Dict data structure containing user credentials.
        Returns:
            response (str) : Authentication response message.
    """
    user = get_session().authenticate(message)
    # If it was authenticated
    if user:
        login_user(user)
        return json.dumps(
            {RESPONSE_MSG.SUCCESS: "True", RESPONSE_MSG.NODE_ID: user.worker.id}
        )
    else:
        return json.dumps({RESPONSE_MSG.ERROR: "Invalid username/password!"})


def connect_grid_nodes(message: dict) -> str:
    """ Connect remote grid nodes between each other.

        Args:
            message (dict) :  Dict data structure containing node_id, node address and user credentials(optional).
        Returns:
            response (str) : response message.
    """
    # If found any credential
    credentials = message.get("auth")
    if credentials:
        credentials = AccountCredential(
            username=credentials["username"], password=credentials["password"]
        )

    if message["id"] not in local_worker._known_workers:
        worker = DynamicFLClient(
            hook, address=message["address"], id=message["id"], credential=credentials
        )
    return json.dumps({"status": "Succesfully connected."})


@authenticated_only
def socket_ping(message: dict) -> str:
    """ Ping request to check node's health state. """
    return json.dumps({"alive": "True"})
