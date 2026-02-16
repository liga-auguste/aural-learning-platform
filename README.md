# Aural Learning Platform

A Django-based web application for organizing structured aural training content. Initially based on the tutorial: https://realpython.com/django-diary-project-python/

This platform is designed to manage modules, lessons, and learning materials for ear training and music theory education. It focuses on content organization rather than exercise automation.

---

## ✨ Features

- Structured learning modules
- Lesson organization within modules
- Tag-based categorization
- Admin interface for content management
- Media file support (PDF, audio, etc.)
- User authentication
- Custom navigation context processor

---

## 🛠 Tech Stack

- Python 3
- Django 5
- SQLite (development)
- django-taggit

---

## 📂 Project Structure

- `config/` – Django project configuration
- `modules/` – Core learning module logic
- `entries/` – Lesson/content entities
- `templates/` – Global templates
- `media/` – Uploaded content files

---

## 🚀 Setup (Development)

Clone the repository:

```bash
git clone git@github.com:liga-auguste/aural-learning-platform.git
cd aural-learning-platform
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python3 manage.py migrate
```

Start development server:

```bash
python3 manage.py runserver
```

---

## 🎯 Project Goal

This project aims to provide a clean, extensible structure for organizing aural training content. It is part of an ongoing development process focused on improving architecture, usability, and educational workflow.

---

## 📌 Status

Active development.
