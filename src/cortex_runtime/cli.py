import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Cortex Agent Runtime CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")


    # Command: run
    run_parser = subparsers.add_parser("run", help="Start the agent runtime loop")
    
    # Command: migrate
    migrate_parser = subparsers.add_parser("migrate", help="Apply pending SQL migrations")

    args = parser.parse_args()

    if args.command == "run":
        from cortex_runtime.main import start_runtime
        start_runtime()
    elif args.command == "migrate":
        from cortex_runtime.migrations.manager import MigrationManager
        manager = MigrationManager()
        manager.apply_migrations()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
