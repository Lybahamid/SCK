# write_mako.py — run once then delete
import os

lines = []
lines.append('"""${message}\n')
lines.append('\n')
lines.append('Revision ID: ${up_revision}\n')
lines.append('Revises: ${down_revision}\n')
lines.append('Create Date: ${create_date}\n')
lines.append('\n')
lines.append('"""\n')
lines.append('from alembic import op\n')
lines.append('import sqlalchemy as sa\n')
lines.append('${imports if imports else ""}\n')
lines.append('\n')
lines.append('\n')
lines.append('# revision identifiers, used by Alembic.\n')
lines.append('revision = ${repr(up_revision)}\n')
lines.append('down_revision = ${repr(down_revision)}\n')
lines.append('branch_labels = ${repr(branch_labels)}\n')
lines.append('depends_on = ${repr(depends_on)}\n')
lines.append('\n')
lines.append('\n')
lines.append('def upgrade() -> None:\n')
lines.append('    ${upgrades if upgrades else "pass"}\n')
lines.append('\n')
lines.append('\n')
lines.append('def downgrade() -> None:\n')
lines.append('    ${downgrades if downgrades else "pass"}\n')

output_path = os.path.join("migrations", "script.py.mako")

with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"OK  {output_path} written successfully")
print(f"     Size: {os.path.getsize(output_path)} bytes")