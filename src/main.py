"""Main CLI entry point for the MARL Cop & Thief game."""

import argparse
import json
import logging
import sys
from cop_thief.sdk.sdk import CopThiefSDK
from cop_thief.services.cop_server import run_cop_server
from cop_thief.services.thief_server import run_thief_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="MARL Cop & Thief via MCP Servers"
    )
    parser.add_argument(
        "--mode",
        choices=["game", "cop-server", "thief-server", "check"],
        default="game",
        help="Run mode: game engine, cop server, thief server, or health check",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for MCP server (cop=8001, thief=8002)",
    )
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="Path to config.json",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Send Gmail report after game completes",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Save game results to this JSON file path",
    )
    return parser.parse_args()


def run_game(args: argparse.Namespace) -> None:
    """Run a full game and optionally report results.

    Args:
        args: Parsed CLI arguments.
    """
    sdk = CopThiefSDK(config_path=args.config)

    # Health check before starting
    status = sdk.check_servers()
    if not status["cop"] or not status["thief"]:
        logger.warning(f"Server health: {status} — proceeding anyway")

    print(f"\n{'='*50}")
    print(f"  MARL Cop & Thief — v{sdk.version}")
    print(f"  Grid: {sdk.config.grid_size} | Sub-games: {sdk.config.num_sub_games}")
    print(f"{'='*50}\n")

    results = sdk.run_full_game()

    print(f"\n{'='*50}")
    print(f"  FINAL SCORES")
    print(f"  Cop:   {results['totals']['cop']} pts")
    print(f"  Thief: {results['totals']['thief']} pts")
    print(f"{'='*50}\n")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")

    if args.report:
        from cop_thief.services.reporter import GmailReporter
        reporter = GmailReporter()
        sent = reporter.send_game_report(results)
        print(f"Report {'sent' if sent else 'FAILED'}")


def main() -> None:
    """Main entry point — routes to correct mode."""
    args = parse_args()

    if args.mode == "cop-server":
        port = args.port or 8001
        run_cop_server(port=port)

    elif args.mode == "thief-server":
        port = args.port or 8002
        run_thief_server(port=port)

    elif args.mode == "check":
        sdk = CopThiefSDK(config_path=args.config)
        status = sdk.check_servers()
        print(f"Cop server:   {'✓ online' if status['cop'] else '✗ offline'}")
        print(f"Thief server: {'✓ online' if status['thief'] else '✗ offline'}")
        sys.exit(0 if all(status.values()) else 1)

    else:
        run_game(args)


if __name__ == "__main__":
    main()
