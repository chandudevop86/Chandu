from __future__ import annotations

import argparse
import getpass

from vinayak.auth.service import UserAuthService
from app.vinayak.infrastructure.db.session import build_session_factory, initialize_database


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Create or update the first Vinayak admin account in the database.',
    )
    parser.add_argument('--username', required=True, help='Admin username to create or update.')
    parser.add_argument('--password', help='Admin password. If omitted, the command prompts securely.')
    parser.add_argument(
        '--force-update',
        action='store_true',
        help='Update an existing user to admin and reset the password if the username already exists.',
    )
    return parser.parse_args()


def _resolve_password(password: str | None) -> str:
    if password:
        return str(password)
    first = getpass.getpass('Admin password: ')
    second = getpass.getpass('Confirm password: ')
    if first != second:
        raise ValueError('Passwords did not match.')
    return first


def main() -> int:
    args = _parse_args()
    password = _resolve_password(args.password)

    initialize_database()
    session = build_session_factory()()
    try:
        auth = UserAuthService(session)
        record = auth.upsert_admin_user(
            username=str(args.username),
            password=password,
            force_update=bool(args.force_update),
        )
        print(f'Admin user ready: {record.username} (role={record.role})')
        return 0
    except Exception as exc:
        print(f'Admin bootstrap failed: {exc}')
        return 1
    finally:
        session.close()


if __name__ == '__main__':
    raise SystemExit(main())
