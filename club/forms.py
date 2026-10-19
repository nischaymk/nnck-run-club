from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, WorkoutAssignment, WorkoutCategory, WorkoutSubmission
from datetime import date, timedelta, datetime


class RunnerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Mobile Number'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Password'}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Username'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip().replace(' ', '_')
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}))

    class Meta:
        model = UserProfile
        fields = [
            'phone', 'gender', 'date_of_birth', 'emergency_contact',
            'profile_photo', 'bio', 'target_race', 'target_pace',
            'weekly_mileage_target'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}),
            'gender': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'type': 'date'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}),
            'bio': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 3, 'placeholder': 'Tell fellow club runners about yourself, your running journey, and goals...'}),
            'target_race': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. TCS 10K, Bengaluru Half Marathon'}),
            'target_pace': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. 5:15 min/km'}),
            'weekly_mileage_target': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'step': '0.5'}),
        }


class WorkoutAssignmentForm(forms.ModelForm):
    target_type = forms.ChoiceField(
        choices=[
            ('all', 'All Club Runners (Broadcast)'),
            ('group', 'Specific Runner(s) or Group'),
        ],
        required=False,
        initial='all',
        widget=forms.HiddenInput()
    )
    post_timing_mode = forms.ChoiceField(
        choices=[
            ('immediate', 'Post Immediately (Visible to athletes right away)'),
            ('scheduled', 'Schedule Posting Time (Release details at specific date & time)'),
        ],
        required=False,
        initial='immediate',
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Athletes/runners queryset
        athlete_qs = User.objects.filter(
            is_active=True
        ).exclude(
            profile__role='coach'
        ).exclude(
            is_staff=True
        ).exclude(
            is_superuser=True
        ).select_related('profile').order_by('first_name', 'username')
        
        self.fields['runners'].queryset = athlete_qs
        self.fields['runners'].required = False
        self.fields['runners'].widget = forms.CheckboxSelectMultiple()
        
        self.fields['runner'].queryset = athlete_qs
        self.fields['runner'].required = False
        self.fields['runner'].widget = forms.HiddenInput()

        self.fields['publish_date'].required = False
        self.fields['publish_time'].required = False

        tomorrow = date.today() + timedelta(days=1)
        self.fields['scheduled_date'].initial = tomorrow

        # Handle existing instance initial state
        if self.instance and self.instance.pk:
            if self.instance.runners.exists():
                self.fields['target_type'].initial = 'group'
                self.fields['runners'].initial = list(self.instance.runners.values_list('id', flat=True))
            elif self.instance.runner:
                self.fields['target_type'].initial = 'group'
                self.fields['runners'].initial = [self.instance.runner.id]
            else:
                self.fields['target_type'].initial = 'all'

            if self.instance.publish_at:
                local_pub = timezone.localtime(self.instance.publish_at)
                self.fields['post_timing_mode'].initial = 'scheduled'
                self.fields['publish_date'].initial = local_pub.date()
                self.fields['publish_time'].initial = local_pub.strftime('%H:%M')
            else:
                self.fields['post_timing_mode'].initial = 'immediate'
                self.fields['publish_date'].initial = self.instance.scheduled_date
                self.fields['publish_time'].initial = '05:00'
        else:
            self.fields['post_timing_mode'].initial = 'immediate'
            self.fields['publish_date'].initial = tomorrow
            self.fields['publish_time'].initial = '05:00'

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data.get('target_type') or 'all'
        runners = cleaned_data.get('runners') or []

        if target_type == 'group':
            if not runners:
                self.add_error('runners', 'Please select at least one runner from the list, or choose "Broadcast to All Club Runners".')
            elif len(runners) == 1:
                cleaned_data['runner'] = runners[0]
            else:
                cleaned_data['runner'] = None
        else:
            cleaned_data['runners'] = []
            cleaned_data['runner'] = None

        # Process post_timing_mode (immediate vs scheduled)
        post_timing_mode = cleaned_data.get('post_timing_mode') or 'immediate'
        publish_time = cleaned_data.get('publish_time')
        publish_date = cleaned_data.get('publish_date')
        scheduled_date = cleaned_data.get('scheduled_date')

        if post_timing_mode == 'scheduled':
            if not publish_time:
                self.add_error('publish_time', 'Please specify the time when workout details should be posted to athletes.')
            pub_date = publish_date or scheduled_date or date.today()
            if publish_time:
                current_tz = timezone.get_current_timezone()
                pub_dt = datetime.combine(pub_date, publish_time)
                if timezone.is_naive(pub_dt):
                    pub_dt = timezone.make_aware(pub_dt, current_tz)
                cleaned_data['publish_at'] = pub_dt
                cleaned_data['publish_date'] = pub_date
                cleaned_data['publish_time'] = publish_time
        else:
            cleaned_data['publish_at'] = None
            cleaned_data['publish_date'] = None
            cleaned_data['publish_time'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        target_type = self.cleaned_data.get('target_type') or 'all'
        runners = self.cleaned_data.get('runners') or []

        if target_type == 'group':
            if len(runners) == 1:
                instance.runner = runners[0]
            else:
                instance.runner = None
        else:
            instance.runner = None

        instance.publish_at = self.cleaned_data.get('publish_at')
        instance.publish_date = self.cleaned_data.get('publish_date')
        instance.publish_time = self.cleaned_data.get('publish_time')

        if commit:
            instance.save()
            if target_type == 'group':
                instance.runners.set(runners)
            else:
                instance.runners.clear()
        else:
            old_save_m2m = self.save_m2m
            def custom_save_m2m():
                old_save_m2m()
                if target_type == 'group':
                    instance.runners.set(runners)
                else:
                    instance.runners.clear()
            self.save_m2m = custom_save_m2m

        return instance

    class Meta:
        model = WorkoutAssignment
        fields = [
            'runners', 'runner', 'category', 'title', 'scheduled_date',
            'publish_date', 'publish_time',
            'target_distance', 'target_duration', 'target_pace',
            'intensity_level', 'description', 'notes'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white', 'style': 'font-size: 16px; min-height: 44px;'}),
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. Group A: 10K Progressive Tempo', 'style': 'font-size: 16px;'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'type': 'date', 'style': 'font-size: 16px; min-height: 44px;'}),
            'publish_date': forms.DateInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'type': 'date', 'style': 'font-size: 16px; min-height: 44px;'}),
            'publish_time': forms.TimeInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'type': 'time', 'style': 'font-size: 16px; min-height: 44px;'}),
            'target_distance': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. 5.0', 'step': '0.1', 'inputmode': 'decimal', 'style': 'font-size: 16px;'}),
            'target_duration': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'minutes', 'step': '1', 'inputmode': 'numeric', 'style': 'font-size: 16px;'}),
            'target_pace': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. 5:10/km', 'style': 'font-size: 16px;'}),
            'intensity_level': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white', 'style': 'font-size: 16px; min-height: 44px;'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 4, 'placeholder': 'Step-by-step workout guidance, intervals, reps, heart rate zones...', 'style': 'font-size: 16px;'}),
            'notes': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 2, 'placeholder': 'Coach advice, warmup guidance, hydration...', 'style': 'font-size: 16px;'}),
        }


