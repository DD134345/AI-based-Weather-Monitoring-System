import click
import asyncio
from system_manager import SystemManager

@click.group()
def cli():
    """Weather Monitoring System CLI"""
    pass

@cli.command()
def start():
    """Start the weather monitoring system"""
    manager = SystemManager()
    asyncio.run(manager.start())

@cli.command()
def check():
    """Check system status"""
    # Add system check functionality here
    pass

if __name__ == '__main__':
    cli()