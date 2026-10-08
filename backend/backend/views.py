"""Owner APIs and recipient access. Image bytes always pass an authorization check."""
import io
import json
import logging
from datetime import timedelta
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q, F, Sum, Count
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (UserImage, UserProfile, WatermarkSettings, InvisibleWatermarkSettings,
                     ImageAccess, AccessLog, AccessRequest, AIProtectionSettings, OTPSecret)
from .serializers import (RegisterUserSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, UserImageListSerializer, SpecificImageSerializer,
    UserProfileUpdateSerializer, PasswordChangeSerializer, WatermarkSettingsSerializer,
    InvisibleWatermarkSettingsSerializer, ImageAccessSerializer, AccessVerificationSerializer,
    OTPVerificationSerializer, AccessLogSerializer, AccessRequestSerializer,
    NotificationSettingsSerializer, AccountDeletionSerializer)
from .utils import OTPHandler, ProtectionChain
from .signatures import encode_signature, inspect_signature

logger = logging.getLogger(__name__)


class PublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, ScopedRateThrottle]
    throttle_scope = 'verification'


class VerifyImageSignatureView(PublicView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = 'signature'

    def post(self, request):
        upload = validate_upload(request.FILES.get('image'))
        import cv2
        import numpy as np
        try:
            with Image.open(upload) as source:
                pixels = cv2.cvtColor(np.array(source.convert('RGBA')), cv2.COLOR_RGBA2BGRA)
        except (OSError, ValueError, Image.DecompressionBombError):
            raise ValidationError({'image': 'This image could not be decoded. Choose a valid image file.'})
        result = inspect_signature(pixels)
        return Response(result, headers={'Cache-Control': 'no-store'})


class LoginView(TokenObtainPairView):
    throttle_classes = [AnonRateThrottle, ScopedRateThrottle]
    throttle_scope = 'login'


def owner_image(request, pk):
    return get_object_or_404(UserImage, pk=pk, user=request.user)


def private_response(data, content_type='image/png', filename=None):
    response = HttpResponse(data, content_type=content_type)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    if filename:
        from django.utils.http import content_disposition_header
        response['Content-Disposition'] = content_disposition_header(True, filename)
    return response


def invalidate_renders(image):
    for rule in image.access_rules.all():
        if rule.protected_image:
            name, storage = rule.protected_image.name, rule.protected_image.storage
            rule.protected_image = None
            rule.save(update_fields=['protected_image'])
            transaction.on_commit(lambda name=name, storage=storage: storage.delete(name))


def validate_upload(upload, max_bytes=None):
    if not upload:
        raise ValidationError({'image': 'Choose an image to upload.'})
    if upload.size > (max_bytes or settings.MAX_UPLOAD_BYTES):
        raise ValidationError({'image': 'Image exceeds the upload size limit.'})
    try:
        with Image.open(upload) as source:
            if source.format not in ['JPEG', 'PNG', 'WEBP']:
                raise ValueError()
            if source.width * source.height > settings.MAX_IMAGE_PIXELS:
                raise ValueError()
            source.verify()
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError({'image': 'Use a valid JPG, PNG, or WebP image within the pixel limit.'})
    finally:
        upload.seek(0)
    return upload


def log_access(request, access, email, action='VIEW', success=True):
    record = AccessLog.objects.create(image_access=access, user_id=access.user_image.user_id,
        image_id=access.user_image_id, image_name=access.user_image.image_name,
        access_rule_name=access.access_name, email=email,
        ip_address=request.META.get('REMOTE_ADDR'), action_type=action, success=success)
    if not success:
        notify_owner(access, 'notify_on_failed_access', 'Failed image access attempt', f'An unsuccessful access attempt was recorded for {access.user_image.image_name}.')
    return record


def notify_owner(access, preference, subject, body):
    profile = UserProfile.objects.get(user_id=access.user_image.user_id)
    if getattr(profile, preference):
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [access.user_image.user.email], fail_silently=False)
        except Exception:
            logger.warning('Could not deliver owner notification')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_decrypted_image(request, image_id):
    image = owner_image(request, image_id)
    data = image.get_decrypted_bytes()
    if request.query_params.get('download') == '1':
        return private_response(data, f'image/{"jpeg" if image.file_type in ["jpg", "jpeg"] else image.file_type}', image.image_name)
    # Reduced-size gallery previews avoid repeatedly shipping full-resolution originals.
    with Image.open(io.BytesIO(data)) as source:
        source = ImageOps.exif_transpose(source).convert('RGB')
        source.thumbnail((1600, 1600))
        output = io.BytesIO()
        source.save(output, 'WEBP', quality=85)
    return private_response(output.getvalue(), 'image/webp')


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, ScopedRateThrottle]
    throttle_scope = 'login'
    serializer_class = RegisterUserSerializer


