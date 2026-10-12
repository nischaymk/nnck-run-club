from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, WorkoutAssignment, WorkoutCategory, WorkoutSubmission
from datetime import date, timedelta


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
        ).order_by('first_name', 'username')
        
        self.fields['runners'].queryset = athlete_qs
        self.fields['runners'].required = False
        self.fields['runners'].help_text = "Hold Ctrl / Cmd to select multiple athletes for this group workout. Leave empty if broadcasting to all runners."
        
        self.fields['runner'].queryset = athlete_qs
        self.fields['runner'].required = False
        self.fields['runner'].empty_label = "None (use group selection or broadcast)"

        tomorrow = date.today() + timedelta(days=1)
        self.fields['scheduled_date'].initial = tomorrow

    class Meta:
        model = WorkoutAssignment
        fields = [
            'runners', 'runner', 'category', 'title', 'scheduled_date',
            'target_distance', 'target_duration', 'target_pace',
            'intensity_level', 'description', 'notes'
        ]
        widgets = {
            'runners': forms.SelectMultiple(attrs={'class': 'form-select bg-dark border-secondary text-white', 'size': '5'}),
            'runner': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white'}),
            'category': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white'}),
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. Group A: 10K Progressive Tempo'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'type': 'date'}),
            'target_distance': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'km', 'step': '0.1'}),
            'target_duration': forms.NumberInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'minutes'}),
            'target_pace': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-white', 'placeholder': 'e.g. 5:10/km'}),
            'intensity_level': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-white'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 4, 'placeholder': 'Step-by-step workout guide, intervals, reps, heart rate zones...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-white', 'rows': 2, 'placeholder': 'Coach advice, warmup guidance, hydration...'}),
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
