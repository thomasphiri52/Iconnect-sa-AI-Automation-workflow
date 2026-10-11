# iConnect SA Production V3

iConnect SA AI Automation V3 is an integration-ready Streamlit business automation platform.

## V3 additions
- AI provider adapter with server-side API key support
- WhatsApp Business outbound adapter
- SMTP email outbound adapter
- Website lead webhook (FastAPI)
- POPIA consent register and withdrawal status
- Workspace foundation
- Scheduled-worker entry point for cron/Task Scheduler
- Environment-only secrets configuration

## Run dashboard
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run webhook
```bash
uvicorn webhook:app --host 0.0.0.0 --port 8000
```

## Security
Set strong admin credentials and provider secrets as environment variables. Use HTTPS, a managed secret store, backups, access logging and a production PostgreSQL database before handling real customer data.

## Important
External integrations remain disabled until valid credentials and customer consent are configured. POPIA tooling is operational support and not legal advice.
