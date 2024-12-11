# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.core.config import get_settings
from app.models.user import Base

# Initialize settings
settings = get_settings()

# This is the Alembic Config object
config = context.config

# Set SQLAlchemy URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set up target metadata (used for generating migrations)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This mode doesn't require a database connection. It generates the SQL
    needed to run the migrations and stores it in a script.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True  # Enable SQLite batch mode for alterations
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this mode, the migrations are run directly against the database,
    making actual changes to the schema.
    """
    # Create an engine configuration with our settings
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Configure the migration context with our connection
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True  # Enable SQLite batch mode for alterations
        )

        # Run the migrations within a transaction
        with context.begin_transaction():
            context.run_migrations()

# Determine how to run the migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()