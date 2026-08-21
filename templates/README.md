# Versioned templates

Templates are immutable starting points for investigation cases. Their version
is independent from the case schema version:

- the schema identifies machine-readable compatibility;
- the template identifies the exact files, prompts, defaults, and directory
  structure copied by an investigator.

Once a template version is present on the default branch, do not edit it in
place. Corrections produce a new patch version; compatible additions produce a
new minor version; a different case model requires a new major version and may
also require a new schema identity.

The initial template is [`case/v0.1.0/`](case/v0.1.0/README.md).
