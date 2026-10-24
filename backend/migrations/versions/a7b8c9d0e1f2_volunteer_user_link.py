"""volunteer user link

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('volunteers') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_volunteers_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_volunteers_user_id_users', 'users', ['user_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('volunteers') as batch_op:
        batch_op.drop_constraint('fk_volunteers_user_id_users', type_='foreignkey')
        batch_op.drop_index('ix_volunteers_user_id')
        batch_op.drop_column('user_id')
