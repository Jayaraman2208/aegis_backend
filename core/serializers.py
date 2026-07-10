from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    EmergencyContact, SafetyZone, IncidentReport, SOSAlert,
    SOSNotification, CheckIn, GeofenceZone, ChatMessage,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'nationality',
            'preferred_language', 'blood_type', 'allergies',
            'medical_conditions', 'medications',
            'location_sharing_enabled', 'offline_maps_downloaded',
            'last_latitude', 'last_longitude', 'last_seen_at',
        ]
        read_only_fields = ['id', 'last_seen_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number', 'nationality']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'name', 'relationship', 'phone_number', 'email', 'priority', 'notify_order']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SafetyZoneSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = SafetyZone
        fields = [
            'id', 'name', 'latitude', 'longitude', 'radius_meters',
            'risk_level', 'safety_score', 'description', 'is_night_risk',
            'updated_at', 'distance_km',
        ]

    def get_distance_km(self, obj):
        lat = self.context.get('lat')
        lng = self.context.get('lng')
        if lat is None or lng is None:
            return None
        return round(obj.distance_km_to(lat, lng), 2)


class IncidentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = [
            'id', 'zone', 'latitude', 'longitude', 'severity',
            'description', 'is_anonymous', 'verified', 'created_at',
        ]
        read_only_fields = ['verified', 'created_at']

    def create(self, validated_data):
        request = self.context['request']
        if not validated_data.get('is_anonymous'):
            validated_data['reporter'] = request.user
        return super().create(validated_data)


class SOSNotificationSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)

    class Meta:
        model = SOSNotification
        fields = ['id', 'contact', 'contact_name', 'status', 'sent_at']


class SOSAlertSerializer(serializers.ModelSerializer):
    notifications = SOSNotificationSerializer(many=True, read_only=True)

    class Meta:
        model = SOSAlert
        fields = [
            'id', 'status', 'trigger_method', 'latitude', 'longitude',
            'address', 'notes', 'triggered_at', 'resolved_at', 'notifications',
        ]
        read_only_fields = ['id', 'status', 'triggered_at', 'resolved_at', 'notifications']


class CheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = ['id', 'latitude', 'longitude', 'location_name', 'note', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GeofenceZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeofenceZone
        fields = ['id', 'name', 'latitude', 'longitude', 'radius_meters', 'is_active', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'intent', 'created_at']
        read_only_fields = ['sender', 'intent', 'created_at']
