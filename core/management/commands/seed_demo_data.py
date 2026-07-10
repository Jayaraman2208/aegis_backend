from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from core.models import SafetyZone, EmergencyContact

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds a demo traveler account, contacts, and safety zones matching the frontend prototype.'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='demo_traveler',
            defaults=dict(
                email='demo@aegis.app', blood_type='O+', allergies='Penicillin',
                medical_conditions='Asthma', medications='Albuterol',
                preferred_language='en', location_sharing_enabled=True,
                offline_maps_downloaded=True,
            ),
        )
        if created:
            user.set_password('demo12345')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created demo_traveler / demo12345'))

        contacts = [
            dict(name='David Lin', relationship='Spouse', phone_number='+1-555-0142', priority=EmergencyContact.Priority.PRIMARY, notify_order=0),
            dict(name='Dr. Rita Chen', relationship='Sister', phone_number='+1-555-0198', priority=EmergencyContact.Priority.SECONDARY, notify_order=1),
            dict(name='Embassy Hotline', relationship='', phone_number='+1-555-0100', priority=EmergencyContact.Priority.ESCALATION, notify_order=2),
        ]
        for c in contacts:
            EmergencyContact.objects.get_or_create(user=user, name=c['name'], defaults=c)

        zones = [
            dict(name='Fountain Square', latitude=13.0850, longitude=80.2701,
                 risk_level=SafetyZone.RiskLevel.SAFE, safety_score=88,
                 description='Well-lit, high foot traffic'),
            dict(name='Market Lane', latitude=13.0870, longitude=80.2730,
                 risk_level=SafetyZone.RiskLevel.CAUTION, safety_score=54,
                 description='Dim lighting after 8pm', is_night_risk=True),
            dict(name='Old Depot Rd', latitude=13.0800, longitude=80.2750,
                 risk_level=SafetyZone.RiskLevel.RISK, safety_score=21,
                 description='2 verified reports in the last 24h'),
            dict(name='Riverside Walk', latitude=13.0790, longitude=80.2680,
                 risk_level=SafetyZone.RiskLevel.SAFE, safety_score=91,
                 description='Patrolled tourist zone'),
        ]
        created = 0
        for z in zones:
            _, was_created = SafetyZone.objects.get_or_create(name=z['name'], defaults=z)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} new safety zones (of {len(zones)} total). Demo login: demo_traveler / demo12345'))