class VerifyView(APIView):
    def get(self, request):
        return Response({'id': request.user.pk, 'username': request.user.username,
                         'email': request.user.email, 'first_name': request.user.first_name})


class PasswordResetRequestView(PublicView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data['email'], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f'{settings.FRONTEND_URL}/forget-password/{uid}/{token}'
            try:
                send_mail('Reset your AuthoGraph password', f'Reset your password: {link}',
                          settings.DEFAULT_FROM_EMAIL, [user.email])
            except Exception:
                logger.warning('Password reset email delivery failed')
        return Response({'message': 'If this email has an account, a reset link will be sent.'})


class PasswordResetConfirmView(PublicView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(data['uidb64'])))
        except (ValueError, TypeError, OverflowError, User.DoesNotExist):
            raise ValidationError('Invalid reset link.')
        if not default_token_generator.check_token(user, data['token']):
            raise ValidationError('This reset link is invalid or expired.')
        user.set_password(data['new_password'])
        user.save()
        return Response({'message': 'Password updated. Sign in with your new password.'})


class ImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        upload = validate_upload(request.FILES.get('image'))
        with transaction.atomic():
            # Serialize quota checks per owner on databases supporting row locks.
            User.objects.select_for_update().get(pk=request.user.pk)
            used = UserImage.objects.filter(user=request.user).aggregate(total=Sum('file_size'))['total'] or 0
            if used + upload.size > settings.STORAGE_QUOTA_BYTES:
                raise ValidationError('Workspace storage limit reached. Remove an image before uploading.')
            image = UserImage.objects.create(user=request.user, image=upload)
        return Response(UserImageListSerializer(image).data, status=201)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100


class ImageListView(generics.ListAPIView):
    serializer_class = UserImageListSerializer
    pagination_class = StandardResultsSetPagination
    def get_queryset(self):
        queryset = UserImage.objects.filter(user=self.request.user)
        p = self.request.query_params
        if p.get('search'):
            queryset = queryset.filter(image_name__icontains=p['search'][:200])
        if p.getlist('file_type'):
            queryset = queryset.filter(file_type__in=p.getlist('file_type'))
        if p.get('shared') == 'true':
            queryset = queryset.filter(access_control_enabled=True)
        for param, field in [('size_min', 'file_size__gte'), ('size_max', 'file_size__lte')]:
            if p.get(param):
                try:
                    value = float(p[param])
                    if not 0 <= value <= 1_000_000:
                        raise ValueError()
                except ValueError:
                    raise ValidationError({param: 'Enter a valid size in MB.'})
                queryset = queryset.filter(**{field: value * 1024 * 1024})
        sort = p.get('sort', '-created_at')
        if sort not in ['created_at', '-created_at', 'image_name', '-image_name', 'file_size', '-file_size']:
            sort = '-created_at'
        return queryset.order_by(sort, '-pk')


class UserImageView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SpecificImageSerializer
    def get_queryset(self):
        return UserImage.objects.filter(user=self.request.user)
    def patch(self, request, pk):
        image = self.get_object()
        name = request.data.get('image_name', '')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 255:
            raise ValidationError('Enter an image name of up to 255 characters.')
        image.image_name = name.strip()
        image.save(update_fields=['image_name'])
        return Response(self.get_serializer(image).data)
    def put(self, request, pk):
        return self.patch(request, pk)


class UserProfileView(APIView):
    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return Response({'username': user.username, 'first_name': user.first_name,
            'last_name': user.last_name, 'email': user.email, 'social_links': profile.social_links,
            'avatar_url': '/api/profile/avatar' if profile.avatar else None})
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data,
            partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)


class AvatarUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        if not profile.avatar:
            return Response(status=404)
        with profile.avatar.open('rb') as source:
            return private_response(source.read())
    def post(self, request):
        upload = validate_upload(request.FILES.get('avatar'), 5 * 1024 * 1024)
        with Image.open(upload) as source:
            source = ImageOps.exif_transpose(source).convert('RGB')
            source.thumbnail((512, 512))
            buffer = io.BytesIO()
            source.save(buffer, 'PNG')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if profile.avatar:
            profile.avatar.delete(save=False)
        profile.avatar.save(f'{request.user.pk}.png', ContentFile(buffer.getvalue()))
        return Response({'avatar_url': '/api/profile/avatar'})


class PasswordChangeView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password updated. Please sign in again.'})


class WatermarkSettingsView(APIView):
    def get(self, request, image_id):
        image = owner_image(request, image_id)
        obj, _ = WatermarkSettings.objects.get_or_create(user_image=image)
        return Response(WatermarkSettingsSerializer(obj).data)
    def post(self, request, image_id):
        image = owner_image(request, image_id)
        obj, _ = WatermarkSettings.objects.get_or_create(user_image=image)
        serializer = WatermarkSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        invalidate_renders(image)
        return Response(serializer.data)
    patch = post
    put = post
    def delete(self, request, image_id):
        return self._disable(request, image_id)
    def _disable(self, request, image_id):
        image = owner_image(request, image_id)
        WatermarkSettings.objects.update_or_create(user_image=image, defaults={'enabled': False})
        invalidate_renders(image)
        return Response(status=204)


class InvisibleWatermarkView(APIView):
    def get(self, request, image_id):
        image = owner_image(request, image_id)
        obj, _ = InvisibleWatermarkSettings.objects.get_or_create(user_image=image, defaults={'text': ''})
        return Response({'enabled': obj.enabled, 'text': obj.text})
    def post(self, request, image_id):
        image = owner_image(request, image_id)
        obj, _ = InvisibleWatermarkSettings.objects.get_or_create(user_image=image, defaults={'text': ''})
        serializer = InvisibleWatermarkSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('enabled', obj.enabled) and not serializer.validated_data.get('text', obj.text):
            raise ValidationError('Enter a hidden message first.')
        if serializer.validated_data.get('enabled', obj.enabled):
            from .scripts.steg import TextSteganography
            try:
                pixels = image.get_decrypted_image()
                message = encode_signature(pixels, image, serializer.validated_data.get('text', obj.text))
                TextSteganography().embed_array(pixels, message)
            except ValueError as exc:
                raise ValidationError(str(exc))
        serializer.save()
        invalidate_renders(image)
        return Response({'enabled': obj.enabled, 'text': obj.text})
    patch = post
    def delete(self, request, image_id):
        image = owner_image(request, image_id)
        InvisibleWatermarkSettings.objects.update_or_create(user_image=image, defaults={'enabled': False, 'text': ''})
        invalidate_renders(image)
        return Response(status=204)


class ProtectedPreviewView(APIView):
    def get(self, request, image_id):
        image = owner_image(request, image_id)
        features = {'watermark': image.watermark_enabled, 'hidden_watermark': image.hidden_watermark_enabled,
                    'metadata': image.metadata_enabled, 'ai_protection': image.ai_protection_enabled}
        try:
            data = ProtectionChain.render(image, features)
        except Exception:
            logger.exception('Image protection processing failed')
            return Response({'error': 'Could not apply protection. Review your settings and try again.'}, status=422)
        return private_response(data, filename=f'protected-{image.pk}.png' if request.query_params.get('download') == '1' else None)

    def post(self, request, image_id):
        image = owner_image(request, image_id)
        serializer = WatermarkSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        features = {'watermark': serializer.validated_data.get('enabled', False),
                    'hidden_watermark': image.hidden_watermark_enabled,
                    'metadata': image.metadata_enabled, 'ai_protection': image.ai_protection_enabled}
        try:
            data = ProtectionChain.render(image, features,
                watermark_settings=serializer.validated_data.get('settings', WatermarkSettings.get_default_settings(image)))
        except Exception:
            logger.exception('Draft protection preview failed')
            return Response({'error': 'Could not render the protection preview.'}, status=422)
        return private_response(data)


