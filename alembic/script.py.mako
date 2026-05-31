# Write the mako template directly via Python with no string interpolation risk
python -c "
lines = [
    '\"\"\"${message}\n',
    '\n',
    'Revision ID: ${up_revision}\n',
    'Revises: ${down_revision}\n',
    'Create Date: ${create_date}\n',
    '\n',
    '\"\"\"\n',
    'from alembic import op\n',
    'import sqlalchemy as sa\n',
    '${imports if imports else \"\"}\n',
    '\n',
    '# revision identifiers, used by Alembic.\n',
    'revision = ${repr(up_revision)}\n',
    'down_revision = ${repr(down_revision)}\n',
    'branch_labels = ${repr(branch_labels)}\n',
    'depends_on = ${repr(depends_on)}\n',
    '\n',
    '\n',
    'def upgrade() -> None:\n',
    '    ${upgrades if upgrades else \"pass\"}\n',
    '\n',
    '\n',
    'def downgrade() -> None:\n',
    '    ${downgrades if downgrades else \"pass\"}\n',
]
with open('migrations/script.py.mako', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('OK  migrations/script.py.mako written')
"