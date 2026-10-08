"""Image processing stays in-process and never silently drops requested protection."""
import io
import json
import math
import secrets
from pathlib import Path
from datetime import timedelta

import cv2
import numpy as np
import pyotp
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps, PngImagePlugin
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from .models import OTPSecret, WatermarkSettings, InvisibleWatermarkSettings, AIProtectionSettings
from .scripts.steg import TextSteganography
from .signatures import encode_signature


class OTPHandler:
    @staticmethod
    def generate_and_store_otp(image_access, email):
        email = email.strip().lower()
        OTPSecret.objects.filter(image_access=image_access, email=email, is_used=False).update(is_used=True)
        secret = pyotp.random_base32()
        OTPSecret.objects.create(image_access=image_access, email=email, secret=secret)
        return pyotp.HOTP(secret).at(0)

    @staticmethod
    def verify_otp(image_access, email, provided_otp):
        with transaction.atomic():
            record = OTPSecret.objects.select_for_update().filter(
                image_access=image_access, email=email.strip().lower(), is_used=False
            ).order_by('-created_at').first()
            if not record or not record.is_valid() or record.attempts >= 5:
                return False
            record.attempts += 1
            valid = pyotp.HOTP(record.secret).verify(str(provided_otp), 0)
            record.is_used = valid or record.attempts >= 5
            record.save(update_fields=['attempts', 'is_used'])
            return valid


class ProtectionChain:
    @staticmethod
    def render(user_image, features, watermark_settings=None):
        with Image.open(io.BytesIO(user_image.get_decrypted_bytes())) as source:
            image = ImageOps.exif_transpose(source).convert('RGBA')
        if features.get('ai_protection'):
            ai = AIProtectionSettings.objects.get(user_image=user_image, enabled=True)
            with ai.protected_image.open('rb') as source:
                image = Image.open(source).convert('RGBA')
        if features.get('watermark'):
            if watermark_settings is None:
                watermark_settings = WatermarkSettings.objects.get(user_image=user_image, enabled=True).settings
            image = ProtectionChain._apply_watermark(image, watermark_settings)
        # Embed last so visible watermark rendering cannot overwrite the hidden payload.
        if features.get('hidden_watermark'):
            hidden = InvisibleWatermarkSettings.objects.get(user_image=user_image, enabled=True)
            image = ProtectionChain._apply_steganography(image, hidden.text, user_image)
        info = PngImagePlugin.PngInfo()
        if features.get('metadata'):
            info.add_text('AuthoGraph', json.dumps(user_image.metadata, ensure_ascii=False))
        # Pillow carries source EXIF/ICC through convert(); only explicitly selected
        # saved metadata may be embedded in a delivered copy.
        image.info.clear()
        output = io.BytesIO()
        image.save(output, format='PNG', pnginfo=info)
        return output.getvalue()

    @staticmethod
    def create_protected_image(user_image, protection_features, access_rule):
        data = ProtectionChain.render(user_image, protection_features)
        old_name = access_rule.protected_image.name
        access_rule.protected_image.save(f'{secrets.token_hex(16)}.png', ContentFile(data), save=False)
        access_rule.save(update_fields=['protected_image'])
        if old_name:
            storage = access_rule.protected_image.storage
            transaction.on_commit(lambda: storage.delete(old_name))
        return access_rule.protected_image

    @staticmethod
    def _apply_watermark(image, options):
        image = image.convert('RGBA')
        width, height = image.size
        size = int(options.get('fontSize', 32))
        try:
            font = ImageFont.truetype(str(Path(__file__).parent / 'assets' / 'watermark.ttf'), size)
        except OSError:
            font = ImageFont.load_default(size=size)
        text = options.get('text', 'Protected preview')
        box = font.getbbox(text)
        stamp = Image.new('RGBA', (max(1, box[2] - box[0] + 24), max(1, box[3] - box[1] + 24)))
        color = ImageColor.getrgb(options.get('color', '#ffffff'))
        alpha = round(float(options.get('opacity', 45)) * 2.55)
        ImageDraw.Draw(stamp).text((12-box[0], 12-box[1]), text, font=font, fill=(*color, alpha))
        stamp = stamp.rotate(float(options.get('rotation', -30)), expand=True, resample=Image.Resampling.BICUBIC)
        layer = Image.new('RGBA', image.size)
        pattern = options.get('pattern', 'tiled')
        offset_x = int(options.get('horizontalOffset', 0))
        offset_y = int(options.get('verticalOffset', 0))
        if pattern == 'tiled':
            gap = max(20, int(options.get('spacing', 80)))
            for y in range(-stamp.height, height + stamp.height, stamp.height + gap):
                for x in range(-stamp.width, width + stamp.width, stamp.width + gap):
                    layer.alpha_composite(stamp, (x + offset_x, y + offset_y))
        else:
            padding = min(50, width // 4, height // 4)
            if pattern == 'diagonal':
                positions = [(padding + (width - 2 * padding) * i / 4,
                              padding + (height - 2 * padding) * i / 4) for i in range(5)]
            elif pattern == 'corners':
                positions = [(padding, padding), (width-padding, padding),
                             (padding, height-padding), (width-padding, height-padding)]
            elif pattern == 'grid':
                gap = max(20, int(options.get('spacing', 80)))
                positions = ((x, y) for y in range(padding, height-padding, stamp.height + gap)
                             for x in range(padding, width-padding, stamp.width + gap))
            else:
                positions = [(width / 2, height / 2)]
            for x, y in positions:
                layer.alpha_composite(stamp, (round(x - stamp.width / 2) + offset_x,
                                             round(y - stamp.height / 2) + offset_y))
        return Image.alpha_composite(image, layer)

    @staticmethod
    def _apply_steganography(image, message, user_image=None):
        source = np.array(image.convert('RGBA'))
        bgra = cv2.cvtColor(source, cv2.COLOR_RGBA2BGRA)
        if user_image is not None:
            message = encode_signature(bgra, user_image, message)
        result = TextSteganography().embed_array(bgra, message)
        return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGRA2RGBA))


class SimpleLocationCollector:
    @staticmethod
    def get_location_data(request):
        # Do not trust caller-controlled forwarded headers or send viewer IPs to third parties.
        return {'ip_address': request.META.get('REMOTE_ADDR'), 'country': None, 'region': None, 'city': None}
