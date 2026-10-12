import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nnck_club.settings')
django.setup()

from django.contrib.auth.models import User
from club.models import UserProfile, WorkoutCategory

def seed_categories():
    categories = [
        {
            'name': 'Easy Run',
            'category_type': 'easy_run',
            'description': 'Aerobic recovery and base aerobic foundation building run at conversation pace.',
            'color_code': '#34a853',
            'icon': 'bi-heart-pulse-fill'
        },
        {
            'name': 'Tempo Run',
            'category_type': 'tempo_run',
            'description': 'Lactate threshold endurance training at steady, comfortably hard pace.',
            'color_code': '#fdbb11',
            'icon': 'bi-speedometer2'
        },
        {
            'name': 'Interval Training',
            'category_type': 'interval',
            'description': 'High-intensity interval repeats for VO2 max enhancement and running speed.',
            'color_code': '#f26522',
            'icon': 'bi-lightning-charge-fill'
        },
        {
            'name': 'Core Training',
            'category_type': 'core',
            'description': 'Core stability, hip flexors, planks, and rotational torso endurance for running posture.',
            'color_code': '#0dcaf0',
            'icon': 'bi-shield-shaded'
        },
        {
            'name': 'Strength Training',
            'category_type': 'strength',
            'description': 'Lower body functional strength, lunges, squats, calf raises, and single-leg stability.',
            'color_code': '#e02874',
            'icon': 'bi-fire'
        },
        {
            'name': 'Warmup',
            'category_type': 'warmup',
            'description': 'Dynamic pre-run mobility, leg swings, A-skips, and activation exercises.',
            'color_code': '#ffc107',
            'icon': 'bi-arrow-clockwise'
        },
        {
            'name': 'Cooldown',
            'category_type': 'cooldown',
            'description': 'Static stretching, foam rolling, hamstring and calf flexibility release.',
            'color_code': '#20c997',
            'icon': 'bi-snow'
        },
        {
            'name': 'Custom Workout',
            'category_type': 'custom',
            'description': 'Specialized cross-training, track sessions, or custom routines assigned by Coach.',
            'color_code': '#6f42c1',
            'icon': 'bi-star-fill'
        },
    ]

    for cat_data in categories:
        WorkoutCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
    print(f"Verified {len(categories)} workout categories.")

def seed_coach():
    coach, created = User.objects.get_or_create(username='coach_nnck')
    coach.first_name = 'CHANDRAKANTH'
    coach.last_name = 'M'
    coach.email = 'chandrakanth@nnck.club'
    if created or not coach.has_usable_password():
        coach.set_password(os.environ.get('COACH_PASSWORD', 'coach123'))
    coach.is_staff = True
    coach.is_superuser = True
    coach.save()

    profile, _ = UserProfile.objects.get_or_create(user=coach)
    profile.role = 'coach'
    profile.profile_photo = 'profiles/chandrakanth_coach.png'
    profile.bio = """Head Coach & Founder · Nanu Nimma CK Run Club

Nanu Nimma CK is both a competitive runner and a running coach based in Bengaluru. His journey began as an athlete, and through years of consistent training and racing, he developed a deep understanding of what it takes to improve as a runner.

Before becoming a coach, he first built his foundation as a runner, achieving strong performances including a sub-2:30 marathon and sub-72-minute half marathon. These experiences shape the way he approaches coaching today.

"Athlete first. Winning comes second." His focus is not only on results but on helping runners develop discipline, consistency, and a long-term approach to training.

Certifications:
• ACSM Certified
• AFI Pre-Level 1

What makes his coaching unique is the balance between scientific knowledge and real racing experience. Having trained as a competitive athlete himself, he understands the demands of structured running training.

As a Physical Education teacher, he also understands the challenges faced by working professionals who want to pursue running seriously while managing their daily responsibilities.

Through Run With Nimma CK, his goal is to build a strong running community where athletes train together, support each other, and continue improving — step by step.

Run Together. Grow Together."""
    profile.save()
    print("Verified Head Coach CHANDRAKANTH M profile.")

if __name__ == '__main__':
    seed_categories()
    seed_coach()
    print("Initial NNCK seed completed successfully.")