class CreateAccessView(APIView):
    def get(self, request, image_id):
        image = owner_image(request, image_id)
        rules = image.access_rules.order_by('-created_at')
        return Response({'rules': ImageAccessSerializer(rules, many=True).data, 'total_count': rules.count()})
    def post(self, request, image_id):
        image = owner_image(request, image_id)
        current_features = {key: getattr(image, f'{key}_enabled')
            for key in ['watermark', 'hidden_watermark', 'metadata', 'ai_protection']}
        serializer = ImageAccessSerializer(data={'protection_features': current_features,
            **request.data, 'user_image': image.pk})
        serializer.is_valid(raise_exception=True)
        features = {**current_features, **serializer.validated_data.get('protection_features', {})}
        for key, field in [('watermark','watermark_enabled'), ('hidden_watermark','hidden_watermark_enabled'),
                           ('ai_protection','ai_protection_enabled'), ('metadata','metadata_enabled')]:
            if features.get(key) and not getattr(image, field):
                raise ValidationError(f'Enable {key.replace("_", " ")} before creating this link.')
        rule = serializer.save(protection_features=features)
        return Response({'access_rule': ImageAccessSerializer(rule).data}, status=201)
    def patch(self, request, image_id, rule_id):
        rule = get_object_or_404(ImageAccess, pk=rule_id, user_image=owner_image(request, image_id))
        allowed = {'revoked', 'protection_features', 'shared_filename', 'show_watermark',
                   'allow_download', 'download_without_watermark', 'download_metadata_mode'}
        if not request.data or set(request.data) - allowed:
            raise ValidationError('Only link delivery settings, revocation and protection can be updated.')
        serializer = ImageAccessSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        fields = ['updated_at']
        if 'revoked' in request.data:
            if type(request.data['revoked']) is not bool:
                raise ValidationError({'revoked': 'Enter true or false.'})
            rule.revoked = request.data['revoked']
            fields.append('revoked')
        if 'protection_features' in request.data:
            features = {**rule.protection_features, **serializer.validated_data['protection_features']}
            for key in ['watermark', 'hidden_watermark', 'metadata', 'ai_protection']:
                if features.get(key) and not getattr(rule.user_image, f'{key}_enabled'):
                    raise ValidationError(f'Enable {key.replace("_", " ")} before applying it to this link.')
            rule.protection_features = features
            fields.append('protection_features')
        if 'protection_features' in request.data or 'show_watermark' in request.data:
            if rule.protected_image:
                name, storage = rule.protected_image.name, rule.protected_image.storage
                transaction.on_commit(lambda: storage.delete(name))
            rule.protected_image = None
            fields.append('protected_image')
        for field in ['shared_filename', 'show_watermark', 'allow_download', 'download_without_watermark', 'download_metadata_mode']:
            if field in serializer.validated_data:
                setattr(rule, field, serializer.validated_data[field])
                fields.append(field)
        rule.save(update_fields=fields)
        return Response(ImageAccessSerializer(rule).data)
    def delete(self, request, image_id, rule_id=None):
        image = owner_image(request, image_id)
        if rule_id:
            get_object_or_404(ImageAccess, pk=rule_id, user_image=image).delete()
        else:
            image.access_rules.all().delete()
        return Response(status=204)


def email_allowed(access, email):
    return not access.allowed_emails or email in [e.lower() for e in access.allowed_emails]


class InitiateAccessView(PublicView):
    def post(self, request, token):
        access = get_object_or_404(ImageAccess.objects.select_related('user_image__user'), token=token)
        serializer = AccessVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data['email'].strip().lower()
        if not access.is_valid():
            raise PermissionDenied('This link has expired, been revoked, or reached its view limit.')
        if not email_allowed(access, email):
            existing = AccessRequest.objects.filter(image_access=access, email=email).first()
            return Response({'error': 'This email is not on the recipient list.', 'can_request_access': True,
                'request_status': existing.status if existing else None}, status=403)
        if access.requires_password and not data.get('password'):
            return Response({'requires_password': True})
        if access.requires_password and not access.check_password(data['password']):
            log_access(request, access, email, 'ATTEMPT', False)
            raise PermissionDenied('Incorrect link password.')
        otp = OTPHandler.generate_and_store_otp(access, email)
        try:
            send_mail('Your AuthoGraph verification code', f'Your code is {otp}. It expires in 5 minutes.',
                      settings.DEFAULT_FROM_EMAIL, [email])
        except Exception:
            OTPSecret.objects.filter(image_access=access, email=email, is_used=False).update(is_used=True)
            return Response({'error': 'Email could not be sent. Please try again later.'}, status=503)
        return Response({'requires_otp': True, 'message': 'Verification code sent.'})


