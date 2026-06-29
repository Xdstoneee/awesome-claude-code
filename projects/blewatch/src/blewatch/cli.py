"""CLI entry point: blewatch scan | blewatch analyze <file>"""
from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console

from .persistence import DEFAULT_MIN_SIGHTINGS, DEFAULT_WINDOW_MINUTES, PersistenceEngine
from .scanner import Sighting, scan_forever

_console = Console(stderr=True)


def _make_engine_and_handler(min_sightings: int, window_minutes: int, human: bool):
    engine = PersistenceEngine(min_sightings=min_sightings, window_minutes=window_minutes)

    def handle_sighting(sighting: Sighting) -> None:
        for alert in engine.ingest(sighting):
            print(alert.to_json_event(), flush=True)
            if human:
                _console.print(
                    f"[bold red]ALERT[/] {alert.tracker_type} ({alert.confidence}) "
                    f"mac={alert.mac} sightings={alert.observation_count}"
                )

    return handle_sighting


@click.group()
def main() -> None:
    """blewatch — BLE tracker detection for pentesters and privacy researchers."""


@main.command()
@click.option("--min-sightings", default=DEFAULT_MIN_SIGHTINGS, show_default=True)
@click.option("--window-minutes", default=DEFAULT_WINDOW_MINUTES, show_default=True)
@click.option("--human", is_flag=True, help="Print human-readable summary to stderr")
def scan(min_sightings: int, window_minutes: int, human: bool) -> None:
    """Scan BLE live. Alerts are emitted to stdout as JSON."""
    handler = _make_engine_and_handler(min_sightings, window_minutes, human)
    try:
        asyncio.run(scan_forever(handler))
    except KeyboardInterrupt:
        _console.print("[yellow]Scan stopped.[/]")
        sys.exit(0)


@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option("--min-sightings", default=DEFAULT_MIN_SIGHTINGS, show_default=True)
@click.option("--window-minutes", default=DEFAULT_WINDOW_MINUTES, show_default=True)
@click.option("--human", is_flag=True)
def analyze(file: str, min_sightings: int, window_minutes: int, human: bool) -> None:
    """Analyze a btsnoop or pcap capture file offline."""
    from .pcap_reader import replay_file

    handler = _make_engine_and_handler(min_sightings, window_minutes, human)
    replay_file(file, handler)
