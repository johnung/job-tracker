"""Admin commands. Usage: python -m app.cli create-user"""

import argparse
import getpass
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.security import hash_password


def create_user() -> int:
    email = input("Email: ").strip().lower()
    name = input("Name (optional): ").strip() or None
    password = getpass.getpass("Password: ")
    if not email or not password:
        print("Email and password are required.", file=sys.stderr)
        return 1
    if password != getpass.getpass("Confirm password: "):
        print("Passwords don't match.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            print(f"A user with email {email} already exists.", file=sys.stderr)
            return 1
        user = User(email=email, name=name, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        print(f"Created user {user.id} ({user.email}).")
    return 0


COMMANDS = {"create-user": create_user}


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("command", choices=COMMANDS)
    args = parser.parse_args()
    return COMMANDS[args.command]()


if __name__ == "__main__":
    sys.exit(main())
