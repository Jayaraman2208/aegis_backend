from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import get_bot_reply
from .models import (
    EmergencyContact, SafetyZone, IncidentReport, SOSAlert,
    SOSNotification, CheckIn, GeofenceZone, ChatMessage,
)
from .serializers import (
    UserSerializer, RegisterSerializer, EmergencyContactSerializer,
    SafetyZoneSerializer, IncidentReportSerializer, SOSAlertSerializer,
    CheckInSerializer, GeofenceZoneSerializer, ChatMessageSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth / profile
# ---------------------------------------------------------------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Emergency contacts
# ---------------------------------------------------------------------------
class EmergencyContactViewSet(viewsets.ModelViewSet):
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# Safety zones / risk map
# ---------------------------------------------------------------------------
class SafetyZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: zones are populated by the ML/risk pipeline, not end users."""
    queryset = SafetyZone.objects.all()
    serializer_class = SafetyZoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['lat'] = self.request.query_params.get('lat')
        ctx['lng'] = self.request.query_params.get('lng')
        return ctx

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """GET /api/zones/nearby/?lat=..&lng=..&radius_km=2"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius_km = float(request.query_params.get('radius_km', 2))
        if lat is None or lng is None:
            return Response({'detail': 'lat and lng are required'}, status=400)
        lat, lng = float(lat), float(lng)

        zones = [
            z for z in SafetyZone.objects.all()
            if z.distance_km_to(lat, lng) <= radius_km
        ]
        zones.sort(key=lambda z: z.distance_km_to(lat, lng))
        serializer = self.get_serializer(zones, many=True, context={'lat': lat, 'lng': lng})
        return Response(serializer.data)


class IncidentReportViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IncidentReport.objects.all().order_by('-created_at')


# ---------------------------------------------------------------------------
# SOS — the core emergency flow
# ---------------------------------------------------------------------------
class SOSAlertViewSet(viewsets.ModelViewSet):
    serializer_class = SOSAlertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head']  # alerts are only created/read/resolved via actions

    def get_queryset(self):
        return SOSAlert.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """POST /api/sos/  -> trigger a new SOS alert and fan out notifications
        to every emergency contact, in priority order."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = serializer.save(user=request.user, status=SOSAlert.Status.ACTIVE)

        contacts = request.user.emergency_contacts.all().order_by('notify_order', 'priority')
        notifications = [
            SOSNotification(alert=alert, contact=c, status=SOSNotification.Status.SENT, sent_at=timezone.now())
            for c in contacts
        ]
        SOSNotification.objects.bulk_create(notifications)

        # In production this is where an async task (Celery) would call the
        # SMS/push/email provider and local emergency dispatch integration.

        out = self.get_serializer(alert)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """POST /api/sos/{id}/resolve/  -> user confirms they're safe."""
        alert = self.get_object()
        alert.status = SOSAlert.Status.CANCELLED if request.data.get('cancelled') else SOSAlert.Status.RESOLVED
        alert.resolved_at = timezone.now()
        alert.save(update_fields=['status', 'resolved_at'])
        return Response(self.get_serializer(alert).data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """GET /api/sos/active/ -> the caller's current in-progress alert, if any."""
        alert = self.get_queryset().filter(status=SOSAlert.Status.ACTIVE).first()
        if not alert:
            return Response(None)
        return Response(self.get_serializer(alert).data)


# ---------------------------------------------------------------------------
# Check-ins & geofences
# ---------------------------------------------------------------------------
class CheckInViewSet(viewsets.ModelViewSet):
    serializer_class = CheckInSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        return CheckIn.objects.filter(user=self.request.user)


class GeofenceZoneViewSet(viewsets.ModelViewSet):
    serializer_class = GeofenceZoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GeofenceZone.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# Chat / AI assistant
# ---------------------------------------------------------------------------
class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """POST /api/chat/ {"message": "..."}  -> stores the user's message,
        generates a bot reply, stores that too, and returns both."""
        text = request.data.get('message', '').strip()
        if not text:
            return Response({'detail': 'message is required'}, status=400)

        user_msg = ChatMessage.objects.create(user=request.user, sender=ChatMessage.Sender.USER, message=text)
        reply_text, intent = get_bot_reply(text)
        bot_msg = ChatMessage.objects.create(
            user=request.user, sender=ChatMessage.Sender.BOT, message=reply_text, intent=intent
        )
        return Response(
            {
                'user_message': ChatMessageSerializer(user_msg).data,
                'bot_message': ChatMessageSerializer(bot_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )
