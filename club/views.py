from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from datetime import date, timedelta, datetime
from decimal import Decimal

from .models import UserProfile, WorkoutAssignment, WorkoutCategory, WorkoutSubmission, ProofScreenshot
from .forms import (
    RunnerRegistrationForm, UserProfileForm, WorkoutAssignmentForm,
    WorkoutCategoryForm, WorkoutSubmissionForm,
    StyledPasswordResetForm, StyledSetPasswordForm
)


def password_reset_request_view(request):
    """Handles requesting a password reset email."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = StyledPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email__iexact=email, is_active=True)
            dev_reset_url = None
            
            for user in associated_users:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                context = {
                    'user': user,
                    'reset_url': reset_url,
                    'domain': request.get_host(),
                    'protocol': 'https' if request.is_secure() else 'http',
                }
                subject = "[NNCK RUN CLUB] Password Reset Request"
                message = render_to_string('club/password_reset_email.html', context)
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nnckrunclub.com'),
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                
                if settings.DEBUG and not dev_reset_url:
                    dev_reset_url = reset_url
                    
            if settings.DEBUG and dev_reset_url:
                request.session['dev_password_reset_url'] = dev_reset_url
                
            return redirect('password_reset_done')
    else:
        form = StyledPasswordResetForm()
        
    return render(request, 'club/password_reset.html', {'form': form})


def password_reset_done_view(request):
    """Informs the user that password reset instructions were sent."""
    dev_reset_url = request.session.pop('dev_password_reset_url', None) if settings.DEBUG else None
    return render(request, 'club/password_reset_done.html', {'dev_reset_url': dev_reset_url})


def password_reset_confirm_view(request, uidb64, token):
    """Validates the reset token and allows the user to choose a new password."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = StyledSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been reset successfully! You can now sign in.")
                return redirect('password_reset_complete')
        else:
            form = StyledSetPasswordForm(user)
        return render(request, 'club/password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        return render(request, 'club/password_reset_confirm.html', {'validlink': False})


def password_reset_complete_view(request):
    """Displays confirmation that the password was reset successfully."""
    return render(request, 'club/password_reset_complete.html')


def index_view(request):
    """Landing / Entrance: Displays opening screen with club branding, motto, and sign in/register modal."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    register_form = RunnerRegistrationForm()
    return render(request, 'club/landing.html', {
        'register_form': register_form,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! Let's lace up!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            
    return redirect('index')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RunnerRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            # Create runner user profile
            UserProfile.objects.create(
                user=user,
                role='runner',
                phone=form.cleaned_data.get('phone', '')
            )
            login(request, user)
            messages.success(request, f"Welcome to NNCK Run Club, {user.first_name}! You are now part of the pack!")
            return redirect('dashboard')
        else:
            return render(request, 'club/landing.html', {'register_form': form, 'show_register': True})
            
    return redirect('index')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out. Keep running!")
    return redirect('index')


@login_required
def dashboard_view(request):
    """
    User Dashboard for Runners:
    - If user is Coach, automatically redirect to coach_portal
    - Next day's workout uploaded by Coach (highlighted)
    - Today's workout assigned by Coach
    - Verification status of submitted workouts
    - Verified distance counter (updated when coach approves screenshot)
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Coach has no workouts to do — their duty is to assign, verify, and manage
    if profile.is_coach:
        return redirect('coach_portal')
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Workout filter: directly assigned, or part of assigned group, or broadcast to all
    assignment_filter = Q(runner=user) | Q(runners=user) | (Q(runner__isnull=True) & Q(runners__isnull=True))

    # Next day workouts assigned by coach
    next_day_workouts = WorkoutAssignment.objects.filter(
        scheduled_date=tomorrow
    ).filter(assignment_filter).distinct()

    # Today workouts assigned by coach
    today_workouts = WorkoutAssignment.objects.filter(
        scheduled_date=today
    ).filter(assignment_filter).distinct()

    # Upcoming workouts beyond tomorrow
    upcoming_workouts = WorkoutAssignment.objects.filter(
        scheduled_date__gt=tomorrow,
        scheduled_date__lte=today + timedelta(days=7)
    ).filter(assignment_filter).distinct().order_by('scheduled_date')

    # Submissions made by this runner
    submissions = WorkoutSubmission.objects.filter(runner=user).order_by('-created_at')
    recent_submissions = submissions[:5]

    # Verified distance calculations
    approved_submissions = submissions.filter(status='approved')
    total_verified_km = approved_submissions.aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')

    # Weekly verified distance (Monday of this week onwards)
    this_week_start = today - timedelta(days=today.weekday())
    weekly_verified_km = approved_submissions.filter(
        assignment__scheduled_date__gte=this_week_start
    ).aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')

    target_mileage = profile.weekly_mileage_target or Decimal('30.0')
    mileage_percentage = min(int((weekly_verified_km / target_mileage) * 100), 100) if target_mileage > 0 else 0

    # Get set of workout IDs that runner already submitted
    submitted_assignment_ids = set(submissions.values_list('assignment_id', flat=True))

    return render(request, 'club/dashboard.html', {
        'profile': profile,
        'next_day_workouts': next_day_workouts,
        'today_workouts': today_workouts,
        'upcoming_workouts': upcoming_workouts,
        'recent_submissions': recent_submissions,
        'submitted_assignment_ids': submitted_assignment_ids,
        'total_verified_km': total_verified_km,
        'weekly_verified_km': weekly_verified_km,
        'approved_count': approved_submissions.count(),
        'pending_count': submissions.filter(status='pending').count(),
        'mileage_percentage': mileage_percentage,
        'tomorrow_date': tomorrow,
        'today_date': today,
    })


@login_required
def submit_workout_proof_view(request, assignment_id):
    """
    Runners submit screenshot proofs and performance data for an assigned workout.
    Supports MULTIPLE proofs per workout with NO LIMIT.
    """
    assignment = get_object_or_404(WorkoutAssignment, id=assignment_id)
    
    # Verify assignment is intended for this user, their group, or broadcast
    if assignment.runner and assignment.runner != request.user and not assignment.runners.filter(id=request.user.id).exists():
        messages.error(request, "This workout was not assigned to you.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = WorkoutSubmissionForm(request.POST, request.FILES)
        uploaded_files = request.FILES.getlist('screenshots')
        
        if len(uploaded_files) > 10:
            messages.error(request, "Maximum of 10 screenshot proofs allowed per submission.")
            return render(request, 'club/submit_proof.html', {
                'form': form,
                'assignment': assignment,
                'existing_proofs': WorkoutSubmission.objects.filter(runner=request.user, assignment=assignment).order_by('-created_at'),
            })

        if form.is_valid():
            sub = form.save(commit=False)
            sub.runner = request.user
            sub.assignment = assignment
            sub.status = 'pending'
            
            # If files were uploaded via multi-file input, assign first to screenshot
            if uploaded_files:
                sub.screenshot = uploaded_files[0]
            sub.save()
            
            # Save all uploaded files (up to 10) into ProofScreenshot
            for f in uploaded_files[:10]:
                ProofScreenshot.objects.create(submission=sub, image=f)

            messages.success(request, f"Workout proof for '{assignment.title}' uploaded successfully with {len(uploaded_files) or 1} screenshot(s)! Distance: {sub.completed_distance} km. Coach will verify shortly.")
            return redirect('dashboard')
    else:
        initial = {
            'completed_distance': assignment.target_distance or '',
            'completed_duration_minutes': assignment.target_duration or '',
            'avg_pace': assignment.target_pace or '',
        }
        form = WorkoutSubmissionForm(initial=initial)

    # All proofs previously uploaded by this runner for this assignment
    existing_proofs = WorkoutSubmission.objects.filter(runner=request.user, assignment=assignment).order_by('-created_at')

    return render(request, 'club/submit_proof.html', {
        'form': form,
        'assignment': assignment,
        'existing_proofs': existing_proofs,
    })


@login_required
def profile_view(request):
    """Runner user profile settings (bio, profile picture, goals)."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()

            form.save()
            messages.success(request, "Your profile photo, bio, and settings have been updated!")
            return redirect('profile')
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = UserProfileForm(instance=profile, initial=initial_data)

    return render(request, 'club/profile.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def club_runners_view(request):
    """
    Community directory: runners can see other runners in the club,
    view their bio, profile photo, verified distance, and target goals.
    """
    runners = User.objects.filter(is_active=True).select_related('profile').annotate(
        approved_submissions_count=Count('workout_submissions', filter=Q(workout_submissions__status='approved'))
    ).order_by('-date_joined')

    return render(request, 'club/runners_directory.html', {
        'runners': runners,
    })


@login_required
def leaderboard_view(request):
    """
    Weekly Leaderboard:
    Ranks runners based on verified weekly completed distance.
    Coaches are excluded from the competition leaderboard.
    """
    today = date.today()
    date_param = request.GET.get('date', '').strip()
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    this_week_start = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = this_week_start + timedelta(days=6)
    prev_week = this_week_start - timedelta(days=7)
    next_week = this_week_start + timedelta(days=7)
    is_current_week = (this_week_start <= today <= end_of_week)

    # Fetch athletes and annotate their weekly verified mileage
    athletes = User.objects.filter(
        is_active=True
    ).exclude(
        profile__role='coach'
    ).exclude(
        is_staff=True
    ).exclude(
        is_superuser=True
    ).select_related('profile').annotate(
        week_km=Sum(
            'workout_submissions__completed_distance',
            filter=Q(
                workout_submissions__status='approved',
                workout_submissions__assignment__scheduled_date__gte=this_week_start,
                workout_submissions__assignment__scheduled_date__lte=end_of_week
            )
        ),
        total_km=Sum(
            'workout_submissions__completed_distance',
            filter=Q(workout_submissions__status='approved')
        ),
        week_runs=Count(
            'workout_submissions',
            filter=Q(
                workout_submissions__status='approved',
                workout_submissions__assignment__scheduled_date__gte=this_week_start,
                workout_submissions__assignment__scheduled_date__lte=end_of_week
            )
        )
    )

    # Sort in python to handle None values as Decimal(0)
    ranked_athletes = sorted(
        athletes,
        key=lambda u: (u.week_km or Decimal('0.0'), u.total_km or Decimal('0.0')),
        reverse=True
    )

    # Assign ranks
    leaderboard_data = []
    for rank, athlete in enumerate(ranked_athletes, 1):
        leaderboard_data.append({
            'rank': rank,
            'athlete': athlete,
            'week_km': athlete.week_km or Decimal('0.0'),
            'total_km': athlete.total_km or Decimal('0.0'),
            'week_runs': athlete.week_runs or 0,
        })

    # Club total this week
    club_total_week_km = sum([entry['week_km'] for entry in leaderboard_data])

    return render(request, 'club/leaderboard.html', {
        'leaderboard': leaderboard_data,
        'this_week_start': this_week_start,
        'end_of_week': end_of_week,
        'prev_week': prev_week,
        'next_week': next_week,
        'selected_date': selected_date,
        'today': today,
        'is_current_week': is_current_week,
        'club_total_week_km': club_total_week_km,
        'runners_count': len(leaderboard_data),
    })


@login_required
def runner_detail_view(request, user_id):
    """Public athlete card showing runner bio, picture, and verified achievements."""
    target_user = get_object_or_404(User, id=user_id, is_active=True)
    target_profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    verified_submissions = WorkoutSubmission.objects.filter(runner=target_user, status='approved').order_by('-created_at')
    total_km = verified_submissions.aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')

    return render(request, 'club/runner_detail.html', {
        'target_user': target_user,
        'target_profile': target_profile,
        'verified_submissions': verified_submissions[:10],
        'total_km': total_km,
    })


@login_required
def workout_history_view(request):
    """Workout tracking history showing submitted proofs, status, and coach feedback with weekly filter."""
    user = request.user
    today = date.today()
    date_param = request.GET.get('date', '').strip()
    show_all = request.GET.get('all') == '1'

    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    is_current_week = (week_start <= today <= week_end)

    all_submissions = WorkoutSubmission.objects.filter(runner=user).select_related('assignment', 'assignment__category')
    total_verified_km = all_submissions.filter(status='approved').aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')
    pending_count = all_submissions.filter(status='pending').count()
    approved_count = all_submissions.filter(status='approved').count()

    if date_param and not show_all:
        submissions = all_submissions.filter(
            assignment__scheduled_date__gte=week_start,
            assignment__scheduled_date__lte=week_end
        ).order_by('-created_at')
    else:
        submissions = all_submissions.order_by('-created_at')

    return render(request, 'club/workout_history.html', {
        'submissions': submissions,
        'total_verified_km': total_verified_km,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'selected_date': selected_date,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': prev_week,
        'next_week': next_week,
        'is_current_week': is_current_week,
        'show_all': show_all,
        'has_date_filter': bool(date_param and not show_all),
        'today': today,
    })


# ==========================================
# COACH & ADMIN PORTAL
# ==========================================

@login_required
def coach_portal_view(request):
    """Coach Admin Portal: overview of runners, pending screenshot verifications, and assignment shortcuts."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Access restricted. Only coaches and administrators can enter this portal.")
        return redirect('dashboard')

    # Only athletes/runners (exclude coaches and staff from the athlete roster)
    runners = User.objects.filter(
        is_active=True
    ).exclude(
        profile__role='coach'
    ).exclude(
        is_staff=True
    ).exclude(
        is_superuser=True
    ).select_related('profile')
    pending_submissions = WorkoutSubmission.objects.filter(status='pending').select_related('runner', 'assignment', 'assignment__category').order_by('-created_at')
    recent_assigned = WorkoutAssignment.objects.select_related('runner', 'category').order_by('-scheduled_date')[:8]
    categories = WorkoutCategory.objects.all()

    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())
    club_week_km = WorkoutSubmission.objects.filter(
        status='approved',
        created_at__gte=this_week_start
    ).aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')

    return render(request, 'club/coach_portal.html', {
        'runners': runners,
        'pending_submissions': pending_submissions,
        'recent_assigned': recent_assigned,
        'categories': categories,
        'club_week_km': club_week_km,
        'total_runners_count': runners.count(),
    })


