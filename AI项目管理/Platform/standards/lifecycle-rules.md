# Lifecycle Rules

## Shared lifecycle states

- `idea`
- `draft`
- `testing`
- `active`
- `paused`
- `archived`

## Rules

- No solution or asset enters `draft` without a registered database record
- No solution or asset enters `testing` without at least one validation definition
- No solution or asset enters `active` without version, owner, and evidence
- No solution or asset enters `archived` without archive reason and replacement note when applicable
