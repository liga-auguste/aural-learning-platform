# modules/storages.py

from __future__ import annotations

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


def _require(setting_name: str) -> str:
    """
    Read a required setting from Django settings.
    In DEBUG, allow missing values (so local dev works).
    In production, fail fast with a clear error.
    """
    value = getattr(settings, setting_name, "") or ""
    if not value and not settings.DEBUG:
        raise RuntimeError(
            f"Missing required setting '{setting_name}' for R2 storage in production."
        )
    return value


class R2BaseStorage(S3Boto3Storage):
    default_acl = None
    file_overwrite = False

    custom_domain = None
    querystring_auth = True

    def __init__(self, *args, **kwargs):
        # django-storages expects these attributes for credentials/endpoint
        self.access_key = _require("R2_ACCESS_KEY_ID")
        self.secret_key = _require("R2_SECRET_ACCESS_KEY")
        self.endpoint_url = _require("R2_ENDPOINT_URL")
        self.region_name = "auto"

        super().__init__(*args, **kwargs)


class StudentMaterialsR2Storage(R2BaseStorage):
    """
    Public-ish bucket (optional): student-facing materials.
    Keep querystring_auth True unless you explicitly make objects public via custom domain.
    """
    bucket_name = _require("R2_BUCKET_STUDENT")
    location = "modules"  # optional prefix inside the bucket


class TeacherMaterialsR2Storage(R2BaseStorage):
    """
    Private bucket: teacher-only materials (solutions, notes).
    """
    bucket_name = _require("R2_BUCKET_TEACHER")
    location = "modules"  # optional prefix inside the bucket


class SubmissionsR2Storage(R2BaseStorage):
    """
    Private bucket: student submissions.
    """
    bucket_name = _require("R2_BUCKET_SUBMISSIONS")
    location = "submissions"


def _local_storage() -> FileSystemStorage:
    # MEDIA_ROOT can be a Path; FileSystemStorage is fine with str
    return FileSystemStorage(location=str(settings.MEDIA_ROOT), base_url=settings.MEDIA_URL)


def get_student_storage():
    return _local_storage() if settings.DEBUG else StudentMaterialsR2Storage()


def get_teacher_storage():
    return _local_storage() if settings.DEBUG else TeacherMaterialsR2Storage()


def get_submissions_storage():
    return _local_storage() if settings.DEBUG else SubmissionsR2Storage()


# Convenient instances (use these in FileField(storage=...))
student_storage = get_student_storage()
teacher_storage = get_teacher_storage()
submissions_storage = get_submissions_storage()