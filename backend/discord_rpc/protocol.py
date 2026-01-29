"""Discord RPC wire protocol implementation"""

import json
import struct
from enum import IntEnum
from typing import Tuple, Optional, Dict, Any


class RPCOpcode(IntEnum):
    """Discord RPC message opcodes"""
    HANDSHAKE = 0
    FRAME = 1
    CLOSE = 2
    PING = 3
    PONG = 4


def encode_message(opcode: int, payload: Dict[str, Any]) -> bytes:
    """
    Encode RPC message into Discord wire format.

    Format: [opcode: uint32][length: uint32][payload: JSON]

    Args:
        opcode: Message opcode (see RPCOpcode enum)
        payload: Dictionary to encode as JSON

    Returns:
        Encoded bytes ready to send over socket

    Example:
        >>> encode_message(RPCOpcode.FRAME, {"cmd": "GET_VOICE_SETTINGS"})
        b'\\x01\\x00\\x00\\x00\\x1c\\x00\\x00\\x00{"cmd": "GET_VOICE_SETTINGS"}'
    """
    payload_json = json.dumps(payload).encode('utf-8')
    header = struct.pack('<II', opcode, len(payload_json))
    return header + payload_json


def decode_message(data: bytes, logger=None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """
    Decode RPC message from Discord wire format.

    Args:
        data: Raw bytes received from socket
        logger: Optional logger instance for warnings/errors

    Returns:
        Tuple of (opcode, payload_dict) or (None, None) if invalid

    Example:
        >>> decode_message(b'\\x01\\x00\\x00\\x00\\x02\\x00\\x00\\x00{}')
        (1, {})
    """
    if len(data) < 8:
        if logger:
            logger.warning("Discord Lite: Received incomplete message (< 8 bytes)")
        return None, None

    try:
        opcode, length = struct.unpack('<II', data[:8])
        payload_bytes = data[8:8 + length]

        payload = json.loads(payload_bytes.decode('utf-8'))
        return opcode, payload

    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"Discord Lite: JSON decode error: {e}")
        return opcode if 'opcode' in locals() else None, None
    except Exception as e:
        if logger:
            logger.error(f"Discord Lite: Message decode error: {e}")
        return None, None
