# Verification toolchain

This isolated Python project contains published command-line tools used to
reproduce cases. It is not the Decision Archaeology application runtime.

`mise.toml` pins Python and `uv`; `uv.lock` pins the complete Python package
closure. The first pinned verifier is the `warrant-verify` distribution, whose
command is named `warrant`.

With mise:

```sh
mise install
mise run toolchain:check
```

Without mise, provide a Python matching `requires-python` and an appropriate
`uv` installation, then run:

```sh
uv sync --project toolchain --frozen
uv run --project toolchain --frozen python -c \
  'from importlib.metadata import version; print(version("warrant-verify"))'
uv run --project toolchain --frozen warrant --help
```

Do not install a local sibling checkout into this environment. Development
builds require a separate, explicitly identified profile and must not replace
the published baseline lock.
