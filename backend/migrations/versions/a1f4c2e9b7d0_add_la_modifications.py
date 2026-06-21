"""add la_modifications and la_modification_exams

Revision ID: a1f4c2e9b7d0
Revises: 00cd7fdc75d9
Create Date: 2026-06-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1f4c2e9b7d0'
down_revision = '00cd7fdc75d9'
branch_labels = None
depends_on = None


SET_DECISION_DATE_FN = """
CREATE OR REPLACE FUNCTION set_modification_decision_date() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('approved', 'rejected') THEN
        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

CREATE_TRIGGER = """
CREATE TRIGGER la_modification_decision_date
BEFORE UPDATE ON la_modifications
FOR EACH ROW
WHEN (OLD.status <> NEW.status)
    EXECUTE FUNCTION set_modification_decision_date();
"""


def upgrade():
    op.create_table(
        'la_modifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'],
                                onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['uploaded_documents.id'],
                                onupdate='CASCADE', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')",
                           name='valid_modification_status'),
    )
    op.create_index('idx_la_modifications_application_id', 'la_modifications',
                    ['application_id'])
    op.create_index('idx_la_modifications_app_status', 'la_modifications',
                    ['application_id', 'status'])

    op.create_table(
        'la_modification_exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('modification_id', sa.Integer(), nullable=False),
        sa.Column('host_exam_id', sa.Integer(), nullable=False),
        sa.Column('sending_exam_id', sa.Integer(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=True, server_default='-1'),
        sa.Column('date_passed', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['modification_id'], ['la_modifications.id'],
                                onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['host_exam_id'], ['exams.id'],
                                onupdate='CASCADE', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sending_exam_id'], ['exams.id'],
                                onupdate='CASCADE', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('modification_id', 'sending_exam_id'),
        sa.UniqueConstraint('modification_id', 'host_exam_id'),
    )
    op.create_index('idx_la_modification_exams_modification_id',
                    'la_modification_exams', ['modification_id'])

    op.execute(SET_DECISION_DATE_FN)
    op.execute(CREATE_TRIGGER)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS la_modification_decision_date ON la_modifications;")
    op.execute("DROP FUNCTION IF EXISTS set_modification_decision_date();")
    op.drop_index('idx_la_modification_exams_modification_id', table_name='la_modification_exams')
    op.drop_table('la_modification_exams')
    op.drop_index('idx_la_modifications_app_status', table_name='la_modifications')
    op.drop_index('idx_la_modifications_application_id', table_name='la_modifications')
    op.drop_table('la_modifications')