class WorkoutCategoryForm(forms.ModelForm):
    class Meta:
        model = WorkoutCategory
        fields = ['name', 'category_type', 'description', 'color_code', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. Hill Repeats, Core Strength'}),
            'category_type': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 2}),
            'color_code': forms.TextInput(attrs={'class': 'form-control form-control-color bg-dark border-secondary', 'type': 'color'}),
            'icon': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. bi-lightning-charge, bi-heart-pulse'}),
        }


class WorkoutSubmissionForm(forms.ModelForm):
    """Form used by runners to upload multiple screenshot proofs and completed workout data"""
    class Meta:
        model = WorkoutSubmission
        fields = [
            'completed_distance', 'completed_duration_minutes',
            'avg_pace', 'avg_heart_rate', 'screenshot',
            'screenshot_2', 'screenshot_3', 'runner_notes'
        ]
        widgets = {
            'completed_distance': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'step': '0.01', 'placeholder': 'Total distance completed in km'}),
            'completed_duration_minutes': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'step': '0.1', 'placeholder': 'Total duration in minutes'}),
            'avg_pace': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. 5:25 /km'}),
            'avg_heart_rate': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'Avg Heart Rate (bpm)'}),
            'screenshot': forms.FileInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}),
            'screenshot_2': forms.FileInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}),
            'screenshot_3': forms.FileInput(attrs={'class': 'form-control bg-dark border-secondary text-white'}),
            'runner_notes': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 3, 'placeholder': 'How did you feel? Multiple splits, warmups, or conditions?'}),
        }


class StyledPasswordResetForm(forms.Form):
    """Clean, high-contrast dark-mode password reset request form"""
    email = forms.EmailField(
        label="Registered Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-dark border-secondary text-white',
            'placeholder': 'Enter your registered email (e.g. runner@example.com)',
            'autocomplete': 'email',
            'autofocus': 'autofocus'
        })
    )


class StyledSetPasswordForm(forms.Form):
    """Clean, high-contrast dark-mode password confirmation form"""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-dark border-secondary text-white',
            'placeholder': 'Enter new password (min. 8 characters)',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-dark border-secondary text-white',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'The two password fields did not match.')
        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
