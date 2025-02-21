# django-htmx-chat-app

A web app built using Django and HTMX. This app utilises WebSockets to enable you to chat with other users individually in real-time with read receipts and also has a friend management system.

**The setup below is designed for testing purposes only.**

## Setup

Before you begin, ensure you have Docker installed, and that the Docker daemon is running.

1. Get a copy of this repository and change into the new directory, using Git or otherwise.

```bash
git clone https://github.com/abmu/message-app.git
cd message-app/
```

2. Create a `.env` file in the root directory of the project and add the following:

```
NGINX_PORT=8000

DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:${NGINX_PORT}

POSTGRES_DB=message_app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
```

Replace `your-secret-key-here` with your own secret key. You can generate one using the following Python command:

```bash
python -c "import secrets; print(''.join(secrets.choice([chr(i) for i in range(0x21, 0x7F)]) for _ in range(60)))"
```

3. Build and start the Docker containers.

```bash
docker-compose build
docker-compose up
```

4. In your web browser, go to http://localhost:8000 to view and interact with the application.

## Additional Notes

For development purposes, an email service provider has not been set up, so the django-allauth emails that would otherwise be sent to the user are simply printed out to the console. Email verification has also been set to 'none' rather than 'mandatory'.

The URLs generated in these emails won't work properly when running the server locally on port 8000, since the port number does not get included within the URLs. To overcome this, manually add port 8000 after localhost in the URLs generated, e.g., from `http://localhost/` to `http://localhost:8000/`.
