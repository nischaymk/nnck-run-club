from django.urls import path
from . import views

urlpatterns = [
    # Public & Auth
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),


    # Password Reset
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete_view, name='password_reset_complete'),

    # Runner Features
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('runners/', views.club_runners_view, name='club_runners'),
    path('runners/<int:user_id>/', views.runner_detail_view, name='runner_detail'),
    path('workout/submit/<int:assignment_id>/', views.submit_workout_proof_view, name='submit_workout_proof'),
    path('history/', views.workout_history_view, name='workout_history'),

    # Coach & Admin Portal
    path('coach/portal/', views.coach_portal_view, name='coach_portal'),
    path('coach/workouts/', views.coach_workouts_list_view, name='coach_workouts_list'),
    path('coach/workouts/delete/<int:workout_id>/', views.coach_delete_workout_view, name='coach_delete_workout'),
    path('coach/assign/', views.coach_assign_workout_view, name='coach_assign_workout'),
    path('coach/category/', views.coach_create_category_view, name='coach_category'),
    path('coach/verify/<int:submission_id>/', views.coach_verify_submission_view, name='coach_verify_submission'),
    path('coach/runner/<int:runner_id>/', views.coach_runner_analysis_view, name='coach_runner_analysis'),
]
