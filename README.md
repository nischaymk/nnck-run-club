# NNCK RUN CLUB - FULL STACK DJANGO WEB APPLICATION
*Motto: "Run Together • Grow Together"*

A modern full-stack web application built for **NNCK Run Club** with athlete profile management, next-day training schedules, Garmin & COROS smart watch telemetry integration, workout history tracking, and an admin & coach portal with athlete performance analysis.

---

## 🌟 Key Features

1. **Initial Entrance & Authentication Screen**:
   - Branded entrance featuring the official club emblem and motto: *"Run Together • Grow Together"*.
   - Tabbed sign-in and runner registration modal.
   - Runners choose roles (Runner or Coach), enter mobile numbers, target races, and pacing goals upon signup.

2. **Runner Dashboard**:
   - **Next Day Workout Display**: Prominently features the next scheduled session (intervals, tempo, long run, core/strength) along with coach guidance, targets (km, duration, pace), and intensity.
   - **Today's Schedule**: Instant view of the day's training plan.
   - **Mileage & Consistency Tracker**: Weekly progress bar towards mileage goals, active days, and lifetime kilometers.
   - **Watch Sync Controls**: Dedicated instant sync triggers for Garmin & COROS devices.

3. **Garmin & COROS Auto-Sync Telemetry**:
   - Automatic fetching of activities matching the date.
   - Captures running distance, duration, average pace, heart rate (average & max bpm), cadence (spm), elevation gain, and calories burned.
   - Distinguishes device source badges (Garmin Connect / COROS Watch).

4. **Runner Profiles**:
   - Manage athlete bio, profile photo, emergency contact, target race (e.g., TCS 10K, Half Marathon), target pace, and weekly goal.
   - Configure Garmin & COROS usernames/tokens for automated telemetry sync.

5. **Coach & Admin Portal**:
   - Coach overview displaying all club runners, active devices, and training completions.
   - **Workout Upload & Assignment**:
     - Coach can assign workouts to a **specific individual runner** or **broadcast to all runners**.
     - Schedule date (defaults to tomorrow).
     - Set target distance, target duration, target pace, intensity level, step-by-step description, and coach pre-run notes.
   - **Workout Discipline / Category Management**:
     - Categorize training: `Warmup`, `Easy Run`, `Tempo Run`, `Interval Training`, `Strength Training`, `Core Training`, `Cooldown`, or `Custom Workout`.
     - Coach can add customized categories with color badges and icons.
   - **Runner Performance Analytics & Feedback**:
     - Coach inspects any runner's training logs, weekly/monthly volume, and heart rate telemetry.
     - Coach writes and updates personalized analytical feedback directly on workouts.
   - Direct link to Django Admin for superusers.

---

## 🚀 Getting Started

### 1. Installation
Prerequisites: Python 3.10+
Dependencies installed:
```bash
pip install django pillow requests django-crispy-forms crispy-bootstrap5
```

### 2. Run Database Migrations & Seed Sample Data
```bash
python manage.py migrate
python manage.py seed_nnck
```

### 3. Start the Local Server
```bash
python manage.py runserver 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 🔑 Pre-Configured Test Accounts

| Role | Username | Password | Notes |
|---|---|---|---|
| **Coach / Admin** | `coach_nnck` | `coach123` | Has access to Coach Portal, workout uploads, and `/admin/` |
| **Runner (Garmin)** | `pavan_runner` | `runner123` | Next day 8K Progressive Tempo assigned, Garmin connected |
| **Runner (COROS)** | `anita_nnck` | `runner123` | TCS 10K target, COROS Pace 3 connected |

---

## 📁 Directory Structure
```
NNCK/
├── manage.py
├── static/
│   └── images/
│       └── logo.jpg          <- Official NNCK Club Emblem
├── media/
│   └── profiles/
├── templates/
│   └── club/
│       ├── base.html
│       ├── landing.html
│       ├── dashboard.html
│       ├── profile.html
│       ├── workout_history.html
│       ├── log_workout.html
│       ├── coach_portal.html
│       ├── coach_assign_workout.html
│       ├── coach_category.html
│       └── coach_runner_analysis.html
├── club/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── services.py
│   ├── admin.py
│   └── management/commands/seed_nnck.py
└── nnck_club/
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```
