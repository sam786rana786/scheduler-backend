"""create_combined_migration

Revision ID: e0ac2030be76
Revises: 
Create Date: 2024-11-27 21:36:39.596412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0ac2030be76'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('company_logo', sa.String(), nullable=True),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('time_zone', sa.String(), nullable=True),
        sa.Column('bio', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('welcome_message', sa.String(), nullable=True),
        sa.Column('scheduling_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_profiles_user_id', 'profiles', ['user_id'], unique=True)

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('working_hours', sa.JSON(), nullable=True),
        sa.Column('notification_settings', sa.JSON(), nullable=True),
        sa.Column('email_settings', sa.JSON(), nullable=True),
        sa.Column('sms_settings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_settings_user_id', 'settings', ['user_id'], unique=True)

    # Create SMS subscriptions table
    op.create_table(
        'sms_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('account_sid', sa.String(), nullable=True),
        sa.Column('auth_token', sa.String(), nullable=True),
        sa.Column('from_number', sa.String(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('api_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sms_subscriptions_user_id', 'sms_subscriptions', ['user_id'])

    # Create event types table
    op.create_table(
        'event_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('locations', sa.JSON(), nullable=True),
        sa.Column('questions', sa.JSON(), nullable=True),
        sa.Column('booking_rules', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_types_slug', 'event_types', ['slug'], unique=True)
    op.create_index('ix_event_types_user_id', 'event_types', ['user_id'])

    # Create events table last since it depends on event_types
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('attendee_name', sa.String(), nullable=True),
        sa.Column('attendee_email', sa.String(), nullable=True),
        sa.Column('attendee_phone', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('answers', sa.JSON(), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['event_type_id'], ['event_types.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_events_user_id', 'events', ['user_id'])
    op.create_index('ix_events_start_time', 'events', ['start_time'])
    op.create_index('ix_events_end_time', 'events', ['end_time'])


def downgrade() -> None:
    op.drop_table('events')
    op.drop_table('event_types')
    op.drop_table('sms_subscriptions')
    op.drop_table('settings')
    op.drop_table('profiles')
    op.drop_table('users')