class VerifyOTPView(PublicView):
    def post(self, request, token):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        with transaction.atomic():
            access = get_object_or_404(ImageAccess.objects.select_for_update().select_related('user_image__user'), token=token)
            if not access.is_valid() or not email_allowed(access, email):
                raise PermissionDenied('This link is no longer available to this recipient.')
            if not OTPHandler.verify_otp(access, email, serializer.validated_data['otp']):
                log_access(request, access, email, 'ATTEMPT', False)
                # Return instead of raising so failed attempts remain committed.
                return Response({'error': 'Invalid or expired code. Request a new code after five attempts.'}, status=400)
            eligible = ImageAccess.objects.filter(pk=access.pk).filter(Q(max_views=0) | Q(current_views__lt=F('max_views')))
            if not eligible.update(current_views=F('current_views') + 1):
                raise PermissionDenied('This link has reached its view limit.')
            log_access(request, access, email)
        grant = signing.dumps({'token': access.token, 'email': email, 'version': access.updated_at.isoformat()}, salt='image-viewer')
        notify_owner(access, 'notify_on_successful_access', 'Image viewed', f'{email} opened {access.user_image.image_name}.')
        return Response({'viewer_token': grant, 'image_url': f'/api/access/{token}/image',
            'image_name': access.shared_filename or access.user_image.image_name, 'allow_download': access.allow_download,
            'download_without_watermark': access.download_without_watermark,
            'protection_features': shared_protection_features(access), 'expires_in': settings.VIEWER_SESSION_SECONDS})


def verified_access(request, token):
    access = get_object_or_404(ImageAccess.objects.select_related('user_image__user'), token=token)
    try:
        grant = signing.loads(request.headers.get('X-Viewer-Token', ''), salt='image-viewer', max_age=settings.VIEWER_SESSION_SECONDS)
    except signing.BadSignature:
        raise PermissionDenied('Verify your email to view this image.')
    if (grant.get('token') != token or grant.get('version') != access.updated_at.isoformat()
            or not access.is_active() or not email_allowed(access, grant.get('email', ''))):
        raise PermissionDenied('Your access has expired or been revoked.')
    return access, grant['email']


def shared_protection_features(access):
    features = dict(access.protection_features)
    # Preview watermarks follow saved image settings unless this link explicitly opts out.
    features['watermark'] = access.show_watermark and access.user_image.watermark_enabled
    return features


def shared_image_bytes(access):
    features = shared_protection_features(access)
    if not access.protected_image or features != access.protection_features:
        try:
            ProtectionChain.create_protected_image(access.user_image, features, access)
            access.protection_features = features
            access.save(update_fields=['protection_features'])
        except Exception:
            logger.exception('Share image processing failed')
            raise ValidationError('Image protection could not be applied. Contact the owner.')
    with access.protected_image.open('rb') as source:
        return source.read()


class SharedImageView(PublicView):
    def get(self, request, token):
        access, _ = verified_access(request, token)
        return private_response(shared_image_bytes(access))


class ServeProtectedImageDownloadView(PublicView):
    def get(self, request, token):
        access, email = verified_access(request, token)
        if not access.allow_download:
            raise PermissionDenied('Downloads are disabled for this link.')
        if access.download_without_watermark or access.download_metadata_mode != 'inherit':
            features = shared_protection_features(access)
            if access.download_without_watermark:
                features['watermark'] = False
            if access.download_metadata_mode != 'inherit':
                features['metadata'] = access.download_metadata_mode == 'include'
            try:
                data = ProtectionChain.render(access.user_image, features)
            except Exception:
                logger.exception('Download image processing failed')
                raise ValidationError('Image protection could not be applied. Contact the owner.')
        else:
            data = shared_image_bytes(access)
        log_access(request, access, email, 'DOWNLOAD')
        notify_owner(access, 'notify_on_download', 'Image downloaded', f'{email} downloaded {access.user_image.image_name}.')
        name = access.shared_filename or access.user_image.image_name or 'image'
        name = ''.join(c for c in name if c not in '/\\' and ord(c) >= 32 and ord(c) != 127).strip().strip('.') or 'image'
        if name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            name = name.rsplit('.', 1)[0]
        return private_response(data, filename=f'{name}.png')


