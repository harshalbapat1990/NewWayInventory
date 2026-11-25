"""Create or restore a verified SQLite backup without overwriting existing data."""
import argparse
import os
import sqlite3
from datetime import datetime


def integrity(path):
    with sqlite3.connect(path) as connection:
        result = connection.execute('PRAGMA integrity_check').fetchone()[0]
    if result != 'ok':
        raise RuntimeError(f'SQLite integrity check failed: {result}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('backup')
    restore = commands.add_parser('restore')
    restore.add_argument('backup_file')
    args = parser.parse_args()

    data_dir = os.path.abspath(os.environ.get('INVENTORY_DATA_DIR', os.path.join(os.environ.get('PROGRAMDATA', r'C:\ProgramData'), 'NewWayInventory')))
    database = os.path.join(data_dir, 'inventory.db')
    if args.command == 'backup':
        if not os.path.isfile(database):
            raise SystemExit(f'Database not found: {database}')
        backup_dir = os.path.join(data_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        target = os.path.join(backup_dir, f"inventory-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db")
        with sqlite3.connect(database) as source, sqlite3.connect(target) as destination:
            source.backup(destination)
        integrity(target)
        print(f'Verified backup created: {target}')
    else:
        source = os.path.abspath(args.backup_file)
        if not os.path.isfile(source):
            raise SystemExit('Backup file does not exist.')
        if os.path.exists(database):
            raise SystemExit(f'Restore target already exists. Set INVENTORY_DATA_DIR to a new empty folder: {data_dir}')
        os.makedirs(data_dir, exist_ok=True)
        integrity(source)
        with sqlite3.connect(source) as backup, sqlite3.connect(database) as destination:
            backup.backup(destination)
        integrity(database)
        print(f'Verified restore created: {database}')


if __name__ == '__main__':
    main()
