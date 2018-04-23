import logging
import myconfig
import textwrap
import pprint
import proto_util
import util
from util import get_bit
from constant import *

class HTTP2Stream(object):
    def __init__(self, stream_id):
        self._stream_id = stream_id
        # split stream status into two directional status.
        self._stream_request_dir_status = STREAM_IDLE
        self._stream_response_dir_status = STREAM_IDLE

        # server recved data, means data recved in request direction
        self._server_recv_header = bytes()
        self._server_recv_data = bytes()

        # client recved data, means data recved in response direction
        self._client_recv_header = bytes()
        self._client_recv_data = bytes()
        self._client_recv_tailer_header = bytes()

    def dump_stream(self, req_hpack_decoder, resp_hpack_decoder):
        """ dump whole stream """
        print('------------------------ stream %s: dump ------------------------' % (self._stream_id))
        self._dump_request(req_hpack_decoder)
        assert(self.__req_path)
        self._dump_response(resp_hpack_decoder)
        print('------------------------ stream %s: dump end ------------------------' % (self._stream_id))

    def _dump_request(self, hpack_decoder):
        """ dump request in a completed stream """
        assert(self.stream_done())

        # get request header.
        header_list = hpack_decoder.decode(self._server_recv_header)
        req_header = dict(util.header_base64_decode(header_list))
        message_encoding = req_header.get(GRPC_MESSAGE_ENCODING, None)

        # get request data info.
        req_data = None
        if self._server_recv_data:
            req_data = proto_util.parse_rpc_data_frame(
                self._server_recv_data,
                req_header[':path'],
                myconfig.PARAMETER_REQUEST,
                message_encoding
            )
        self.__req_path = req_header[':path']

        print('request header: ')
        print(textwrap.indent(pprint.pformat(req_header), ' '*4))
        print('request data(LPS parse in protobuf): ')
        for lps in req_data:
            print(textwrap.indent(str(lps.__class__), ' '*4))
            print(textwrap.indent(str(lps), ' '*8))

    def _dump_response(self, hpack_decoder):
        """ dump response in a completed stream """
        assert(self.stream_done())

        # ger response
        resp_header = None
        message_encoding = None
        if self._client_recv_header:
            header_list = hpack_decoder.decode(self._client_recv_header)
            resp_header = dict(header_list)
            message_encoding = resp_header.get(GRPC_MESSAGE_ENCODING, None)

        resp_data = None
        if self._client_recv_data:
            resp_data = proto_util.parse_rpc_data_frame(
                self._client_recv_data,
                self.__req_path,
                myconfig.PARAMETER_RESPONSE,
                message_encoding
            )

        header_list = hpack_decoder.decode(self._client_recv_tailer_header)
        resp_tailer_header = dict(util.header_base64_decode(header_list))
        print('response header: ')
        print(textwrap.indent(pprint.pformat(resp_header), ' '*4))
        print('response tailer: ')
        print(textwrap.indent(pprint.pformat(resp_tailer_header), ' '*4))
        print('response data(parse in protobuf): ')
        for lps in resp_data:
            print(textwrap.indent(str(lps.__class__), ' '*4))
            print(textwrap.indent(str(lps), ' '*8))
        
    def stream_done(self):
        return (self._stream_request_dir_status == STREAM_CLOSE
                and self._stream_response_dir_status == STREAM_CLOSE)

    def _handle_stream_close_flag(self, is_close, frame_direction):
        """ handle stream close action. """

        if frame_direction == FRAME_DIR_REQUEST:
            assert(self._stream_request_dir_status == STREAM_OPEN)
            if is_close:
                self._stream_request_dir_status = STREAM_CLOSE
        elif frame_direction == FRAME_DIR_RESPONSE:
            assert(self._stream_response_dir_status == STREAM_OPEN)
            if is_close:
                self._stream_response_dir_status = STREAM_CLOSE

    def _parse_header_frame(self, header_frame, frame_direction):
        frame_flags = header_frame.frame_flags
        assert(not get_bit(frame_flags, HEADER_FLAG_PADDED)) # not support padded
        assert(not get_bit(frame_flags, HEADER_FLAG_PRIORITY)) # not support priority

        # first recv a header, stream status change to open.
        if (self._stream_request_dir_status == STREAM_IDLE
            and self._stream_response_dir_status == STREAM_IDLE):
            self._stream_request_dir_status = STREAM_OPEN
            self._stream_response_dir_status = STREAM_OPEN

        end_of_header = get_bit(frame_flags, HEADER_FLAG_END_HEADER)
        assert(end_of_header) # not support CONTINUATION frame, means only one header frame.

        # save request or response header block.
        if frame_direction == FRAME_DIR_REQUEST:
            # if already have header, this header block must be tailer header.
            if self._server_recv_header:
                raise Exception('multiple header frame in request direction.')
            else:
                self._server_recv_header = header_frame.frame_payload
        elif frame_direction == FRAME_DIR_RESPONSE:
            if self._client_recv_header:
                assert(not self._client_recv_tailer_header)
                self._client_recv_tailer_header = header_frame.frame_payload
            else:
                self._client_recv_header = header_frame.frame_payload
        
        end_of_stream = get_bit(frame_flags, HEADER_FLAG_END_STREAM)
        self._handle_stream_close_flag(end_of_stream, frame_direction)

    def _parse_data_frame(self, data_frame, frame_direction):
        frame_flags = data_frame.frame_flags
        assert(not get_bit(frame_flags, DATA_FLAG_PADDED)) # not support padded.

        # load data.
        if frame_direction == FRAME_DIR_REQUEST:
            assert(self._stream_request_dir_status == STREAM_OPEN)
            self._server_recv_data += data_frame.frame_payload
        elif frame_direction == FRAME_DIR_RESPONSE:
            assert(self._stream_response_dir_status == STREAM_OPEN)
            self._client_recv_data += data_frame.frame_payload
    
        # handle flag setting.
        end_of_stream = get_bit(frame_flags, DATA_FLAG_END_STREAM)
        self._handle_stream_close_flag(end_of_stream, frame_direction)

    def add_frame(self, frame, frame_direction):
        frame_type = frame.frame_type
        frame_flags = frame.frame_flags
        assert(frame_type in {FRAME_TYPE_HEADERS, FRAME_TYPE_DATA, FRAME_TYPE_WINDOW_UPDATE})

        if frame_type == FRAME_TYPE_HEADERS:
            self._parse_header_frame(frame, frame_direction)
        elif frame_type == FRAME_TYPE_DATA:
            self._parse_data_frame(frame, frame_direction)
        elif frame_type == FRAME_TYPE_WINDOW_UPDATE:
            # should record in stream obj?
            logging.info('stream %s add window update frame, direction %s' %
                         (self._stream_id, frame_direction))    