@login_required
def coach_verify_submission_view(request, submission_id):
    """
    Coach verifies/approves runner screenshot submission.
    When verified, completed distance is added to the runner's profile total.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Coach access required.")
        return redirect('dashboard')

    sub = get_object_or_404(WorkoutSubmission, id=submission_id)

    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        feedback = request.POST.get('coach_feedback', '')
        
        # Coach can adjust distance if screenshot says differently
        adjusted_distance = request.POST.get('completed_distance')
        if adjusted_distance:
            try:
                sub.completed_distance = Decimal(adjusted_distance)
            except Exception:
                pass

        if action == 'approve':
            sub.status = 'approved'
            sub.verified_by = request.user
            sub.verified_at = timezone.now()
            sub.coach_feedback = feedback
            sub.save()
            messages.success(request, f"Verified and Approved workout for {sub.runner.get_full_name() or sub.runner.username}! {sub.completed_distance} km has been added to their profile.")
        elif action == 'reject':
            sub.status = 'rejected'
            sub.verified_by = request.user
            sub.verified_at = timezone.now()
            sub.coach_feedback = feedback
            sub.save()
            messages.warning(request, f"Marked submission as revision requested for {sub.runner.username}.")

        return redirect('coach_portal')

    return render(request, 'club/coach_verify_detail.html', {
        'submission': sub,
    })


@login_required
def coach_assign_workout_view(request):
    """Coach uploads workout for a runner or all runners on daily basis."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Coach access required.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = WorkoutAssignmentForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.coach = request.user
            workout.save()
            form.save_m2m()  # Saves selected group runners ManyToMany
            
            # Message formatting
            selected_group = workout.runners.all()
            if selected_group.exists():
                names = ", ".join([u.first_name or u.username for u in selected_group])
                target = f"Group of {selected_group.count()} runners ({names})"
            elif workout.runner:
                target = workout.runner.get_full_name() or workout.runner.username
            else:
                target = "All Club Runners (Broadcast)"

            messages.success(request, f"Workout '{workout.title}' successfully assigned to {target} for {workout.scheduled_date}!")
            return redirect('coach_portal')
    else:
        runner_id = request.GET.get('runner_id')
        initial = {}
        if runner_id:
            initial['runner'] = runner_id
        form = WorkoutAssignmentForm(initial=initial)

    return render(request, 'club/coach_assign_workout.html', {'form': form})