class AccessLogView(APIView):
    def queryset(self, request, image_id=None):
        queryset = AccessLog.objects.filter(Q(image_access__user_image__user=request.user) | Q(user_id=request.user.pk))
        if image_id or request.query_params.get('image_id'):
            try:
                pk = int(image_id or request.query_params['image_id'])
            except ValueError:
                raise ValidationError('Invalid image ID.')
            queryset = queryset.filter(Q(image_access__user_image_id=pk) | Q(image_id=pk))
        if request.query_params.get('search'):
            term = request.query_params['search'][:200]
            queryset = queryset.filter(Q(email__icontains=term) | Q(city__icontains=term) | Q(image_name__icontains=term))
        if request.query_params.get('action_type'):
            queryset = queryset.filter(action_type=request.query_params['action_type'].upper())
        return queryset.select_related('image_access__user_image').order_by('-accessed_at', '-pk')
    def get(self, request, image_id=None):
        paginator = StandardResultsSetPagination()
        rows = paginator.paginate_queryset(self.queryset(request, image_id), request)
        return paginator.get_paginated_response(AccessLogSerializer(rows, many=True).data)
    def delete(self, request, image_id=None):
        self.queryset(request, image_id).delete()
        return Response(status=204)


class ImageAccessLogView(AccessLogView):
    pass


class ImageMetadataView(APIView):
    def get(self, request, image_id):
        return Response({'metadata': owner_image(request, image_id).metadata})
    def put(self, request, image_id):
        image = owner_image(request, image_id)
        updates = request.data.get('updates')
        if not isinstance(updates, list) or len(updates) > 100:
            raise ValidationError('Supply up to 100 metadata updates.')
        metadata = image.metadata or {}
        for update in updates:
            if not isinstance(update, dict):
                raise ValidationError('Invalid metadata entry.')
            name, value = update.get('field_name'), update.get('value')
            if not isinstance(name, str) or not 1 <= len(name) <= 100 or not isinstance(value, str) or len(value) > 2000:
                raise ValidationError('Use a field name and a text value of up to 2000 characters.')
            metadata.setdefault('custom', {})[name] = {'label': name, 'value': value, 'type': 'string'}
        image.metadata = metadata
        image.save(update_fields=['metadata'])
        invalidate_renders(image)
        return Response({'metadata': image.metadata})
    def delete(self, request, image_id):
        image = owner_image(request, image_id)
        image.metadata.get('custom', {}).pop(request.query_params.get('field'), None)
        image.save(update_fields=['metadata'])
        invalidate_renders(image)
        return Response(status=204)


class CustomMetadataView(ImageMetadataView):
    def post(self, request, image_id):
        data = request.data
        name, value = data.get('tag_name'), data.get('value')
        if not isinstance(name, str) or not 1 <= len(name) <= 100 or not isinstance(value, str) or len(value) > 2000:
            raise ValidationError('Enter a name and value for this metadata field.')
        image = owner_image(request, image_id)
        image.metadata.setdefault('custom', {})[name] = {'label': name, 'value': value, 'type': 'string'}
        image.save(update_fields=['metadata'])
        invalidate_renders(image)
        return Response({'metadata': image.metadata})


class RequestAccessView(PublicView):
    def post(self, request, token):
        access = get_object_or_404(ImageAccess.objects.select_related('user_image__user'), token=token)
        if not access.is_valid():
            raise PermissionDenied('This link is no longer available.')
        email = serializers.EmailField().run_validation(request.data.get('email')).lower()
        message = serializers.CharField(max_length=2000, allow_blank=True).run_validation(request.data.get('message', ''))
        obj, _ = AccessRequest.objects.get_or_create(image_access=access, email=email, defaults={'message': message})
        if obj.status == 'denied':
            obj.status, obj.message = 'pending', message
            obj.save()
        notify_owner(access, 'notify_on_access_request', 'New image access request', f'{email} requested access to {access.user_image.image_name}.')
        return Response({'message': 'Access request sent.', 'status': obj.status}, status=201)


class ManageAccessRequestsView(APIView):
    def get(self, request):
        rows = AccessRequest.objects.filter(image_access__user_image__user=request.user, status='pending').select_related('image_access__user_image').order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(rows, request)
        return paginator.get_paginated_response(AccessRequestSerializer(page, many=True).data)
    def post(self, request, request_id=None):
        with transaction.atomic():
            obj = get_object_or_404(AccessRequest.objects.select_for_update(), pk=request_id, image_access__user_image__user=request.user)
            action = request.data.get('action')
            if action not in ['approve', 'deny']:
                raise ValidationError('Choose approve or deny.')
            obj.status = 'approved' if action == 'approve' else 'denied'
            obj.save()
            access = ImageAccess.objects.select_for_update().get(pk=obj.image_access_id)
            if action == 'approve' and access.allowed_emails and obj.email not in access.allowed_emails:
                access.allowed_emails.append(obj.email)
                access.save()
        return Response({'status': obj.status})


