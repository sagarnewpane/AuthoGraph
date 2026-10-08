import io
import os
import tempfile
from datetime import timedelta
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image
from cryptography.exceptions import InvalidTag
from django.core import mail, signing
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from backend.encryption import encrypt_image, decrypt_image, encrypt_aes_cbc, wrap_key, unwrap_key
from backend.models import User, UserImage, ImageAccess, OTPSecret, AccessLog, WatermarkSettings, InvisibleWatermarkSettings
from backend.scripts.steg import TextSteganography
from backend.utils import OTPHandler, ProtectionChain
from backend.signatures import inspect_signature


def image_file(name='sample.png', size=(129, 131)):
    output = io.BytesIO()
    Image.new('RGBA', size, (120, 140, 200, 180)).save(output, 'PNG')
    return SimpleUploadedFile(name, output.getvalue(), content_type='image/png')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SecurityTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media = tempfile.TemporaryDirectory()
        cls.override = override_settings(MEDIA_ROOT=cls.media.name)
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        cls.media.cleanup()
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='creator', password='Test!Password99', email='creator@example.com')
        self.other = User.objects.create_user(username='other', password='Test!Password99', email='other@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.visitor = APIClient()
        self.image = UserImage.objects.create(user=self.owner, image=image_file())
        self.rule = ImageAccess.objects.create(user_image=self.image, access_name='Client review', allowed_emails=['client@example.com'])

    def grant(self, rule=None):
        rule = rule or self.rule
        code = OTPHandler.generate_and_store_otp(rule, 'client@example.com')
        response = self.visitor.post(f'/access/{rule.token}/verify/', {'email': 'CLIENT@example.com', 'otp': code})
        self.assertEqual(response.status_code, 200, response.data)
        return response.data['viewer_token']

    def test_owner_only_decrypted_image(self):
        path = f'/images/{self.image.pk}/decrypted/'
        self.assertEqual(self.visitor.get(path).status_code, 401)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(path).status_code, 404)
        self.client.force_authenticate(self.owner)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_private_media_is_never_public(self):
        self.assertEqual(self.visitor.get(self.image.image.url).status_code, 404)
        ProtectionChain.create_protected_image(self.image, {}, self.rule)
        self.assertEqual(self.visitor.get(self.rule.protected_image.url).status_code, 404)

    def test_share_token_alone_cannot_view_or_download(self):
        ProtectionChain.create_protected_image(self.image, {}, self.rule)
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/').status_code, 403)
        self.assertEqual(self.visitor.get(f'/api/access/{self.rule.token}/download-protected/', HTTP_X_ACCESS_EMAIL='owner@igaurdian.local').status_code, 403)

    def test_verified_view_does_not_break_after_rendering(self):
        token = self.grant()
        for _ in range(2):
            response = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
            self.assertEqual(response.status_code, 200, getattr(response, 'data', None))
        self.assertEqual(AccessLog.objects.filter(action_type='VIEW').count(), 1)

    def test_download_permissions_and_trusted_attribution(self):
        token = self.grant()
        path = f'/api/access/{self.rule.token}/download-protected/'
        self.assertEqual(self.visitor.get(path, HTTP_X_VIEWER_TOKEN=token).status_code, 403)
        self.rule.allow_download = True
        self.rule.save()
        token = self.grant()
        response = self.visitor.get(path, HTTP_X_VIEWER_TOKEN=token, HTTP_X_ACCESS_EMAIL='spoofed@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AccessLog.objects.get(action_type='DOWNLOAD').email, 'client@example.com')

    def test_revocation_invalidates_existing_session(self):
        token = self.grant()
        self.client.patch(f'/images/{self.image.pk}/access/{self.rule.pk}/', {'revoked': True}, format='json')
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token).status_code, 403)

    def test_restoring_link_does_not_restore_old_sessions(self):
        token = self.grant()
        self.client.patch(f'/images/{self.image.pk}/access/{self.rule.pk}/', {'revoked': True}, format='json')
        self.client.patch(f'/images/{self.image.pk}/access/{self.rule.pk}/', {'revoked': False}, format='json')
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token).status_code, 403)

    def test_expiry_enforced_for_existing_session(self):
        token = self.grant()
        ImageAccess.objects.filter(pk=self.rule.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token).status_code, 403)

    def test_max_views_limits_admission_but_allows_admitted_session(self):
        self.rule.max_views = 1
        self.rule.save()
        token = self.grant()
        code = OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        self.assertEqual(self.visitor.post(f'/access/{self.rule.token}/verify/', {'email':'client@example.com','otp':code}).status_code, 403)
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token).status_code, 200)

    def test_grant_cannot_be_reused_on_another_link(self):
        token = self.grant()
        other = ImageAccess.objects.create(user_image=self.image)
        self.assertEqual(self.visitor.get(f'/access/{other.token}/image/', HTTP_X_VIEWER_TOKEN=token).status_code, 403)

    @override_settings(VIEWER_SESSION_SECONDS=-1)
    def test_viewer_session_expires(self):
        token = self.grant()
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token).status_code, 403)

    def test_otp_is_single_use(self):
        code = OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        self.assertTrue(OTPHandler.verify_otp(self.rule, 'client@example.com', code))
        self.assertFalse(OTPHandler.verify_otp(self.rule, 'client@example.com', code))

    def test_otp_expiry_and_attempt_limit(self):
        code = OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        OTPSecret.objects.filter(image_access=self.rule).update(created_at=timezone.now()-timedelta(minutes=6))
        self.assertFalse(OTPHandler.verify_otp(self.rule, 'client@example.com', code))
        code = OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(5):
            self.assertEqual(self.visitor.post(f'/access/{self.rule.token}/verify/', {'email':'client@example.com','otp':wrong}).status_code,400)
        self.assertFalse(OTPHandler.verify_otp(self.rule, 'client@example.com', code))
        self.assertEqual(OTPSecret.objects.latest('created_at').attempts, 5)

    def test_new_otp_invalidates_prior_codes(self):
        OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        self.assertEqual(OTPSecret.objects.filter(is_used=False).count(),1)

    def test_password_required_before_otp_is_issued(self):
        self.rule.requires_password = True
        self.rule.password = 'client-secret'
        self.rule.save()
        response = self.visitor.post(f'/access/{self.rule.token}/initiate/', {'email':'client@example.com'})
        self.assertTrue(response.data['requires_password'])
        self.assertEqual(OTPSecret.objects.count(),0)
        self.assertEqual(self.visitor.post(f'/access/{self.rule.token}/initiate/', {'email':'client@example.com','password':'wrong'}).status_code,403)
        self.assertEqual(self.visitor.post(f'/access/{self.rule.token}/initiate/', {'email':'CLIENT@example.com','password':'client-secret'}).status_code,200)
        self.assertEqual(len(mail.outbox),2) # owner failure alert and recipient code

    def test_current_recipient_list_checked_at_verification(self):
        code = OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        self.rule.allowed_emails=['someone-else@example.com'];self.rule.save()
        self.assertEqual(self.visitor.post(f'/access/{self.rule.token}/verify/', {'email':'client@example.com','otp':code}).status_code,403)

    def test_registration_without_optional_names(self):
        response = self.visitor.post('/api/register/',{'username':'newuser','email':'new@example.com','password':'Example!Pass98','password2':'Example!Pass98'})
        self.assertEqual(response.status_code,201,response.data)

    def test_reset_response_does_not_reveal_account_existence(self):
        known = self.visitor.post('/api/password-reset/', {'email':'creator@example.com'})
        unknown = self.visitor.post('/api/password-reset/', {'email':'nobody@example.com'})
        self.assertEqual(known.data,unknown.data)
        self.assertEqual(known.status_code,200)

    def test_owner_scoping_on_all_mutations(self):
        self.client.force_authenticate(self.other)
        for path,method,payload in [
            (f'/image/{self.image.pk}/','delete',{}),
            (f'/images/{self.image.pk}/access/','post',{'access_name':'stolen'}),
            (f'/api/image/{self.image.pk}/watermark-settings/','post',{'enabled':True}),
            (f'/api/image/{self.image.pk}/metadata/custom/','post',{'tag_name':'creator','value':'other'}),
        ]:
            self.assertEqual(getattr(self.client,method)(path,payload,format='json').status_code,404,path)

    def test_malformed_filters_are_validation_errors(self):
        self.assertEqual(self.client.get('/images/?size_min=invalid').status_code,400)
        self.assertEqual(self.client.get('/images/?size_max=nan').status_code,400)
        self.assertEqual(self.client.get('/access-logs/?search=client').status_code,200)

    def test_validation_of_share_and_watermark_settings(self):
        path = f'/images/{self.image.pk}/access/'
        for payload in [{'max_views':-1},{'allowed_emails':'client@example.com'},{'allowed_emails':['invalid']},{'requires_password':True},{'protection_features':{'watermark':'yes'}}]:
            self.assertEqual(self.client.post(path,payload,format='json').status_code,400,payload)
        response = self.client.post(f'/api/image/{self.image.pk}/watermark-settings/',{'settings':{'fontSize':100000}},format='json')
        self.assertEqual(response.status_code,400)

    def test_upload_validation_and_encrypted_storage(self):
        response = self.client.post('/upload/', {'image':SimpleUploadedFile('attack.png',b'not an image')}, format='multipart')
        self.assertEqual(response.status_code,400)
        response = self.client.post('/upload/', {'image':image_file('real.png')}, format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        uploaded = UserImage.objects.get(pk=response.data['id'])
        with uploaded.image.open('rb') as file:
            self.assertTrue(file.read().startswith(b'AGCM1'))
        self.assertTrue(uploaded.encryption_key.startswith('wrapped:'))
        self.assertTrue(uploaded.get_decrypted_bytes().startswith(b'\x89PNG'))
        self.assertNotIn('encryption_key',response.data)
        self.assertNotIn('/media/',response.data['image_url'])

    @override_settings(STORAGE_QUOTA_BYTES=1)
    def test_storage_limit_enforced(self):
        self.assertEqual(self.client.post('/upload/',{'image':image_file()},format='multipart').status_code,400)

    def test_processing_fails_closed(self):
        self.rule.protection_features={'watermark':True};self.rule.save()
        token=self.grant()
        with patch('backend.utils.ProtectionChain.render',side_effect=ValueError('broken')):
            response=self.visitor.get(f'/access/{self.rule.token}/image/',HTTP_X_VIEWER_TOKEN=token)
        self.assertEqual(response.status_code,400)
        self.assertNotIn(b'PNG',response.content)

    def test_watermark_and_unicode_hidden_message_preserve_alpha_and_size(self):
        WatermarkSettings.objects.create(user_image=self.image,enabled=True,settings={'text':'Studio','fontSize':16,'opacity':40,'color':'#ffffff','pattern':'tiled'})
        InvisibleWatermarkSettings.objects.create(user_image=self.image,enabled=True,text='© Studio — नेपाल')
        rendered=ProtectionChain.render(self.image,{'watermark':True,'hidden_watermark':True,'metadata':True})
        image=cv2.imdecode(np.frombuffer(rendered,np.uint8),cv2.IMREAD_UNCHANGED)
        self.assertEqual(image.shape,(131,129,4))
        self.assertEqual(inspect_signature(image), {'status': 'verified', 'creator': 'creator', 'signature': '© Studio — नेपाल'})
        self.assertNotEqual(rendered,self.image.get_decrypted_bytes())

    def test_draft_watermark_preview_changes_pixels_without_saving(self):
        response = self.client.post(f'/images/{self.image.pk}/preview/', {
            'enabled': True, 'settings': {'text': 'Studio', 'fontSize': 20,
                'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'}
        }, format='json')
        self.assertEqual(response.status_code, 200)
        preview = np.array(Image.open(io.BytesIO(response.content)).convert('RGBA'))
        original = np.array(Image.open(io.BytesIO(self.image.get_decrypted_bytes())).convert('RGBA'))
        self.assertTrue(np.any(preview != original))
        self.image.refresh_from_db()
        self.assertFalse(self.image.watermark_enabled)
        self.assertFalse(WatermarkSettings.objects.filter(user_image=self.image).exists())

    def test_legacy_watermark_layouts_render_and_can_be_saved(self):
        original = Image.new('RGBA', (400, 300), (0, 0, 0, 255))
        for pattern in ['single', 'tiled', 'diagonal', 'grid', 'corners']:
            with self.subTest(pattern=pattern):
                settings = {'text': 'Studio', 'fontSize': 20, 'opacity': 80,
                            'color': '#ffffff', 'pattern': pattern}
                response = self.client.post(f'/api/image/{self.image.pk}/watermark-settings/',
                    {'enabled': True, 'settings': settings}, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                rendered = np.array(ProtectionChain._apply_watermark(original, settings))
                self.assertTrue(np.any(rendered[..., :3] != 0))
                if pattern in ['diagonal', 'corners']:
                    self.assertTrue(np.any(rendered[:100, :150, :3] != 0))

    def test_update_link_protection_replaces_cached_copy_and_session(self):
        old_grant = self.grant()
        old_copy = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=old_grant)
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        response = self.client.patch(f'/images/{self.image.pk}/access/{self.rule.pk}/',
            {'protection_features': {'watermark': True}}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=old_grant).status_code, 403)
        self.rule.refresh_from_db()
        token = self.grant()
        new_copy = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        self.assertEqual(new_copy.status_code, 200)
        before = np.array(Image.open(io.BytesIO(old_copy.content)))
        after = np.array(Image.open(io.BytesIO(new_copy.content)))
        self.assertTrue(np.any(before != after))

    def test_new_link_inherits_saved_watermark(self):
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        response = self.client.post(f'/images/{self.image.pk}/access/',
            {'access_name': 'Review', 'shared_filename': 'Client proof'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['access_rule']['protection_features']['watermark'])
        rule = ImageAccess.objects.get(pk=response.data['access_rule']['id'])
        token = self.grant(rule)
        result = self.visitor.get(f'/access/{rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        self.assertEqual(result.content, ProtectionChain.render(self.image, rule.protection_features))

    def test_existing_link_adds_newly_saved_watermark(self):
        token = self.grant()
        before = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        after = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        self.assertEqual(after.status_code, 200)
        self.assertNotEqual(before.content, after.content)
        self.assertEqual(after.content, ProtectionChain.render(self.image, {'watermark': True}))

    def test_watermarked_preview_and_clean_download_preserve_other_protection(self):
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        InvisibleWatermarkSettings.objects.create(user_image=self.image, enabled=True, text='Private attribution')
        self.rule.protection_features = {'hidden_watermark': True, 'metadata': True}
        self.rule.allow_download = True
        self.rule.download_without_watermark = True
        self.rule.shared_filename = 'Client proof.jpg'
        self.rule.save()
        token = self.grant()
        preview = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        download = self.visitor.get(f'/api/access/{self.rule.token}/download-protected/', HTTP_X_VIEWER_TOKEN=token)
        self.assertEqual(download.status_code, 200)
        self.assertIn('filename="Client proof.png"', download['Content-Disposition'])
        self.assertNotEqual(preview.content, download.content)
        self.assertEqual(download.content, ProtectionChain.render(self.image, {'hidden_watermark': True, 'metadata': True, 'watermark': False}))
        decoded = cv2.imdecode(np.frombuffer(download.content, np.uint8), cv2.IMREAD_UNCHANGED)
        self.assertEqual(inspect_signature(decoded)['signature'], 'Private attribution')
        self.assertIn('AuthoGraph', Image.open(io.BytesIO(download.content)).info)
        # Download rendering must never replace the watermarked preview cache.
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token).content, preview.content)

    def test_recipient_cannot_request_clean_download_without_owner_permission(self):
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        self.rule.allow_download = True
        self.rule.save()
        token = self.grant()
        preview = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        download = self.visitor.get(f'/api/access/{self.rule.token}/download-protected/?download_without_watermark=true', HTTP_X_VIEWER_TOKEN=token)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(preview.content, download.content)

    def test_owner_can_edit_delivery_and_turn_off_preview_watermark(self):
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        old_token = self.grant()
        payload = {'shared_filename': 'Campaign delivery', 'show_watermark': False,
                   'allow_download': True, 'download_without_watermark': False}
        self.client.force_authenticate(self.other)
        path = f'/images/{self.image.pk}/access/{self.rule.pk}/'
        self.assertEqual(self.client.patch(path, payload, format='json').status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(path, payload, format='json').status_code, 200)
        self.assertEqual(self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=old_token).status_code, 403)
        self.rule.refresh_from_db()
        code = OTPHandler.generate_and_store_otp(self.rule, 'client@example.com')
        verified = self.visitor.post(f'/access/{self.rule.token}/verify/', {'email': 'client@example.com', 'otp': code})
        self.assertEqual(verified.data['image_name'], 'Campaign delivery')
        self.assertFalse(verified.data['protection_features']['watermark'])
        preview = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=verified.data['viewer_token'])
        self.assertEqual(preview.content, ProtectionChain.render(self.image, {'watermark': False}))

    def test_shared_filename_validation(self):
        path = f'/images/{self.image.pk}/access/{self.rule.pk}/'
        for name in ['../file', 'path\\file', 'name\r\nHeader', '..']:
            with self.subTest(name=name):
                self.assertEqual(self.client.patch(path, {'shared_filename': name}, format='json').status_code, 400)

    def test_metadata_can_differ_between_preview_and_download(self):
        WatermarkSettings.objects.create(user_image=self.image, enabled=True,
            settings={'text': 'Studio', 'fontSize': 20, 'opacity': 80, 'color': '#ffffff', 'pattern': 'tiled'})
        for include_preview, mode, include_download in [(True, 'strip', False),
                (False, 'include', True), (False, 'inherit', False), (True, 'inherit', True)]:
            with self.subTest(preview=include_preview, download=mode):
                created = self.client.post(f'/images/{self.image.pk}/access/', {
                    'allow_download': True, 'protection_features': {'metadata': include_preview},
                    'download_metadata_mode': mode
                }, format='json')
                self.assertEqual(created.status_code, 201, created.data)
                rule = ImageAccess.objects.get(pk=created.data['access_rule']['id'])
                self.assertTrue(rule.protection_features['watermark'])
                token = self.grant(rule)
                preview = self.visitor.get(f'/access/{rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
                download = self.visitor.get(f'/api/access/{rule.token}/download-protected/', HTTP_X_VIEWER_TOKEN=token)
                self.assertEqual(download.status_code, 200)
                preview_image = Image.open(io.BytesIO(preview.content))
                download_image = Image.open(io.BytesIO(download.content))
                self.assertEqual('AuthoGraph' in preview_image.info, include_preview)
                self.assertEqual('AuthoGraph' in download_image.info, include_download)
                np.testing.assert_array_equal(np.array(preview_image), np.array(download_image))

    def test_metadata_strip_removes_source_exif_icc_and_text(self):
        from types import SimpleNamespace
        from PIL import PngImagePlugin
        source = Image.new('RGB', (40, 40), 'red')
        exif = Image.Exif()
        exif[315] = 'Original photographer'
        text = PngImagePlugin.PngInfo()
        text.add_text('Private note', 'Source metadata')
        payload = io.BytesIO()
        source.save(payload, 'PNG', exif=exif, icc_profile=b'source-profile', pnginfo=text)
        original = Image.open(io.BytesIO(payload.getvalue()))
        self.assertIn('exif', original.info)
        self.assertIn('icc_profile', original.info)
        image = SimpleNamespace(get_decrypted_bytes=lambda: payload.getvalue(),
                                metadata={'custom': {'Copyright': 'Studio'}})
        for included in [False, True]:
            rendered = Image.open(io.BytesIO(ProtectionChain.render(image, {'metadata': included})))
            self.assertNotIn('exif', rendered.info)
            self.assertNotIn('icc_profile', rendered.info)
            self.assertNotIn('Private note', rendered.info)
            self.assertEqual(set(rendered.info), {'AuthoGraph'} if included else set())

    def test_editing_metadata_preserves_other_link_protection_and_invalidates_cache(self):
        InvisibleWatermarkSettings.objects.create(user_image=self.image, enabled=True, text='Studio attribution')
        self.rule.protection_features = {'hidden_watermark': True, 'metadata': True}
        self.rule.save()
        old_token = self.grant()
        before = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=old_token)
        self.assertIn('AuthoGraph', Image.open(io.BytesIO(before.content)).info)
        response = self.client.patch(f'/images/{self.image.pk}/access/{self.rule.pk}/',
            {'protection_features': {'metadata': False}, 'download_metadata_mode': 'strip'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['protection_features']['hidden_watermark'])
        self.rule.refresh_from_db()
        self.assertFalse(self.rule.protected_image)
        token = self.grant()
        after = self.visitor.get(f'/access/{self.rule.token}/image/', HTTP_X_VIEWER_TOKEN=token)
        self.assertNotIn('AuthoGraph', Image.open(io.BytesIO(after.content)).info)
        decoded = cv2.imdecode(np.frombuffer(after.content, np.uint8), cv2.IMREAD_UNCHANGED)
        self.assertEqual(inspect_signature(decoded)['signature'], 'Studio attribution')
        self.assertEqual(self.client.patch(f'/images/{self.image.pk}/access/{self.rule.pk}/',
            {'download_metadata_mode': 'invalid'}, format='json').status_code, 400)

    def test_public_signature_check_verifies_creator_without_saving_upload(self):
        InvisibleWatermarkSettings.objects.create(user_image=self.image, enabled=True, text='© Creator — नेपाल')
        protected = ProtectionChain.render(self.image, {'hidden_watermark': True})
        before = UserImage.objects.count()
        response = self.visitor.post('/api/verify-signature/', {
            'image': SimpleUploadedFile('copy.png', protected, content_type='image/png')
        }, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'verified', 'creator': 'creator', 'signature': '© Creator — नेपाल'})
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertNotIn(self.owner.email.encode(), response.content)
        self.assertEqual(UserImage.objects.count(), before)

    def test_public_signature_check_distinguishes_unsigned_and_missing(self):
        pixels = np.zeros((129, 131, 4), dtype=np.uint8)
        pixels[:, :, 3] = 255
        for signature in [None, 'Claimed creator']:
            sample = TextSteganography().embed_array(pixels, signature) if signature else pixels
            encoded = cv2.imencode('.png', sample)[1].tobytes()
            response = self.visitor.post('/api/verify-signature/', {
                'image': SimpleUploadedFile('legacy.png', encoded, content_type='image/png')
            }, format='multipart')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {'status': 'unsigned' if signature else 'not_found',
                                           'creator': None, 'signature': signature})

    def test_public_signature_check_rejects_transplanted_and_forged_attribution(self):
        InvisibleWatermarkSettings.objects.create(user_image=self.image, enabled=True, text='Studio')
        protected = ProtectionChain.render(self.image, {'hidden_watermark': True})
        changed = cv2.imdecode(np.frombuffer(protected, np.uint8), cv2.IMREAD_UNCHANGED)
        changed[:, :, 2] ^= 128
        forged = TextSteganography().embed_array(changed, 'AGS1:forged-creator-record')
        for pixels in [changed, forged]:
            encoded = cv2.imencode('.png', pixels)[1].tobytes()
            response = self.visitor.post('/api/verify-signature/', {
                'image': SimpleUploadedFile('changed.png', encoded, content_type='image/png')
            }, format='multipart')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {'status': 'invalid', 'creator': None, 'signature': None})

    def test_public_signature_check_validates_uploads(self):
        self.assertEqual(self.visitor.post('/api/verify-signature/', {}, format='multipart').status_code, 400)
        bad = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        self.assertEqual(self.visitor.post('/api/verify-signature/', {'image': bad}, format='multipart').status_code, 400)

    @override_settings(AI_PROTECTION_URL='')
    def test_ai_service_disabled_by_default(self):
        self.assertEqual(self.client.post(f'/images/{self.image.pk}/ai-protection/',{'consent':True},format='json').status_code,503)

    @override_settings(AI_PROTECTION_URL='https://processor.example.com/perturb')
    def test_ai_service_requires_explicit_consent(self):
        with patch('backend.views.requests.post') as mocked:
            self.assertEqual(self.client.post(f'/images/{self.image.pk}/ai-protection/',{},format='json').status_code,400)
            mocked.assert_not_called()

    def test_deleted_rule_logs_remain_owner_scoped(self):
        self.grant()
        self.rule.delete()
        self.assertEqual(self.client.get('/access-logs/').data['count'],1)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/access-logs/').data['count'],0)

    def test_files_deleted_after_database_commit(self):
        filename=self.image.image.path
        with self.captureOnCommitCallbacks(execute=True): self.image.delete()
        self.assertFalse(os.path.exists(filename))

    def test_password_change_invalidates_old_jwt(self):
        token=str(RefreshToken.for_user(self.owner).access_token)
        self.owner.set_password('Different!Pass77');self.owner.save()
        client=APIClient();client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(client.get('/verify/').status_code,401)

    def test_authenticated_encryption_detects_tampering_and_reads_legacy(self):
        key=os.urandom(32);plain=b'original image bytes'
        encrypted=encrypt_image(plain,key)
        self.assertEqual(decrypt_image(encrypted,key),plain)
        with self.assertRaises(InvalidTag): decrypt_image(encrypted[:-1]+bytes([encrypted[-1]^1]),key)
        self.assertEqual(decrypt_image(encrypt_aes_cbc(plain,key),key),plain)
        self.assertEqual(unwrap_key(wrap_key(key)),key)