@login_required
def coach_create_category_view(request):
    """Coach creates or manages workout categories."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Coach access required.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = WorkoutCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created successfully!")
            return redirect('coach_portal')
    else:
        form = WorkoutCategoryForm()

    categories = WorkoutCategory.objects.all()
    return render(request, 'club/coach_category.html', {
        'form': form,
        'categories': categories,
    })


@login_required
def coach_runner_analysis_view(request, runner_id):
    """Coach views runner performance tracking and all submitted screenshots."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Coach access required.")
        return redirect('dashboard')

    runner = get_object_or_404(User, id=runner_id)
    runner_profile, _ = UserProfile.objects.get_or_create(user=runner)
    submissions = WorkoutSubmission.objects.filter(runner=runner).order_by('-created_at')

    today = date.today()
    this_week = today - timedelta(days=today.weekday())

    week_km = submissions.filter(status='approved', created_at__gte=this_week).aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')
    total_km = submissions.filter(status='approved').aggregate(s=Sum('completed_distance'))['s'] or Decimal('0.0')

    assigned_workouts = WorkoutAssignment.objects.filter(
        Q(runner=runner) | Q(runner__isnull=True)
    ).order_by('-scheduled_date')[:6]

    return render(request, 'club/coach_runner_analysis.html', {
        'runner': runner,
        'runner_profile': runner_profile,
        'submissions': submissions,
        'week_km': week_km,
        'total_km': total_km,
        'assigned_workouts': assigned_workouts,
    })


