# LinkHub 🔗
### ML-Based Networking and Portfolio Management Platform for Developers

**LinkHub** is a full-stack developer networking and portfolio management platform built with Django, powered by machine learning to connect developers with the most relevant projects and peers. Developers can showcase their work, collaborate as co-owners, exchange direct messages, and receive project and friends recommendations — all in one place.

---

## ✨ Core Features

- **Developer Profiles**
- **Project Showcase**
- **Voting & Comments**
- **Personalized Feed**
- **Collaborator Invites**
- **Direct Messaging**
- **Follow & Bookmark**
- **Semantic Based Searching**
- **Email Notifications**

---

## 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/NiharPopat17/linkhub.git
cd linkhub
```

### 2. Create and activate a virtual environment

```bash
python -m venv env
env\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Open `psql` or pgAdmin and run:

```sql
CREATE DATABASE db_name;
```


### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. (Optional) Create a superuser for the admin panel

```bash
python manage.py createsuperuser
```

### 7. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 8. Start the development server

```bash
python manage.py runserver
```

---

## ⚙️ Environment Variables (`.env`)

Create a `.env` file in the root directory with the following keys:

```env
SECRET_KEY = your_secret_key
DEBUG = True
ALLOWED_HOSTS = localhost,127.0.0.1

DB_NAME= db_name
DB_USER = postgres
DB_PASSWORD = db_password
DB_HOST = localhost
DB_PORT = 5432

# Generate an App Password from your Google Account:
EMAIL_HOST_USER = your_email@gmail.com
EMAIL_HOST_PASSWORD= generated_password
```
---

## 🗂️ Project Structure

```
linkhub/
├── linkhub/          
├── users/            
├── projects/         
├── api/              
├── ml/               
├── templates/        
├── static/           
├── requirements.txt
└── manage.py
```