class AIProtectionView(APIView):
    def get(self, request, image_id):
        image = owner_image(request, image_id)
        return Response({'enabled': image.ai_protection_enabled, 'available': bool(settings.AI_PROTECTION_URL),
                         'protected_image': f'/api/images/{image_id}/preview' if image.ai_protection_enabled else None})
    def post(self, request, image_id):
        image = owner_image(request, image_id)
        if not settings.AI_PROTECTION_URL:
            return Response({'error': 'AI processing is not configured for this workspace.'}, status=503)
        if urlparse(settings.AI_PROTECTION_URL).scheme != 'https':
            return Response({'error': 'AI processing requires a secure HTTPS service.'}, status=503)
        if request.data.get('consent') is not True:
            raise ValidationError('Confirm that this image may be sent to the configured processing service.')
        try:
            response = requests.post(settings.AI_PROTECTION_URL, files={'file': ('image', image.get_decrypted_bytes())},
                                     timeout=(5, 30), allow_redirects=False, stream=True)
            with response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > settings.MAX_UPLOAD_BYTES:
                        raise ValueError('Response too large')
                    chunks.append(chunk)
                payload = b''.join(chunks)
            with Image.open(io.BytesIO(payload)) as result:
                if result.width * result.height > settings.MAX_IMAGE_PIXELS:
                    raise ValueError('Response dimensions too large')
                result.load()
                output = io.BytesIO()
                result.save(output, 'PNG')
        except (requests.RequestException, OSError, ValueError, Image.DecompressionBombError):
            return Response({'error': 'Image processing failed. Try again later.'}, status=502)
        obj, _ = AIProtectionSettings.objects.get_or_create(user_image=image)
        if obj.protected_image:
            obj.protected_image.delete(save=False)
        obj.enabled = True
        obj.protected_image.save(f'ai-{image.pk}.png', ContentFile(output.getvalue()))
        image.ai_protection_enabled = True
        image.save(update_fields=['ai_protection_enabled'])
        invalidate_renders(image)
        return self.get(request, image_id)
    def delete(self, request, image_id):
        image = owner_image(request, image_id)
        AIProtectionSettings.objects.filter(user_image=image).delete()
        image.ai_protection_enabled = False
        image.save(update_fields=['ai_protection_enabled'])
        invalidate_renders(image)
        return Response(status=204)


class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSettingsSerializer
    def get_object(self):
        return UserProfile.objects.get_or_create(user=self.request.user)[0]


class DeleteAccountView(APIView):
    def delete(self, request):
        serializer = AccountDeletionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            AccessLog.objects.filter(Q(user_id=request.user.pk) | Q(image_access__user_image__user=request.user)).delete()
            request.user.delete()
        return Response(status=204)
    post = delete


class WorkspaceView(APIView):
    def get(self, request):
        images = UserImage.objects.filter(user=request.user)
        rules = ImageAccess.objects.filter(user_image__user=request.user)
        logs = AccessLog.objects.filter(user_id=request.user.pk)
        return Response({'images': images.count(), 'storage_bytes': images.aggregate(total=Sum('file_size'))['total'] or 0,
            'storage_limit': settings.STORAGE_QUOTA_BYTES, 'upload_limit': settings.MAX_UPLOAD_BYTES,
            'active_links': rules.filter(revoked=False).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())).filter(Q(max_views=0) | Q(current_views__lt=F('max_views'))).count(),
            'views': logs.filter(action_type='VIEW', success=True).count(),
            'pending_requests': AccessRequest.objects.filter(image_access__user_image__user=request.user, status='pending').count()})


class LinkListView(APIView):
    def get(self, request):
        rows = ImageAccess.objects.filter(user_image__user=request.user).select_related('user_image').order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(rows, request)
        data = [{**ImageAccessSerializer(row).data, 'image_name': row.user_image.image_name} for row in page]
        return paginator.get_paginated_response(data)
