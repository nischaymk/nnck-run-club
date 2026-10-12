from django.contrib import admin
from .models import UserProfile, WorkoutCategory, WorkoutAssignment, WorkoutSubmission

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'target_race', 'weekly_mileage_target', 'total_verified_distance')
    list_filter = ('role', 'gender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'target_race')


@admin.register(WorkoutCategory)
class WorkoutCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'color_code', 'icon')
    search_fields = ('name',)


@admin.register(WorkoutAssignment)
class WorkoutAssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_date', 'category', 'runner', 'coach', 'target_distance', 'target_duration', 'intensity_level')
    list_filter = ('scheduled_date', 'category', 'intensity_level')
    search_fields = ('title', 'description', 'runner__username', 'coach__username')


@admin.register(WorkoutSubmission)
class WorkoutSubmissionAdmin(admin.ModelAdmin):
    list_display = ('runner', 'assignment', 'completed_distance', 'completed_duration_minutes', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('runner__username', 'assignment__title', 'runner_notes', 'coach_feedback')
