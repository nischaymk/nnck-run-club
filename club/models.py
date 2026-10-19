from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('runner', 'Runner'),
        ('coach', 'Coach'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='runner')
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    profile_photo_base64 = models.TextField(blank=True, null=True, help_text="Permanent database-persisted avatar")
    bio = models.TextField(blank=True, null=True, help_text="Runner bio, motivation, or introduction")
    
    # Running goals
    target_race = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. TCS 10k, Bengaluru Marathon, Half Marathon")
    target_pace = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 5:15 min/km")
    weekly_mileage_target = models.DecimalField(max_digits=5, decimal_places=2, default=30.0, help_text="Target in km")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def avatar_url(self):
        """
        Permanent avatar URL immune to cloud ephemeral disk wipes.
        1. Returns base64 data URI stored in database if available.
        2. Falls back to profile_photo.url if available.
        3. Returns None otherwise.
        """
        if self.profile_photo_base64:
            return self.profile_photo_base64
        if self.profile_photo:
            try:
                return self.profile_photo.url
            except Exception:
                pass
        return None

    def save(self, *args, **kwargs):
        # Automatically generate permanent base64 thumbnail from profile_photo
        if self.profile_photo:
            try:
                from PIL import Image
                import io
                import base64

                f = getattr(self.profile_photo, 'file', None)
                if f:
                    try:
                        f.seek(0)
                    except Exception:
                        pass
                    img = Image.open(f)
                    img.thumbnail((300, 300))
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    self.profile_photo_base64 = f"data:image/jpeg;base64,{b64}"
                    try:
                        f.seek(0)
                    except Exception:
                        pass
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def is_coach(self):
        return self.role == 'coach' or self.user.is_staff or self.user.is_superuser

    @property
    def total_verified_distance(self):
        total = self.user.workout_submissions.filter(status='approved').aggregate(models.Sum('completed_distance'))['completed_distance__sum']
        return total or 0.0

    @property
    def weekly_verified_distance(self):
        today = date.today()
        this_week_start = today - timedelta(days=today.weekday())
        total = self.user.workout_submissions.filter(
            status='approved',
            assignment__scheduled_date__gte=this_week_start
        ).aggregate(models.Sum('completed_distance'))['completed_distance__sum']
        return total or 0.0


class WorkoutCategory(models.Model):
    CATEGORY_TYPES = [
        ('warmup', 'Warmup'),
        ('easy_run', 'Easy Run'),
        ('tempo_run', 'Tempo Run'),
        ('interval_training', 'Interval Training'),
        ('strength_training', 'Strength Training'),
        ('core_training', 'Core Training'),
        ('cooldown', 'Cooldown'),
        ('custom', 'Custom Workout'),
    ]

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES, default='easy_run')
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=20, default='#ff6b35', help_text="Hex color code for UI badge")
    icon = models.CharField(max_length=50, default='bi-stopwatch', help_text="Bootstrap icon name")

    class Meta:
        verbose_name_plural = "Workout Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkoutAssignment(models.Model):
    """
    Daily / scheduled workout created by Coach for runners.
    Can be assigned to a specific runner, multiple runners, or broadcast to all runners.
    """
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_workouts')
    runner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_workouts', null=True, blank=True,
                               help_text="Single runner target (optional)")
    runners = models.ManyToManyField(User, related_name='group_assigned_workouts', blank=True,
                                    help_text="Selected group of runners for this workout")
    category = models.ForeignKey(WorkoutCategory, on_delete=models.CASCADE, related_name='workouts')
    title = models.CharField(max_length=200)
    scheduled_date = models.DateField(default=date.today, help_text="Workout scheduled date")
    description = models.TextField(help_text="Step-by-step workout guidance, sets, reps, pace...")
    target_distance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Target distance in km")
    target_duration = models.IntegerField(null=True, blank=True, help_text="Target duration in minutes")
    target_pace = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 5:10 min/km")
    intensity_level = models.CharField(max_length=20, choices=[
        ('low', 'Low / Recovery'),
        ('moderate', 'Moderate'),
        ('high', 'High / Threshold'),
        ('max', 'Maximum / Intervals'),
    ], default='moderate')
    notes = models.TextField(blank=True, null=True, help_text="Coach's pre-run advice, hydration, warmup...")
    
    # Scheduled Release / Posting Time for workout details
    publish_date = models.DateField(null=True, blank=True, help_text="Date when workout details become visible to runners")
    publish_time = models.TimeField(null=True, blank=True, help_text="Time of day when workout details become visible to runners (e.g. 05:00 AM, 20:00)")
    publish_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Exact timestamp when workout details are released to runners. If null, posted immediately.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.scheduled_date})"

    @property
    def is_tomorrow(self):
        return self.scheduled_date == date.today() + timedelta(days=1)

    @property
    def is_today(self):
        return self.scheduled_date == date.today()

    @property
    def is_published(self):
        """Returns True if this workout is already released to runners."""
        if not self.publish_at:
            return True
        return timezone.now() >= self.publish_at

    @property
    def publish_status_display(self):
        """Human-readable publication status for badges."""
        if self.is_published:
            return "Live to Runners"
        local_dt = timezone.localtime(self.publish_at)
        return f"Scheduled for {local_dt.strftime('%d %b, %I:%M %p')}"


