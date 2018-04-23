NETWORK_BYTEORDER = 'big'

HTTP2_CLIENT_PREFACE = b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n';

#  ---------------------- frame type -----------------
FRAME_TYPE_DATA          =  0x0
FRAME_TYPE_HEADERS       =  0x1
FRAME_TYPE_PRIORITY      =  0x2
FRAME_TYPE_RST_STREAM    =  0x3
FRAME_TYPE_SETTINGS      =  0x4
FRAME_TYPE_PUSH_PROMISE  =  0x5
FRAME_TYPE_PING          =  0x6
FRAME_TYPE_GOAWAY        =  0x7
FRAME_TYPE_WINDOW_UPDATE =  0x8
FRAME_TYPE_CONTINUATION  =  0x9


#  ------------- header type frame flags ----------
HEADER_FLAG_END_STREAM = 0x1
HEADER_FLAG_END_HEADER = 0x4
HEADER_FLAG_PADDED = 0x8
HEADER_FLAG_PRIORITY = 0x20


# ----------- data type frame flags ------------
DATA_FLAG_END_STREAM = 0x1
DATA_FLAG_PADDED = 0x8


# ------------ http2 header name ---------------
GRPC_MESSAGE_ENCODING = 'message-encoding'



# --------- setting type(in setting frame) map to description string ---------
SETTING_TYPE_STR = {
    0x1: 'HEADER_TABLE_SIZE',
    0x2: 'ENABLE_PUSH',
    0x3: 'MAX_CONCURRENT_STREAMS',
    0x4: 'INITIAL_WINDOW_SIZE',
    0x5: 'MAX_FRAME_SIZE',
    0x6: 'MAX_HEADER_LIST_SIZE ',
}

# --------------- frame type map to description string -------------
FRAME_TYPE_STR = {
    0x0 : 'DATA', 
    0x1 : 'HEADERS',
    0x2 : 'PRIORITY',
    0x3 : 'RST_STREAM',
    0x4 : 'SETTINGS',
    0x5 : 'PUSH_PROMISE',
    0x6 : 'PING',
    0x7 : 'GOAWAY',
    0x8 : 'WINDOW_UPDATE',
    0x9 : 'CONTINUATION',
}



# ------------- frame direction defniation ------------------
FRAME_DIR_REQUEST = 1
FRAME_DIR_RESPONSE = 2



# ------------- stream status -----------
STREAM_IDLE = 1
STREAM_OPEN = 2
STREAM_CLOSE = 3

