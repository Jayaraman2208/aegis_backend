import math
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Traveler account. Extends Django's built-in auth user with the
    profile / medical-ID fields shown on the app's 'You' screen."""

    class Language(models.TextChoices):
        ENGLISH = 'en', 'English'
        HINDI = 'hi', 'Hindi'
        SPANISH = 'es', 'Spanish'
        FRENCH = 'fr', 'French'
        GERMAN = 'de', 'German'
        CHINESE = 'zh', 'Chinese'
        JAPANESE = 'ja', 'Japanese'
        ARABIC = 'ar', 'Arabic'
        RUSSIAN = 'ru', 'Russian'
        PORTUGUESE = 'pt', 'Portuguese'
        ITALIAN = 'it', 'Italian'
        KOREAN = 'ko', 'Korean'

    phone_number = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=80, blank=True)
    preferred_language = models.CharField(max_length=2, choices=Language.choices, default=Language.ENGLISH)

    # Medical ID card
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)

    # Preferences
    location_sharing_enabled = models.BooleanField(default=True)
    offline_maps_downloaded = models.BooleanField(default=False)

    # Live status (updated by the app periodically)
    last_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username


class EmergencyContact(models.Model):
    """A person notified when this user triggers an SOS alert."""

    class Priority(models.TextChoices):
        PRIMARY = 'primary', 'Primary'
        SECONDARY = 'secondary', 'Secondary'
        ESCALATION = 'escalation', 'Escalation'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=60, blank=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.PRIMARY)
    notify_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['notify_order', 'priority']

    def __str__(self):
        return f'{self.name} ({self.get_priority_display()}) — {self.user.username}'


class SafetyZone(models.Model):
    """A geographic area with a computed safety score, used to render the
    heat-map and drive route/area risk warnings."""

    class RiskLevel(models.TextChoices):
        SAFE = 'safe', 'Safe'
        CAUTION = 'caution', 'Caution'
        RISK = 'risk', 'Avoid'

    name = models.CharField(max_length=150)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField(default=300)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.SAFE)
    safety_score = models.PositiveSmallIntegerField(
        default=80, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    description = models.CharField(max_length=255, blank=True)
    is_night_risk = models.BooleanField(default=False, help_text='Risk level increases after sunset')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [models.Index(fields=['latitude', 'longitude'])]

    def __str__(self):
        return f'{self.name} [{self.risk_level}:{self.safety_score}]'

    def distance_km_to(self, lat, lng):
        """Great-circle distance via the haversine formula (no GIS extensions required)."""
        r = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [float(self.latitude), float(self.longitude), float(lat), float(lng)])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return r * 2 * math.asin(math.sqrt(a))


class IncidentReport(models.Model):
    """Community-submitted safety report, feeding into zone risk scores."""

    class Severity(models.TextChoices):
        MINOR = 'minor', 'Minor'
        MODERATE = 'moderate', 'Moderate'
        CRITICAL = 'critical', 'Critical'

    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incident_reports')
    zone = models.ForeignKey(SafetyZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MINOR)
    description = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_severity_display()} report near {self.zone or "unmapped zone"}'


class SOSAlert(models.Model):
    """An emergency event triggered by a user — the core safety-net record."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        RESOLVED = 'resolved', 'Resolved'
        CANCELLED = 'cancelled', 'Cancelled'

    class TriggerMethod(models.TextChoices):
        BUTTON = 'button', 'Button hold'
        SHAKE = 'shake', 'Shake gesture'
        VOICE = 'voice', 'Voice command'
        SILENT = 'silent', 'Silent mode'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sos_alerts')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    trigger_method = models.CharField(max_length=10, choices=TriggerMethod.choices, default=TriggerMethod.BUTTON)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f'SOS[{self.status}] {self.user.username} @ {self.triggered_at:%Y-%m-%d %H:%M}'


class SOSNotification(models.Model):
    """Delivery record of an SOS alert to one emergency contact."""

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        FAILED = 'failed', 'Failed'

    alert = models.ForeignKey(SOSAlert, on_delete=models.CASCADE, related_name='notifications')
    contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE, related_name='sos_notifications')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['alert', 'contact__notify_order']

    def __str__(self):
        return f'{self.alert_id} -> {self.contact.name} [{self.status}]'


class CheckIn(models.Model):
    """Manual 'I'm here / I'm safe' check-in at a location."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_ins')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_name = models.CharField(max_length=150, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} checked in at {self.location_name or "location"}'


class GeofenceZone(models.Model):
    """A user-defined safe zone (e.g. hotel) that raises an alert on exit."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='geofences')
    name = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField(default=150)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.user.username})'


class ChatMessage(models.Model):
    """A single turn in the multilingual AI assistant conversation."""

    class Sender(models.TextChoices):
        USER = 'user', 'User'
        BOT = 'bot', 'Bot'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.CharField(max_length=4, choices=Sender.choices)
    message = models.TextField()
    intent = models.CharField(max_length=40, blank=True, help_text='Detected intent, e.g. find_hospital')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.sender}] {self.message[:40]}'
