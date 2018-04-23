import os
import functools

CURRENT_DIR = functools.partial(os.path.join,
                                os.path.abspath(os.path.dirname(__file__)))

SERVER_PORT = 50051

PROTO_BUILD_PATH = CURRENT_DIR('./py_proto_build/')

PARAMETER_REQUEST = 'request_type'
PARAMETER_RESPONSE = 'response_type'

RPC_TYPE = {
    '/kvscan.KVService/find': {PARAMETER_REQUEST: 'KVPackage', PARAMETER_RESPONSE: 'KVPackage'},
    '/kvscan.KVService/next': {PARAMETER_REQUEST: 'KVPackage', PARAMETER_RESPONSE: 'KVPackage'}
}
