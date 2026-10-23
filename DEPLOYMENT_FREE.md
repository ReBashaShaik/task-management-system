# Free public deployment guide

This guide deploys the FastAPI application on Render and uses Aiven's free MySQL service.

> Free plans can sleep after inactivity. The first request after a sleep can take longer. Free plans are useful for a demo or learning project, but are not intended for production availability or important data.

## What you need

- This project pushed to your GitHub repository.
- A Render account connected to GitHub.
- An Aiven account.
- Do not paste database passwords or secret keys into chat or commit them to GitHub.

## Part 1: Create the hosted MySQL database in Aiven

1. Sign in to Aiven and create a **MySQL** service. Choose the free plan if it is offered for your account and region.
2. Wait until the service status says **Running**.
3. Open the service's connection information. Copy the host, port, database name, username, and password. Keep the password private.
4. Download the service's CA certificate from the Aiven connection information page. Save it on your computer as `aiven-ca.pem`.
5. Build the database connection URL in this format:

   ```text
   mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
   ```

   If your password contains URL-special characters such as `@`, `:`, `/`, or `#`, URL-encode those characters before putting the password in the URL. Do not use the local Docker database URL or `127.0.0.1`; the hosted API needs Aiven's public host.

## Part 2: Deploy the API on Render

1. Sign in to Render and choose **New** → **Blueprint**.
2. Connect the GitHub repository `ReBashaShaik/task-management-system` and select the `main` branch.
3. Render reads `render.yaml` and prepares the API service. Choose the free instance plan if asked.
4. In the service's settings, open **Environment**. Set `DATABASE_URL` to the Aiven connection URL. Set `BOOTSTRAP_ADMIN_EMAIL` to the admin email you want and `BOOTSTRAP_ADMIN_PASSWORD` to a strong private password.
5. Add the downloaded `aiven-ca.pem` as a **Secret File** with the mount path:

   ```text
   /etc/secrets/aiven-ca.pem
   ```

   The Render configuration already points `DATABASE_SSL_CA` to that path. Keep the generated `SECRET_KEY` private; Render creates it for this service.
6. Save the settings and deploy. The container runs Alembic migrations, creates the configured bootstrap admin if that email is not already in the database, and starts the API.
7. Wait for the deployment status to show **Live**. Open the service's public URL followed by `/health`, for example:

   ```text
   https://YOUR-SERVICE.onrender.com/health
   ```

   A working API returns `{"status":"ok"}`. Then open `/docs` on the same domain to try the endpoints in Swagger UI.

## If deployment fails

- Open the service's **Logs** in Render and read the first error around startup.
- If the database connection fails, check the Aiven host, port, username, password, database name, and that `DATABASE_URL` uses `mysql+pymysql://`.
- If TLS certificate verification fails, check that the Aiven CA file is uploaded as `/etc/secrets/aiven-ca.pem` and that `DATABASE_SSL_CA` has the same path.
- If admin creation fails, check the `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` values in Render's Environment settings.
- After changing environment values, trigger a new deploy.

## Important notes

- Local `docker compose up` still uses local port 8000 and the local MySQL container. Public deployment uses Render and Aiven settings.
- Render and Aiven free services may sleep when unused, and free-tier limits can change. Check the providers' current plan details before relying on them.
- Never commit `.env`, database credentials, CA private keys, passwords, or access tokens. The CA certificate is not a password, but upload it as a Render Secret File so the application can read it securely.
- The public URL does not exist until you create the Render service and its deployment succeeds.