class WorkoutSubmission(models.Model):
    """
    Runners upload workout proofs & data when completing an assigned workout.
    Supports up to 10 screenshots per submission via ProofScreenshot model.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Coach Verification'),
        ('approved', 'Verified & Approved'),
        ('rejected', 'Revision Requested / Rejected'),
    ]

    runner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_submissions')
    assignment = models.ForeignKey(WorkoutAssignment, on_delete=models.CASCADE, related_name='submissions')
    
    # Runner submitted metrics
    completed_distance = models.DecimalField(max_digits=6, decimal_places=2, help_text="Distance completed in km")
    completed_duration_minutes = models.DecimalField(max_digits=6, decimal_places=2, help_text="Time taken in minutes")
    avg_pace = models.CharField(max_length=30, blank=True, null=True, help_text="e.g. 5:20 min/km")
    avg_heart_rate = models.IntegerField(blank=True, null=True, help_text="bpm")
    
    # Legacy direct fields preserved for backward compatibility
    screenshot = models.ImageField(upload_to='workout_proofs/', blank=True, null=True, help_text="Primary proof screenshot")
    screenshot_2 = models.ImageField(upload_to='workout_proofs/', blank=True, null=True)
    screenshot_3 = models.ImageField(upload_to='workout_proofs/', blank=True, null=True)
    runner_notes = models.TextField(blank=True, null=True, help_text="How was the workout? Any issues?")

    # Coach verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_submissions')
    coach_feedback = models.TextField(blank=True, null=True, help_text="Coach's feedback & performance analysis")
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.runner.username} - {self.assignment.title} ({self.status}) - {self.completed_distance}km"

    @property
    def pace_calculated(self):
        if self.completed_distance and self.completed_duration_minutes and self.completed_distance > 0:
            pace_dec = float(self.completed_duration_minutes) / float(self.completed_distance)
            mins = int(pace_dec)
            secs = int((pace_dec - mins) * 60)
            return f"{mins}:{secs:02d} /km"
        return self.avg_pace or "--"

    def get_all_screenshots(self):
        """Returns list of all image URLs (up to 10 photos), preferring permanent database copies"""
        imgs = []
        for photo in self.additional_screenshots.all():
            u = photo.photo_url
            if u:
                imgs.append(u)
        if not imgs and self.screenshot:
            try:
                imgs.append(self.screenshot.url)
            except Exception:
                pass
            if self.screenshot_2:
                try:
                    imgs.append(self.screenshot_2.url)
                except Exception:
                    pass
            if self.screenshot_3:
                try:
                    imgs.append(self.screenshot_3.url)
                except Exception:
                    pass
        return imgs


class ProofScreenshot(models.Model):
    """Allows uploading up to 10 screenshots per workout submission"""
    submission = models.ForeignKey(WorkoutSubmission, on_delete=models.CASCADE, related_name='additional_screenshots')
    image = models.ImageField(upload_to='workout_proofs/')
    image_base64 = models.TextField(blank=True, null=True, help_text="Permanent database-persisted screenshot")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    @property
    def photo_url(self):
        if self.image_base64:
            return self.image_base64
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return ""

    def save(self, *args, **kwargs):
        if self.image:
            try:
                from PIL import Image
                import io
                import base64

                f = getattr(self.image, 'file', None)
                if f:
                    try:
                        f.seek(0)
                    except Exception:
                        pass
                    img = Image.open(f)
                    img.thumbnail((1000, 1000))
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=80)
                    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    self.image_base64 = f"data:image/jpeg;base64,{b64}"
                    try:
                        f.seek(0)
                    except Exception:
                        pass
            except Exception:
                pass
        super().save(*args, **kwargs)

