"""CLI entry point: ``python -m design`` (delegates to design.bedrock.main).

Both ``python -m design.bedrock <subcommand>`` (via the ``__main__`` guard in
:mod:`design.bedrock`) and ``python -m design <subcommand>`` share the single
CLI surface defined in ``design.bedrock.main``.
"""

from design.bedrock import main

if __name__ == "__main__":
    raise SystemExit(main())