@login_required
def coach_workouts_list_view(request):
    """
    Coach views posted workouts filtered by selected week/date to reduce list size.
    Can pick any date, navigate weeks (previous/current/next), or toggle to view all workouts.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Coach access required.")
        return redirect('dashboard')

    today = date.today()
    date_param = request.GET.get('date', '').strip()
    show_all = request.GET.get('all') == '1'

    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # Calculate Monday to Sunday of the selected date's week
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    is_current_week = (week_start <= today <= week_end)

    workouts_qs = WorkoutAssignment.objects.select_related('category', 'runner').prefetch_related('runners', 'submissions')
    total_posted_count = workouts_qs.count()

    if not show_all:
        workouts = workouts_qs.filter(
            scheduled_date__gte=week_start,
            scheduled_date__lte=week_end
        ).order_by('scheduled_date', '-created_at')
    else:
        workouts = workouts_qs.order_by('-scheduled_date', '-created_at')

    return render(request, 'club/coach_workouts_list.html', {
        'workouts': workouts,
        'selected_date': selected_date,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': prev_week,
        'next_week': next_week,
        'today': today,
        'is_current_week': is_current_week,
        'show_all': show_all,
        'total_posted_count': total_posted_count,
        'filtered_count': workouts.count(),
    })


@login_required
def coach_delete_workout_view(request, workout_id):
    """Coach deletes an assigned workout"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_coach:
        messages.error(request, "Coach access required.")
        return redirect('dashboard')

    workout = get_object_or_404(WorkoutAssignment, id=workout_id)
    workout.delete()
    messages.success(request, f"Workout '{workout.title}' deleted successfully.")
    return redirect('coach_workouts_list')
