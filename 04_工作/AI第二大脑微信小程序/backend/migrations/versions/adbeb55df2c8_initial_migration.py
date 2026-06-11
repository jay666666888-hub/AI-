"""Initial migration

Revision ID: adbeb55df2c8
Revises:
Create Date: 2026-06-10 04:17:23.647314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'adbeb55df2c8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create AI Second Brain tables."""
    # Enable uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Projects table
    op.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            goal TEXT,
            status VARCHAR(20) DEFAULT 'active',
            progress INT DEFAULT 0,
            tags TEXT[],
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    ''')

    # Tasks table
    op.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            project_id UUID,
            type VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            detail TEXT,
            detail_source VARCHAR(20),
            status VARCHAR(20) DEFAULT 'active',
            due_date TIMESTAMP,
            priority INT DEFAULT 3,
            tags TEXT[],
            ai_metadata JSONB,
            frequency VARCHAR(20),
            execution_mode VARCHAR(20),
            scheduled_time VARCHAR(10),
            target_type VARCHAR(20),
            target_value INT,
            location VARCHAR(200),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            wait_status VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    ''')

    # Habit logs table
    op.execute('''
        CREATE TABLE IF NOT EXISTS habit_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            task_id UUID,
            executed_at TIMESTAMP DEFAULT NOW(),
            status VARCHAR(20) DEFAULT 'completed',
            ai_metadata JSONB
        )
    ''')

    # Checklist items table
    op.execute('''
        CREATE TABLE IF NOT EXISTS checklist_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            task_id UUID,
            parent_id UUID,
            content VARCHAR(500) NOT NULL,
            is_done BOOLEAN DEFAULT FALSE,
            sort_order INT DEFAULT 0,
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Notes table
    op.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            content TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'inbox',
            tags TEXT[],
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    ''')

    # Memories table
    op.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            title VARCHAR(200) NOT NULL,
            content TEXT,
            tags TEXT[],
            memory_type VARCHAR(20),
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    ''')

    # Reminders table
    op.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            entity_type VARCHAR(20),
            entity_id UUID,
            remind_at TIMESTAMP NOT NULL,
            repeat_rule JSONB,
            wx_template_id VARCHAR(100),
            is_sent BOOLEAN DEFAULT FALSE,
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            sent_at TIMESTAMP
        )
    ''')

    # Attachments table
    op.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            entity_type VARCHAR(20),
            entity_id UUID,
            url VARCHAR(500) NOT NULL,
            file_type VARCHAR(50),
            file_name VARCHAR(200),
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Project logs table
    op.execute('''
        CREATE TABLE IF NOT EXISTS project_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID,
            action VARCHAR(50) NOT NULL,
            content TEXT,
            ai_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Notifications table
    op.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            title VARCHAR(200) NOT NULL,
            content TEXT,
            type VARCHAR(20),
            entity_type VARCHAR(20),
            entity_id UUID,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Add foreign key constraints
    op.execute('ALTER TABLE projects ADD CONSTRAINT projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)')
    op.execute('ALTER TABLE tasks ADD CONSTRAINT tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)')
    op.execute('ALTER TABLE tasks ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(id)')
    op.execute('ALTER TABLE habit_logs ADD CONSTRAINT habit_logs_task_id_fkey FOREIGN KEY (task_id) REFERENCES tasks(id)')
    op.execute('ALTER TABLE checklist_items ADD CONSTRAINT checklist_items_task_id_fkey FOREIGN KEY (task_id) REFERENCES tasks(id)')
    op.execute('ALTER TABLE notes ADD CONSTRAINT notes_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)')
    op.execute('ALTER TABLE memories ADD CONSTRAINT memories_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)')
    op.execute('ALTER TABLE reminders ADD CONSTRAINT reminders_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)')
    op.execute('ALTER TABLE project_logs ADD CONSTRAINT project_logs_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(id)')
    op.execute('ALTER TABLE notifications ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)')


def downgrade() -> None:
    """Downgrade schema - drop all tables."""
    op.execute('ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey')
    op.execute('ALTER TABLE project_logs DROP CONSTRAINT IF EXISTS project_logs_project_id_fkey')
    op.execute('ALTER TABLE reminders DROP CONSTRAINT IF EXISTS reminders_user_id_fkey')
    op.execute('ALTER TABLE memories DROP CONSTRAINT IF EXISTS memories_user_id_fkey')
    op.execute('ALTER TABLE notes DROP CONSTRAINT IF EXISTS notes_user_id_fkey')
    op.execute('ALTER TABLE checklist_items DROP CONSTRAINT IF EXISTS checklist_items_task_id_fkey')
    op.execute('ALTER TABLE habit_logs DROP CONSTRAINT IF EXISTS habit_logs_task_id_fkey')
    op.execute('ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_project_id_fkey')
    op.execute('ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_user_id_fkey')
    op.execute('ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_user_id_fkey')

    op.execute('DROP TABLE IF EXISTS notifications')
    op.execute('DROP TABLE IF EXISTS project_logs')
    op.execute('DROP TABLE IF EXISTS attachments')
    op.execute('DROP TABLE IF EXISTS reminders')
    op.execute('DROP TABLE IF EXISTS memories')
    op.execute('DROP TABLE IF EXISTS notes')
    op.execute('DROP TABLE IF EXISTS checklist_items')
    op.execute('DROP TABLE IF EXISTS habit_logs')
    op.execute('DROP TABLE IF EXISTS tasks')
    op.execute('DROP TABLE IF EXISTS projects')