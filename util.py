import base64

def get_bit(a_num, mask):
    """ idx from 1 """
    return bool(a_num &  mask)

def base64_decode(base64_str):
    """ base64 decode.   str -> bytes """
    base64_bytes = base64_str.replace('-', '+').replace('_', '/').encode('utf-8')
    if (len(base64_bytes) % 4) != 0:
        base64_bytes += b'=' * (4 - (len(base64_bytes) % 4))

    return base64.decodebytes(base64_bytes)

def header_base64_decode(header_list):
    """ base64 decode for header name with -bin """
    def header_item_convert(item):
        if item[0].endswith('-bin'):
            return (item[0], base64_decode(item[1]).decode('utf-8'))
        
        return item
    return list(map(header_item_convert, header_list))
