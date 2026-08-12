"""CLI entry point: python -m design.bedrock <subcommand>."""

import argparse

from design.bedrock import cmd_preflight, cmd_report, cmd_trial


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m design.bedrock",
        description="AWS Bedrock extraction trial for Phase 3.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # preflight
    p_preflight = sub.add_parser("preflight", help="Validate AWS credentials and model access.")
    p_preflight.add_argument(
        "--output",
        default="design/output/preflight_result.json",
        help="Path for preflight result JSON.",
    )
    p_preflight.set_defaults(handler=cmd_preflight)

    # trial
    p_trial = sub.add_parser("trial", help="Run the five extraction test cases against Bedrock.")
    p_trial.add_argument(
        "--output-dir", default="design/output", help="Directory for trial outputs."
    )
    p_trial.set_defaults(handler=cmd_trial)

    # report
    p_report = sub.add_parser("report", help="Re-generate trial summary from saved raw responses.")
    p_report.add_argument(
        "--output-dir", default="design/output", help="Directory containing trial outputs."
    )
    p_report.set_defaults(handler=cmd_report)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
