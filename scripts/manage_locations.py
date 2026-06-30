"""
Location Management Script

CLI tool for managing sensor locations.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.location_service import LocationService
from app.config.logging_config import logger


def list_locations(args):
    """List all locations."""
    service = LocationService()
    locations = service.get_all_locations(
        active_only=not args.all,
        country=args.country,
        city=args.city
    )
    
    if not locations:
        print("No locations found")
        return
    
    print(f"\nFound {len(locations)} locations:\n")
    print(f"{'ID':<10} {'Name':<30} {'City':<20} {'Country':<15} {'Active':<8}")
    print("-" * 85)
    
    for loc in locations:
        print(
            f"{loc['location_id']:<10} "
            f"{loc['name'][:29]:<30} "
            f"{loc['city'][:19]:<20} "
            f"{loc['country']:<15} "
            f"{'Yes' if loc['is_active'] else 'No':<8}"
        )


def search_locations(args):
    """Search for locations."""
    service = LocationService()
    locations = service.search_locations(args.term)
    
    if not locations:
        print(f"No locations found matching '{args.term}'")
        return
    
    print(f"\nFound {len(locations)} locations matching '{args.term}':\n")
    print(f"{'ID':<10} {'Name':<30} {'City':<20} {'Country':<15}")
    print("-" * 75)
    
    for loc in locations:
        print(
            f"{loc['location_id']:<10} "
            f"{loc['name'][:29]:<30} "
            f"{loc['city'][:19]:<20} "
            f"{loc['country']:<15}"
        )


def sync_locations(args):
    """Sync locations from OpenAQ API."""
    service = LocationService()
    
    print(f"Syncing locations from OpenAQ...")
    results = service.sync_locations_from_api(
        country=args.country,
        city=args.city,
        limit=args.limit
    )
    
    print(f"\nSync completed:")
    print(f"  Added: {results['added']}")
    print(f"  Updated: {results['updated']}")
    print(f"  Errors: {results['errors']}")


def show_location_stats(args):
    """Show statistics for a location."""
    service = LocationService()
    stats = service.get_location_statistics(args.location_id)
    
    if not stats:
        print(f"Location {args.location_id} not found")
        return
    
    print(f"\nLocation Statistics for {stats['name']}:\n")
    print(f"  Location ID: {stats['location_id']}")
    print(f"  City: {stats['city']}")
    print(f"  Country: {stats['country']}")
    print(f"  Parameters: {stats['parameter_count']}")
    print(f"  Total Measurements: {stats['total_measurements']:,}")
    print(f"  First Measurement: {stats['first_measurement_time']}")
    print(f"  Last Measurement: {stats['last_measurement_time']}")
    print(f"  Average Quality Score: {stats['avg_quality_score']:.2f}")


def deactivate_location(args):
    """Deactivate a location."""
    service = LocationService()
    
    if service.deactivate_location(args.location_id):
        print(f"Location {args.location_id} deactivated")
    else:
        print(f"Failed to deactivate location {args.location_id}")


def activate_location(args):
    """Activate a location."""
    service = LocationService()
    
    if service.activate_location(args.location_id):
        print(f"Location {args.location_id} activated")
    else:
        print(f"Failed to activate location {args.location_id}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Location Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all locations")
    list_parser.add_argument("--all", action="store_true", help="Include inactive locations")
    list_parser.add_argument("--country", help="Filter by country")
    list_parser.add_argument("--city", help="Filter by city")
    list_parser.set_defaults(func=list_locations)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search locations")
    search_parser.add_argument("term", help="Search term")
    search_parser.set_defaults(func=search_locations)
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync locations from OpenAQ API")
    sync_parser.add_argument("--country", help="Filter by country")
    sync_parser.add_argument("--city", help="Filter by city")
    sync_parser.add_argument("--limit", type=int, default=1000, help="Maximum locations to fetch")
    sync_parser.set_defaults(func=sync_locations)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show location statistics")
    stats_parser.add_argument("location_id", type=int, help="Location ID")
    stats_parser.set_defaults(func=show_location_stats)
    
    # Deactivate command
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate a location")
    deactivate_parser.add_argument("location_id", type=int, help="Location ID")
    deactivate_parser.set_defaults(func=deactivate_location)
    
    # Activate command
    activate_parser = subparsers.add_parser("activate", help="Activate a location")
    activate_parser.add_argument("location_id", type=int, help="Location ID")
    activate_parser.set_defaults(func=activate_location)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
