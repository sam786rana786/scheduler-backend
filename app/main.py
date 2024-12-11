from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.endpoints import auth, profile, settings, events, event_types, public
from .db.database import engine
from .models import user, profile as profile_model, settings as settings_model, sms, event, event_type
import os
from pathlib import Path
from dotenv import load_dotenv

# Determine the environment and load the appropriate .env file
env_file = ".env.prod" if os.getenv("ENV") == "production" else ".env"
env_path = Path(__file__).parent.parent / env_file

if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment file: {env_file}")
else:
    print(f"No .env file found. Using environment variables.")

# Log the environment being used
env = os.getenv('ENV', 'development')
print(f"Using environment: {env}")

# Create tables in correct order
models = [user, profile_model, settings_model, sms, event, event_type]
for model in models:
    model.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
if env == "production":
    allowed_origins = [
        "https://popsita.com",
        "https://appointments.txhut.ca"
    ]
else:
    allowed_origins = [
        "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(public.router, tags=["public"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(event_types.router, prefix="/api/event-types", tags=["event_types"])
