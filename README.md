# Gehörbildung – Aural Learning Platform

Eine webbasierte Lernplattform für den Gehörbildungsunterricht, entwickelt mit Django. Die Plattform unterstützt zwei Rollen (Lehrkraft / Schüler:in) und bildet den vollständigen Unterrichtsablauf ab – von der Modulverwaltung über Hausaufgaben-Abgaben bis hin zur Korrektur.

> **Live-Demo:** [aural-learning-platform.onrender.com](https://aural-learning-platform.onrender.com)
> | Rolle | Login | Passwort |
> |---|---|---|
> | Lehrkraft | `Demo_Lehrkraft` | `Demo1234!` |
> | Schüler:in | `Demo_Schüler_in` | `Demo1234!` |

## Screenshots

| Lehrer-Dashboard | Moduldetail |
|---|---|
| ![Lehrer-Dashboard](docs/screenshots/teacher_dashboard.png) | ![Moduldetail](docs/screenshots/module_detail.png) |

| Hausaufgaben verwalten | Einladungssystem |
|---|---|
| ![Hausaufgaben verwalten](docs/screenshots/submissions_dashboard.png) | ![Einladungssystem](docs/screenshots/invite_system.png) |

---

## Funktionsumfang

### Für Schüler:innen
- Modulübersicht mit persönlichem Fortschritt
- Modul als „erledigt" markieren
- Audiodateien und PDFs je Modul
- Hausaufgaben einreichen (PDF-Upload, 36-Stunden-Sperrfrist vor Abgabetermin)
- Eigene Abgaben einsehen, Korrekturstatus verfolgen
- Persönliches Dashboard mit Fortschrittsbalken und „Weiterlernen"-Direktlink
- Glossar mit Lernbegriffen

### Für Lehrkräfte
- Module erstellen, bearbeiten, löschen (Skript, Lösung, Hausaufgabe, Audio)
- Hausaufgaben-Verwaltung: Abgaben je Einheit einsehen, als korrigiert markieren, ZIP-Download aller PDFs
- Schülerfortschritt einsehen und manuell bearbeiten
- Einladungslinks für Schüler:innen und Lehrkräfte generieren
- Glossar pflegen (Lernbegriffe, Prüfungsrelevanz setzen)
- Aufgabentypen verwalten
- Kursfortschritt (Ziel: 40 Module) im Überblick

---

## Tech Stack

| Bereich | Technologie |
|---|---|
| Framework | Django 5.2 |
| Datenbank | PostgreSQL (Produktion), SQLite (Entwicklung) |
| Dateiablage | Cloudflare R2 (3 Buckets) / lokal (Entwicklung) |
| Static Files | WhiteNoise + CompressedManifestStaticFilesStorage |
| Deployment | Gunicorn, HTTPS, HSTS |
| Abhängigkeiten | django-storages, boto3, adminsortable2 |
| Frontend | Vanilla CSS (Glass Design System), Vanilla JS |

---

## Architektur

### Apps

```
aural-learning-platform/
├── accounts/          # User-Modell, Rollen, Login, Einladungs-System
├── modules/           # Kernlogik: Module, Glossar, Abgaben, Dashboards
├── config/            # Django-Konfiguration, URLs, Middleware
├── templates/         # Globale Templates (Login, About, Impressum …)
└── imports/           # Skripte für den Erstimport von Moduldaten
```

### Rollen-System

Das Rollen-System läuft über ein eigenes `role`-Feld im User-Modell – nicht über Djangos Permissions oder Groups:

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

Views werden mit `TeacherRequiredMixin` bzw. `StudentRequiredMixin` abgesichert.

### Datei-Storage (Cloudflare R2)

Drei getrennte Buckets – abhängig von der Sensitivität der Datei:

| Storage | Inhalt | Sichtbarkeit |
|---|---|---|
| `StudentMaterialsR2Storage` | Skript, Hausaufgaben-PDF, Audio | Eingeloggte Nutzer |
| `TeacherMaterialsR2Storage` | Lösungen (PDF 2 & 4) | Nur Lehrkraft |
| `SubmissionsR2Storage` | Schüler-Abgaben | Nur Lehrkraft + eigene Schüler |

Im Entwicklungsmodus (`DEBUG=True`) wird lokal gespeichert.

---

## Datenmodell (Übersicht)

```
User (accounts)
 ├── role: TEACHER | STUDENT
 └── created_invites → InviteToken

InviteToken (accounts)
 ├── token: UUID (einmalig, 7 Tage gültig)
 ├── role: TEACHER | STUDENT
 ├── first_name, last_name, email
 └── used: bool

Module
 ├── title, slug, order
 ├── inclass (Unterrichtsinhalt), homework
 ├── pdf_1 … pdf_4 (Skript, Lösungen, Hausaufgabe)
 ├── audio_1 … audio_4 + Titel
 ├── tasktype → Aufgabentyp (M2M)
 └── glossary_terms → GlossaryEntry (M2M)

Unit  (wird automatisch bei Hausaufgaben-PDF angelegt)
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

Aufgabentyp
 └── name, slug
```

---

## Einladungs-System

Lehrkräfte generieren Einladungslinks direkt im Frontend – kein Admin-Zugang nötig.

**Flow:**
1. Lehrkraft → `/teacher/invite/` → Vorname, Nachname, E-Mail, Rolle eingeben → Link generieren
2. Link per Kopieren- oder Mail-Button direkt versenden
3. Eingeladene Person öffnet Link → sieht ihren Namen und die Rolle → setzt nur ein Passwort
4. Username wird automatisch auf die E-Mail gesetzt
5. Link ist einmalig nutzbar und läuft nach 7 Tagen ab

---

## Hausaufgaben-Abgabe & Sperrmechanismus

- `submissions_enabled = True` → Schüler:in kann Dateien hochladen
- **36-Stunden-Regel**: 36 Stunden vor dem Datum der Folge-Unit wird die Abgabe automatisch gesperrt
- Status-Übergänge: `SUBMITTED` → `CORRECTED` (manuell durch Lehrkraft oder Bulk-Aktion)
- Lehrkraft kann alle PDFs einer Einheit als ZIP herunterladen

---

## Setup (Entwicklung)

**Voraussetzungen:** Python 3.11+, PostgreSQL (oder SQLite)

```bash
git clone <repo>
cd aural-learning-platform

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**.env anlegen:**

```env
SECRET_KEY=dein-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Kontaktformular
CONTACT_RECIPIENT=deine@email.de

# Cloudflare R2 (nur Produktion)
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_BUCKET_STUDENT=...
R2_BUCKET_TEACHER=...
R2_BUCKET_SUBMISSIONS=...
```

**Datenbank & Start:**

```bash
python manage.py migrate
python manage.py runserver
```

**Demo-Daten laden (optional):**

```bash
python manage.py create_demo_data
```

Erstellt zwei Demo-Accounts (`lehrer@demo.de` / `schueler@demo.de`, Passwort `Demo1234!`) sowie Beispielmodule, Aufgabentypen und Glossareinträge.

Den Superuser zur Lehrkraft machen: Im Admin `role = TEACHER` setzen oder direkt in der Shell:

```bash
python manage.py shell -c "
from accounts.models import User
u = User.objects.get(username='<username>')
u.role = 'TEACHER'
u.save()
"
```

---

## Deployment (Produktion)

```env
DJANGO_ENV=production
DEBUG=False
DATABASE_URL=<postgres-url>
```

```bash
python manage.py collectstatic
gunicorn config.wsgi:application
```

Aktiviert automatisch: HTTPS-Redirect, HSTS (7 Tage), Secure Cookies, SSL-Header.

---

## Bekannte technische Schulden

| Thema | Details |
|---|---|
| `django-taggit` entfernen | Taggit ist im Code nicht mehr aktiv (ersetzt durch `Aufgabentyp`), bleibt wegen Migrationshistorie in `INSTALLED_APPS`. Lösung: Migrationen squashen, dann Paket aus Settings und `requirements.txt` entfernen. |

---

## Projektstruktur

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
│   ├── views.py            # ~30 Views
│   ├── urls.py
│   ├── forms.py            # ModuleForm, ContactForm
│   ├── admin.py            # Erweiterte Admin-Ansichten
│   ├── storages.py         # R2-Storage-Klassen
│   ├── context_processors.py
│   ├── widgets.py
│   ├── migrations/
│   ├── static/modules/
│   │   ├── css/style.css   # Haupt-Stylesheet (Glass Design System)
│   │   ├── css/auth.css
│   │   ├── js/script.js
│   │   └── icons/
│   └── templates/
│       ├── base.html
│       ├── includes/sidebar.html
│       └── modules/        # Alle App-Templates
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── middleware.py       # RememberMeMiddleware
├── templates/              # Globale Templates (Login, Impressum, …)
├── imports/                # Datenimport-Skripte
├── media/                  # Lokale Uploads (nur Entwicklung)
├── staticfiles/            # collectstatic-Output
├── requirements.txt
└── manage.py
```
