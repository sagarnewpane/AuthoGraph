"""Lossless PNG attribution payload with a versioned header and corruption check.

This is fragile steganography, not a watermark resistant to transformations.
"""
import struct
import zlib
import cv2
import numpy as np

MAGIC = b'AGH1'
HEADER_SIZE = 12


class TextSteganography:
    def embed_message(self, image_path, message):
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError('Could not read image')
        return self.embed_array(image, message)

    def embed_array(self, image, message):
        payload = message.encode('utf-8')
        if len(payload) > 4096:
            raise ValueError('Message is too long')
        encoded = MAGIC + struct.pack('>II', len(payload), zlib.crc32(payload)) + payload
        bits = np.unpackbits(np.frombuffer(encoded, dtype=np.uint8))
        result = image.copy()
        # Modify only the blue channel; alpha and dimensions are preserved.
        channel = result[:, :, 0].copy().reshape(-1)
        if bits.size > channel.size:
            raise ValueError('Image is too small for this hidden message')
        channel[:bits.size] = (channel[:bits.size] & 254) | bits
        result[:, :, 0] = channel.reshape(image.shape[:2])
        return result

    def extract_message(self, image):
        channel = image[:, :, 0].reshape(-1)
        if channel.size < HEADER_SIZE * 8:
            raise ValueError('No hidden message found')
        header = np.packbits(channel[:HEADER_SIZE * 8] & 1).tobytes()
        if header[:4] != MAGIC:
            raise ValueError('No supported hidden message found')
        length, checksum = struct.unpack('>II', header[4:])
        end = (HEADER_SIZE + length) * 8
        if length > 4096 or end > channel.size:
            raise ValueError('Invalid hidden message length')
        payload = np.packbits(channel[HEADER_SIZE * 8:end] & 1).tobytes()
        if zlib.crc32(payload) != checksum:
            raise ValueError('The hidden message has been altered')
        return payload.decode('utf-8')
