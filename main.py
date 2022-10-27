#!/bin/env python
"""The main entry point for the bot."""
from contextlib import contextmanager

import typer
from sqlalchemy_utils.functions import database_exists, create_database, drop_database

from archivebot.db import engine, base
from archivebot.models import *  # noqa
from archivebot.archivebot import main

cli = typer.Typer()


@contextmanager
def wrap_echo(msg: str):
    typer.echo(f"{msg}... ", nl=False)
    yield
    typer.echo("done.")


@cli.command()
def initdb(exist_ok: bool = False, drop_existing: bool = False):
    """Set up the database.

    Can be used to remove an existing database.
    """
    db_url = engine.url
    typer.echo(f"Using database at {db_url}")

    if database_exists(db_url):
        if drop_existing:
            with wrap_echo("Dropping database"):
                drop_database(db_url)
        elif not exist_ok:
            typer.echo(
                "Database already exists, aborting.\n"
                "Use --exist-ok if you are sure the database is uninitialized and contains no data.\n"
                "Use --drop-existing if you want to recreate it.",
                err=True,
            )
            return

    with wrap_echo("Creating database"):
        create_database(db_url)
        pass

    with wrap_echo("Creating metadata"):
        base.metadata.create_all()
        pass

    typer.echo("Database initialization complete.")


@cli.command()
def run():
    """Actually start the bot."""
    main()


if __name__ == "__main__":
    cli()
