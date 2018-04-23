import os
import sys
import struct
import logging
import myconfig
import importlib


def proto_instance(rpc_path, parameter_type):
    """ get a protobuf instance """
    type_info = myconfig.RPC_TYPE.get(rpc_path, None)[parameter_type]
    if not type_info:
        return None

    # add compiled python protobuf file
    py_proto_path = os.path.abspath(myconfig.PROTO_BUILD_PATH)
    sys.path.insert(1, py_proto_path)
    for py_file in filter(lambda f_name: f_name.endswith('.py'), os.listdir(py_proto_path)):
        proto_pack = importlib.import_module(py_file.split('.')[0])
        if type_info in proto_pack.__dict__:
            return getattr(proto_pack, type_info)()
    else:
        return None


def parse_rpc_data_frame(lps_data, rpc_path, parameter_type, compression):
    """ parse lps data """
    result = []
    while lps_data:
        compress_flags, data_len = struct.unpack('!BI', lps_data[:5])
        proto_data = lps_data[5:5+data_len]
        lps_data = lps_data[5+data_len:]
        if compress_flags != 0:
            logging.warning('not support compression, %s' % compression)
            result.append(lps_data)
            continue
            
        proto_obj = proto_instance(rpc_path, parameter_type)
        if not proto_obj:
            logging.warning('not find rpc %s' % rpc_path)
            result.append(lps_data)
        else:
            proto_obj.ParseFromString(proto_data)
            result.append(proto_obj)

    return result


        
        
        
        
        
    
