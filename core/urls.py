from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register('contacts', views.EmergencyContactViewSet, basename='contact')
router.register('zones', views.SafetyZoneViewSet, basename='zone')
router.register('incidents', views.IncidentReportViewSet, basename='incident')
router.register('sos', views.SOSAlertViewSet, basename='sos')
router.register('checkins', views.CheckInViewSet, basename='checkin')
router.register('geofences', views.GeofenceZoneViewSet, basename='geofence')
router.register('chat', views.ChatMessageViewSet, basename='chat')

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
