from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from .views import (
    RegisterView, LoginView, SharedImageView, ProtectedPreviewView, WorkspaceView, LinkListView,
    VerifyImageSignatureView,
    VerifyView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ImageUploadView,
    ImageListView,
    UserImageView,
    UserProfileView,
    AvatarUploadView,
    PasswordChangeView,
    WatermarkSettingsView,
    InvisibleWatermarkView,
    InitiateAccessView,
    CreateAccessView,
    VerifyOTPView,
    AccessLogView,
    ImageAccessLogView,
    ImageMetadataView,
    CustomMetadataView,
    RequestAccessView,
    ManageAccessRequestsView,
    AIProtectionView,
    ServeProtectedImageDownloadView,
    NotificationSettingsView,
    DeleteAccountView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import serve_decrypted_image

urlpatterns = [
    path('api/verify-signature/', VerifyImageSignatureView.as_view(), name='verify-image-signature'),
    path('workspace/', WorkspaceView.as_view()),
    path('links/', LinkListView.as_view()),
    path('access/<str:token>/image/', SharedImageView.as_view()),
    path('images/<int:image_id>/preview/', ProtectedPreviewView.as_view()),
    path('admin/', admin.site.urls),
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='auth_register'),
    path('verify/', VerifyView.as_view(), name='verify'),
    path('api/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('api/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('images/', ImageListView.as_view(), name='image-list'),
    path('image/<int:pk>/', UserImageView.as_view(), name='view-image'),
    path('api/profile/', UserProfileView.as_view(), name='user-profile'),
    path('api/profile/avatar/', AvatarUploadView.as_view(), name='avatar-upload'),
    path('api/password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('api/user/notification-settings/', NotificationSettingsView.as_view(), name='user-notification-settings'),
    path('api/image/<int:image_id>/watermark-settings/',WatermarkSettingsView.as_view(),name='watermark-settings'),
    path('api/image/<int:image_id>/invisible-watermark/', InvisibleWatermarkView.as_view(), name='invisible_watermark'),


    path('images/<int:image_id>/access/', CreateAccessView.as_view()),
    path('images/<int:image_id>/access/<int:rule_id>/', CreateAccessView.as_view(), name='image-access-detail'),
    path('access/<str:token>/initiate/', InitiateAccessView.as_view()),
    path('access/<str:token>/verify/', VerifyOTPView.as_view()),
    path('access/<str:token>/request/', RequestAccessView.as_view(), name='request-access'),
    path('access-requests/',
             ManageAccessRequestsView.as_view(),
             name='access-requests-list'),

        # Endpoint for handling specific request actions (approve/deny)
        path('access-requests/<int:request_id>/',
             ManageAccessRequestsView.as_view(),
             name='access-request-detail'),

    path('access-logs/', AccessLogView.as_view(), name='access-logs'),
    path('access-logs/<int:image_id>/', ImageAccessLogView.as_view(), name='image-logs'),

    path('api/image/<int:image_id>/metadata/', ImageMetadataView.as_view(), name='image-metadata'),
    path('api/image/<int:image_id>/metadata/custom/', CustomMetadataView.as_view(), name='custom-metadata'),

    path('images/<int:image_id>/decrypted/', serve_decrypted_image, name='serve_decrypted_image'),
    path('images/<int:image_id>/ai-protection/', AIProtectionView.as_view(), name='ai-protection'),

    # New endpoint for downloading protected image by access token
    path('api/access/<str:token>/download-protected/', ServeProtectedImageDownloadView.as_view(), name='download_protected_image'),

    path('api/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('api/delete-account/', DeleteAccountView.as_view(), name='delete-account'),
]

# Private media must never be exposed by Django or the reverse proxy.
