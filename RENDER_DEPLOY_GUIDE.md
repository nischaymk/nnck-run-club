# 🚀 Hosting NNCK Run Club on Render

This guide provides step-by-step instructions for deploying the **NNCK RUN CLUB** website to [Render](https://render.com) for free.

---

## 🛠️ What has been pre-configured for you:
1. **`build.sh`**: Installs dependencies, collects static files with WhiteNoise, runs migrations, and seeds the coach profile and workout categories automatically.
2. **`requirements.txt`**: Includes Django, Gunicorn, WhiteNoise, Pillow, Crispy Forms, and PostgreSQL/database drivers.
3. **`render.yaml`**: Pre-configured Render Blueprint for automated 1-click deployment.
4. **`Procfile`**: Specifies the Gunicorn WSGI production web server.
5. **`settings.py`**: Configured with WhiteNoise static asset serving, dynamic host allowances, CSRF security for `.onrender.com`, and media file streaming.

---

## 📋 Step 1: Push Your Code to GitHub

1. Open your terminal in this project folder (`C:\Users\pavan\Downloads\NNCK`).
2. Initialize git and make your first commit:
   ```bash
   git init
   git add .
   git commit -m "Deploy NNCK Run Club to Render"
   git branch -M main
   ```
3. Create a **New Repository** on [GitHub](https://github.com/new) (e.g. named `nnck-run-club`). Keep it Private or Public.
4. Link and push your code:
   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/nnck-run-club.git
   git push -u origin main
   ```

---

## 🌐 Step 2: Deploy on Render

### Method A: Blueprint (Recommended - 1-Click Setup)
1. Go to [dashboard.render.com](https://dashboard.render.com) and log in.
2. Click the **New +** button in the top right and select **Blueprint**.
3. Connect your GitHub account and select your `nnck-run-club` repository.
4. Render will automatically detect `render.yaml` with all settings pre-filled!
5. Click **Apply**. Render will run `./build.sh` and deploy your website.

---

### Method B: Manual Web Service Setup
If you prefer setting up manually:
1. In Render, click **New +** -> **Web Service**.
2. Select your `nnck-run-club` repository.
3. Configure the following fields:
   * **Name**: `nnck-run-club` (or any custom name)
   * **Region**: `Singapore` (fastest for India/Bengaluru)
   * **Branch**: `main`
   * **Runtime**: `Python 3`
   * **Build Command**: `./build.sh`
   * **Start Command**: `gunicorn nnck_club.wsgi:application`
   * **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `PYTHON_VERSION` | `3.12.0` |
   | `DEBUG` | `False` |
   | `SECRET_KEY` | *(Click generate or type any secret key)* |
   | `ALLOWED_HOSTS` | `*` |
5. Click **Create Web Service**.

---

## 🏁 Step 3: Accessing Your Website & Coach Portal

Once Render finishes building (usually 2-3 minutes), your live URL will be:
```
https://nnck-run-club.onrender.com
```

### Default Login Accounts:
* **Head Coach / Admin Portal**:
  * **Username**: `coach_nnck`
  * **Password**: `coach123`
  * **Coach Portal**: `https://your-service.onrender.com/coach/portal/`
  * **Django Admin**: `https://your-service.onrender.com/admin/`
* **Runners**:
  * Can register directly on the landing page!
