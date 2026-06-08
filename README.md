# Ear Training – Aural Learning Platform

![CI](https://github.com/liga-auguste/aural-learning-platform/actions/workflows/test.yml/badge.svg)

A web-based learning platform for ear training (Gehörbildung), built with Django. The platform supports two roles (teacher / student) and covers the full teaching workflow — from module management and homework submissions to grading.

## Motivation

I teach ear training myself and always struggled to consistently manage course materials and keep up with student submissions. That frustration is what drove me to build this. If I were teaching again, this is the tool I'd want to use.

> **Live Demo:** [aural-learning-platform.onrender.com](https://aural-learning-platform.onrender.com)
> | Role | Login | Password |
> |---|---|---|
> | Teacher | `Demo_Lehrkraft` | `Demo1234!` |
> | Student | `Demo_Schüler_in` | `Demo1234!` |

## Screenshots

| Teacher Dashboard | Module Detail |
|---|---|
| ![Teacher Dashboard](docs/screenshots/teacher_dashboard.png) | ![Module Detail](docs/screenshots/module_detail.png) |

| Homework Management | Invitation System |
|---|---|
| ![Homework Management](docs/screenshots/submissions_dashboard.png) | ![Invitation System](docs/screenshots/invite_system.png) |

| Student Dashboard | Glossary |
|---|---|
| ![Student Dashboard](docs/screenshots/student_dashboard.png) | ![Glossary](docs/screenshots/glossary.png) |

---

## Features

### For Students
- Module overview with personal progress tracking
- Mark modules as completed
- Audio files and PDFs per module
- Submit homework (PDF upload)
- View own submissions and track correction status
- Personal dashboard with progress bar and "Continue Learning" shortcut
- Glossary with musical terms

### For Teachers
- Create, edit, and delete modules (script, solution, homework, audio)
- Homework management: view submissions per unit, mark as corrected, ZIP download of all PDFs
- View and manually edit student progress
- Generate invitation links for students and teachers
- Manage glossary (terms, exam relevance)
- Manage task types
- Course progress overview (goal: 40 modules)

---

## Tech Stack

| Area | Technology |
|---|---|
| Framework | Django 5.2 |
| Database | PostgreSQL (production), SQLite (development) |
| File Storage | Cloudflare R2 (3 buckets) / local (development) |
| Static Files | WhiteNoise + CompressedManifestStaticFilesStorage |
| Deployment | Gunicorn, HTTPS, HSTS |
| Dependencies | django-storages, boto3, adminsortable2 |
| Frontend | Vanilla CSS (Glass Design System), Vanilla JS |

---

## Architecture

### Apps

```
aural-learning-platform/
├── accounts/          # User model, roles, login, invitation system
├── modules/           # Core logic: modules, glossary, submissions, dashboards
├── config/            # Django configuration, URLs, middleware
├── templates/         # Global templates (login, about, imprint …)
└── imports/           # Scripts for initial module data import
```

### Role System

The role system uses a custom `role` field on the user model — not Django's built-in permissions or groups:

```python
class User(AbstractUser):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    role = models.CharField(choices=ROLE_CHOICES, default=STUDENT)

    @property
    def is_teacher(self): return self.role == self.TEACHER

    @property
    def is_student(self): return self.role == self.STUDENT
```

Views are protected with `TeacherRequiredMixin` and `StudentRequiredMixin`.

### File Storage (Cloudflare R2)

Three separate buckets — based on file sensitivity:

| Storage | Contents | Visibility |
|---|---|---|
| `StudentMaterialsR2Storage` | Script, homework PDF, audio | Logged-in users |
| `TeacherMaterialsR2Storage` | Solutions (PDF 2 & 4) | Teachers only |
| `SubmissionsR2Storage` | Student submissions | Teachers + submitting student |

In development mode (`DEBUG=True`), files are stored locally.

---

## Data Model (Overview)

```
User (accounts)
 ├── role: TEACHER | STUDENT
 └── created_invites → InviteToken

InviteToken (accounts)
 ├── token: UUID (single-use, valid for 7 days)
 ├── role: TEACHER | STUDENT
 ├── first_name, last_name, email
 └── used: bool

Module
 ├── title, slug, order
 ├── inclass (lesson content), homework
 ├── pdf_1 … pdf_4 (script, solutions, homework)
 ├── audio_1 … audio_4 + titles
 ├── tasktype → TaskType (M2M)
 └── glossary_terms → GlossaryEntry (M2M)

Unit  (created automatically when a homework PDF is added)
 ├── module → Module (1:1)
 ├── date, number, kind (REGULAR | HOLIDAY | EXAM | OTHER)
 └── submissions_enabled: bool

Submission
 ├── unit → Unit
 ├── student → User
 ├── status: SUBMITTED | CORRECTED
 └── files → SubmissionFile (1:N)

ModuleCompletion
 ├── user → User
 └── module → Module

GlossaryEntry
 ├── title, slug, definition
 ├── exam_relevant: bool
 └── modules → Module (M2M)

TaskType
 └── name, slug
```

---

## Invitation System

Teachers generate invitation links directly in the frontend — no admin access required.

**Flow:**
1. Teacher → `/teacher/invite/` → enter first name, last name, email, role → generate link
2. Share the link via copy or email button
3. Invited person opens the link → sees their name and role → sets a password only
4. Username is automatically set to the email address
5. Link is single-use and expires after 7 days

---

## Homework Submission & Locking

- `submissions_enabled = True` → student can upload files
- Teacher locks submissions after downloading
- Status transitions: `SUBMITTED` → `CORRECTED` (manually by teacher or via bulk action)
- Teacher can download all PDFs for a unit as a ZIP

---

## Setup (Development)

**Prerequisites:** Python 3.11+, PostgreSQL (or SQLite)

```bash
git clone <repo>
cd aural-learning-platform

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Create a `.env` file:**

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Contact form
CONTACT_RECIPIENT=your@email.com

# Cloudflare R2 (production only)
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_BUCKET_STUDENT=...
R2_BUCKET_TEACHER=...
R2_BUCKET_SUBMISSIONS=...
```

**Migrate and run:**

```bash
python3 manage.py migrate
python3 manage.py runserver
```

**Load demo data (optional):**

```bash
python3 manage.py create_demo_data
```

Creates two demo accounts (`lehrer@demo.de` / `schueler@demo.de`, password `Demo1234!`) along with sample modules, task types, and glossary entries.

To make a superuser a teacher — set `role = TEACHER` in the admin, or via the shell:

```bash
python3 manage.py shell -c "
from accounts.models import User
u = User.objects.get(username='<username>')
u.role = 'TEACHER'
u.save()
"
```

---

## Deployment (Production)

```env
DJANGO_ENV=production
DEBUG=False
DATABASE_URL=<postgres-url>
```

```bash
python3 manage.py collectstatic
gunicorn config.wsgi:application
```

Automatically enables: HTTPS redirect, HSTS (7 days), secure cookies, SSL headers.

---

## Known Technical Debt

| Topic | Details |
|---|---|
| Remove `django-taggit` | Taggit is no longer active in the code (replaced by `TaskType`), but remains in `INSTALLED_APPS` due to migration history. Fix: squash migrations, then remove the package from settings and `requirements.txt`. |

---

## Project Structure

```
aural-learning-platform/
├── accounts/
│   ├── models.py           # User, InviteToken
│   ├── views.py            # RoleBasedLoginView
│   ├── forms.py            # RoleLoginForm, AcceptInviteForm
│   ├── mixins.py           # TeacherRequiredMixin, StudentRequiredMixin
│   ├── admin.py
│   └── migrations/
├── modules/
│   ├── models.py           # Module, Unit, Submission, GlossaryEntry, …
│   ├── views.py            # ~30 views
│   ├── urls.py
│   ├── forms.py            # ModuleForm, ContactForm
│   ├── admin.py            # Extended admin views
│   ├── storages.py         # R2 storage classes
│   ├── context_processors.py
│   ├── widgets.py
│   ├── migrations/
│   ├── static/modules/
│   │   ├── css/style.css   # Main stylesheet (Glass Design System)
│   │   ├── css/auth.css
│   │   ├── js/script.js
│   │   └── icons/
│   └── templates/
│       ├── base.html
│       ├── includes/sidebar.html
│       └── modules/        # All app templates
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── middleware.py       # RememberMeMiddleware
├── templates/              # Global templates (login, imprint, …)
├── imports/                # Data import scripts
├── media/                  # Local uploads (development only)
├── staticfiles/            # collectstatic output
├── requirements.txt
└── manage.py
```
