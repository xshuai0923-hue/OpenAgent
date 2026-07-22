# Deployment

## Docker Compose

Build and start the development service:

```bash
docker compose up --build -d
```

The API is bound to `127.0.0.1:8000` and is not exposed on other host network
interfaces.

Check its status and stop it with:

```bash
docker compose ps
docker compose down
```
