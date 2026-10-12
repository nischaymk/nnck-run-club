from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from club.models import WorkoutCategory, UserProfile, WorkoutAssignment, WorkoutSubmission
from datetime import date, timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds initial sample data for NNCK Run Club'

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")
        categories_data = [
            ('Warmup', 'warmup', 'Dynamic stretches, leg swings, activation drills', '#ffb703', 'bi-arrow-clockwise'),
            ('Easy Run', 'easy_run', 'Zone 2 aerobic base building, conversational pace', '#8ecae6', 'bi-person-walking'),
            ('Tempo Run', 'tempo_run', 'Comfortably hard sustained threshold effort', '#fb8500', 'bi-speedometer2'),
            ('Interval Training', 'interval_training', 'High intensity track repeats, speedwork with recovery', '#e63946', 'bi-lightning-charge-fill'),
            ('Strength Training', 'strength_training', 'Lower body, glutes, calf, and hamstring resistance work', '#06d6a0', 'bi-universal-access'),
            ('Core Training', 'core_training', 'Planks, hollow holds, stability for running posture', '#118ab2', 'bi-shield-shaded'),
            ('Cooldown', 'cooldown', 'Static stretching, jog down, foam rolling', '#90e0ef', 'bi-snow'),
            ('Custom Workout', 'custom', 'Bespoke cross-training, hill sprints, progression run', '#d90429', 'bi-stars'),
        ]

        cat_objs = {}
        for name, c_type, desc, color, icon in categories_data:
            cat, _ = WorkoutCategory.objects.get_or_create(
                name=name,
                defaults={
                    'category_type': c_type,
                    'description': desc,
                    'color_code': color,
                    'icon': icon
                }
            )
            cat_objs[name] = cat

        # 1. Coach / Admin User
        coach_user, created = User.objects.get_or_create(username='coach_nnck', defaults={
            'first_name': 'Naveen',
            'last_name': 'Kumar',
            'email': 'coach@nnck.club',
            'is_staff': True,
            'is_superuser': True,
        })
        if created:
            coach_user.set_password('coach123')
            coach_user.save()
            UserProfile.objects.create(
                user=coach_user,
                role='coach',
                phone='+91 98888 12345',
                target_race='Head Coach & Ultra Runner',
                target_pace='4:15 /km',
                weekly_mileage_target=60.0,
                bio='Head Coach at NNCK Run Club. Passionate about aerobic foundation, cadence, injury prevention and marathon training!'
            )

        # 2. Runner 1: Pavan
        runner1, created = User.objects.get_or_create(username='pavan_runner', defaults={
            'first_name': 'Pavan',
            'last_name': 'K',
            'email': 'pavan@nnck.club',
        })
        if created:
            runner1.set_password('runner123')
            runner1.save()
            UserProfile.objects.create(
                user=runner1,
                role='runner',
                phone='+91 99000 54321',
                target_race='Bengaluru Half Marathon',
                target_pace='5:20 /km',
                weekly_mileage_target=35.0,
                bio='Targeting a sub-1:55 Half Marathon this season. Love early morning club group runs!'
            )

        # 3. Runner 2: Anita
        runner2, created = User.objects.get_or_create(username='anita_nnck', defaults={
            'first_name': 'Anita',
            'last_name': 'Rao',
            'email': 'anita@nnck.club',
        })
        if created:
            runner2.set_password('runner123')
            runner2.save()
            UserProfile.objects.create(
                user=runner2,
                role='runner',
                phone='+91 98111 22334',
                target_race='TCS World 10K',
                target_pace='5:45 /km',
                weekly_mileage_target=25.0,
                bio='Passionate runner aiming for a 55-minute 10K finish. Believer in "Run Together • Grow Together".'
            )

        today = date.today()
        tomorrow = today + timedelta(days=1)

        # 4. Tomorrow's Workout for Runner 1
        workout_tomorrow, _ = WorkoutAssignment.objects.get_or_create(
            coach=coach_user,
            runner=runner1,
            scheduled_date=tomorrow,
            title='8K Progressive Tempo Run',
            defaults={
                'category': cat_objs['Tempo Run'],
                'target_distance': Decimal('8.0'),
                'target_duration': 44,
                'target_pace': '5:20 - 4:55 /km',
                'intensity_level': 'high',
                'description': '1. Warmup: 1.5 km easy jog + dynamic leg drills.\n2. Main block: 5 km progressive tempo starting at 5:20/km and cutting down 5s each km down to 4:55/km.\n3. Cooldown: 1.5 km jog + post-run calf and hamstring stretch.',
                'notes': 'Keep cadence above 175 spm. Hydrate with electrolyte 30 mins before the start.'
            }
        )

        # 5. Tomorrow's Workout Broadcast to All Runners
        WorkoutAssignment.objects.get_or_create(
            coach=coach_user,
            runner=None,
            scheduled_date=tomorrow,
            title='Club Morning Strides & Core Strength',
            defaults={
                'category': cat_objs['Core Training'],
                'target_distance': Decimal('5.0'),
                'target_duration': 40,
                'target_pace': '5:45 /km',
                'intensity_level': 'moderate',
                'description': '1. Easy aerobic run: 5 km conversational pace.\n2. 4x100m smooth strides on turf.\n3. 15-minute core circuit: 3 sets of 45s Plank, 20 Russian Twists, 15 Bird-Dogs.',
                'notes': 'Focus on tall running posture and relaxed shoulders.'
            }
        )

        # 6. Today's Workout
        workout_today, _ = WorkoutAssignment.objects.get_or_create(
            coach=coach_user,
            runner=None,
            scheduled_date=today,
            title='7K Aerobic Base Morning Run',
            defaults={
                'category': cat_objs['Easy Run'],
                'target_distance': Decimal('7.0'),
                'target_duration': 40,
                'target_pace': '5:35 /km',
                'intensity_level': 'low',
                'description': 'Continuous comfortable aerobic run in Zone 2. Conversational effort.',
                'notes': 'Post workout stretch for hip flexors.'
            }
        )

        # Sample Approved Submission for runner 1
        WorkoutSubmission.objects.get_or_create(
            runner=runner1,
            assignment=workout_today,
            defaults={
                'completed_distance': Decimal('7.20'),
                'completed_duration_minutes': Decimal('39.5'),
                'avg_pace': '5:29 /km',
                'avg_heart_rate': 148,
                'screenshot': 'images/logo.jpg',  # sample image
                'runner_notes': 'Felt very smooth throughout the entire 7.2 km loop!',
                'status': 'approved',
                'verified_by': coach_user,
                'coach_feedback': 'Superb pace discipline! Distance verified and added to your profile mileage.',
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded NNCK Club categories, profiles, and workouts!'))
