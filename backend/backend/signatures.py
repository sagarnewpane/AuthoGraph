"""Public attribution checks never look up private images or account email addresses."""
import hashlib
import hmac
import struct

from django.core import signing

from .scripts.steg import TextSteganography

PREFIX = 'AGS1:'
SALT = 'authograph.hidden-attribution.v1'


def pixel_digest(image):
    normalized = image.copy()
    normalized[:, :, 0] &= 254
    height, width, channels = normalized.shape
    return hashlib.sha256(struct.pack('>III', width, height, channels) + normalized.tobytes()).hexdigest()


def encode_signature(image, user_image, message):
    record = {'version': 1, 'creator': user_image.user.username, 'image': user_image.pk,
              'message': message, 'pixels': pixel_digest(image)}
    return PREFIX + signing.Signer(salt=SALT).sign_object(record, compress=True)


def inspect_signature(image):
    try:
        payload = TextSteganography().extract_message(image)
    except (ValueError, UnicodeDecodeError) as error:
        corrupted = 'altered' in str(error) or 'Invalid' in str(error) or isinstance(error, UnicodeDecodeError)
        return {'status': 'invalid' if corrupted else 'not_found', 'creator': None, 'signature': None}
    if not payload.startswith(PREFIX):
        return {'status': 'unsigned', 'creator': None, 'signature': payload}
    try:
        record = signing.Signer(salt=SALT).unsign_object(payload[len(PREFIX):])
        if (not isinstance(record, dict) or record.get('version') != 1
                or not isinstance(record.get('creator'), str) or not 1 <= len(record['creator']) <= 150
                or not isinstance(record.get('message'), str) or len(record['message']) > 255
                or not isinstance(record.get('pixels'), str) or len(record['pixels']) != 64
                or any(c not in '0123456789abcdef' for c in record['pixels'])
                or not hmac.compare_digest(record['pixels'], pixel_digest(image))):
            raise ValueError('Invalid image attribution')
    except (signing.BadSignature, ValueError, TypeError, KeyError):
        return {'status': 'invalid', 'creator': None, 'signature': None}
    return {'status': 'verified', 'creator': record['creator'], 'signature': record['message']}
