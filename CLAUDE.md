# Aural Learning Platform — project conventions

Django application for a two-year ear-training course. Two roles (teacher, student),
one course of numbered units with materials, audio and homework submissions, plus a
glossary. The audience is a German-speaking music school, so the product is German
while the engineering around it is English.

## Language convention

**User-facing strings are German. Code is English.** That means German
`verbose_name`, `help_text`, `choices` labels, templates, and every message a
visitor reads; English identifiers, new comments, docstrings, commit messages,
branch names and `README.md`.

Older comments in `modules/views.py` and `accounts/` are still German. That is
history, not a rule: leave them alone unless you are already editing the
surrounding block, and write new ones in English.

### Do not "fix" these

- **`Aufgabentyp`** is a German identifier on purpose. It is a domain term the
  teacher uses, its values are German, and renaming it would split the model from
  its own vocabulary. It replaced a `django-taggit` tag in a deliberate migration.
- **`impressum` / `datenschutz`** are established legal terms, coupled to their URL
  paths and templates. Both pages must stay German for legal reasons.
- **`LANGUAGE_CODE = "de-de"` and `TIME_ZONE = "Europe/Berlin"`** are product
  decisions, not defaults left unchanged.
- **Migrations are committed.** `.gitignore` says so explicitly.

## Roles and access control

`accounts.User` extends `AbstractUser` with a `role` field and the derived
properties `is_teacher` / `is_student`. `AUTH_USER_MODEL` points at it, so always
use `get_user_model()`.

Access is enforced in the view layer by the mixins in `accounts/mixins.py`
(`TeacherRequiredMixin`, `StudentRequiredMixin`, `OwnerOrTeacherRequiredMixin`).
They redirect anonymous visitors to the login page and raise `PermissionDenied`
for authenticated users without the right role, which renders `403.html`.

**Hiding a link in a template is not access control.** Every teacher-only or
student-only view carries its mixin, and a new view needs one too.

New accounts are created through `InviteToken`, not through open registration.
Tokens are single-use and expire after seven days.

## The course structure

`Unit` is one session of the course. Its `kind` and `number` are bound together by
database constraints, not just by form validation:

- a `number`, when set, is unique across the course (`unique_unit_number_when_set`)
- `REGULAR` units must have a number; `HOLIDAY`, `EXAM` and `OTHER` must not
  (`regular_units_require_number`)
- `clean()` additionally limits the number to the course range 1 to 40

Write units through the ORM's full validation path. Bulk operations that skip
`full_clean()` will still hit the constraints, but with a database error instead of
a readable message.

`Module` ordering is assigned inside `save()` under `transaction.atomic()` with
`select_for_update()`, and `modules/signals.py` closes the gap with an `F()`
expression when a module is deleted. **Never assign `order` by hand** and never
reimplement the renumbering; two concurrent writes are exactly what this guards
against.

## File storage

Three separate Cloudflare R2 buckets, by audience: student materials, teacher-only
materials, and submissions. `modules/storages.py` exposes them through
`get_student_storage()`, `get_teacher_storage()` and `get_submissions_storage()`,
which fall back to local `FileSystemStorage` when `DEBUG` is on.

**Always go through those functions.** A `FileField` that names a storage class
directly breaks local development, and one that names no storage puts teacher
material in the student bucket.

## Tests

The suite runs against SQLite with its own settings module:

```
python manage.py test --settings=config.settings_test
```

Those settings disable `django-axes` (its backend needs a `request` that
`client.login()` does not provide), swap in the MD5 password hasher, and force
local file storage. A test that fails only under `config.settings` is usually
hitting one of those three.

Tests live in the `modules/tests/` package and in `accounts/tests.py`.
`.github/workflows/test.yml` runs them on every push and pull request and commits
the coverage badge on `main`. Coverage is currently 84 per cent; a change that
lowers it needs a reason.

## Security settings

`django-axes` locks an IP after five failed logins for one hour. The production
block in `config/settings.py` (SSL redirect, HSTS, secure cookies,
`SECURE_PROXY_SSL_HEADER`) is gated on `DEBUG` being off. Do not relax that gate to
make something work locally; set `DEBUG=True` in the environment instead.
