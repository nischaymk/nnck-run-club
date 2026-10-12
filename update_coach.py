import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nnck_club.settings')
django.setup()

from django.contrib.auth.models import User
from club.models import UserProfile

coach, _ = User.objects.get_or_create(username='coach_nnck')
coach.first_name = 'CHANDRAKANTH'
coach.last_name = 'M'
coach.email = 'chandrakanth@nnck.club'
coach.set_password('coach123')
coach.is_staff = True
coach.is_superuser = True
coach.save()

profile, _ = UserProfile.objects.get_or_create(user=coach)
profile.role = 'coach'
profile.target_race = ''
profile.target_pace = ''
profile.weekly_mileage_target = 0
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

print("Coach CHANDRAKANTH M profile updated successfully with photo and credentials!")
