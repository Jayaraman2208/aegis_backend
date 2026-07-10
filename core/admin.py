from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    User, EmergencyContact, SafetyZone, IncidentReport, SOSAlert,
    SOSNotification, CheckIn, GeofenceZone, ChatMessage,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Traveler profile', {
            'fields': (
                'phone_number', 'nationality', 'preferred_language',
                'blood_type', 'allergies', 'medical_conditions', 'medications',
                'location_sharing_enabled', 'offline_maps_downloaded',
                'last_latitude', 'last_longitude', 'last_seen_at',
            )
        }),
    )
    list_display = ['username', 'email', 'phone_number', 'nationality', 'is_staff']


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'relationship', 'priority', 'phone_number']
    list_filter = ['priority']
    search_fields = ['name', 'user__username']


@admin.register(SafetyZone)
class SafetyZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'risk_level', 'safety_score', 'is_night_risk', 'updated_at']
    list_filter = ['risk_level', 'is_night_risk']
    search_fields = ['name']


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'severity', 'zone', 'verified', 'created_at']
    list_filter = ['severity', 'verified']


class SOSNotificationInline(admin.TabularInline):
    model = SOSNotification
    extra = 0
    readonly_fields = ['contact', 'status', 'sent_at']


@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'trigger_method', 'triggered_at']
    list_filter = ['status', 'trigger_method']
    inlines = [SOSNotificationInline]


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ['user', 'location_name', 'created_at']


@admin.register(GeofenceZone)
class GeofenceZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'radius_meters', 'is_active']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'sender', 'intent', 'created_at']
    list_filter = ['sender', 'intent']
