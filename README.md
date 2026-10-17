# FastAPI Layered Config Service

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/effective-config`.

Try query overrides:
`http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=false&set=workers=2`

## Deploy
Create a new web service on a Python-friendly host (for example Render), upload/push these files to a Git repository, and set the start command to:
`uvicorn main:app --host 0.0.0.0 --port $PORT`

The host assigns its own `PORT` variable, so this app intentionally uses `APP_PORT` for the configuration layer to avoid confusing the web server's listening port with the config value returned by the endpoint.

The service returns `api_key` as `****` regardless of the underlying configured value.
