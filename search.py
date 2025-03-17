#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
import argparse
import csv
import json
import os
import sqlite3
import sys
import urllib.parse
import requests
from datetime import datetime


class ARCGrantsAPI:
    """Class to interact with the Australian Research Council (ARC) Grants Search API."""

    BASE_URL = "https://dataportal.arc.gov.au/NCGP/API/grants"

    def __init__(self):
        self.results = []

    def build_filter_query(
        self,
        search_text=None,
        scheme=None,
        admin_org=None,
        admin_org_short=None,
        status=None,
        year_from=None,
        year_to=None,
        funding_from=None,
        funding_to=None,
        fellowships_only=None,
        lief_register=None,
        four_digit_for=None,
        two_digit_for=None,
    ):
        """Build filter query string based on provided parameters."""
        filter_parts = []

        # Start with search text
        filter_query = search_text or ""

        # Add filters
        if scheme:
            filter_parts.append(f'scheme="{scheme}"')

        if admin_org:
            filter_parts.append(f'admin-org-name="{admin_org}"')

        if admin_org_short:
            filter_parts.append(f'admin-org-short-name="{admin_org_short}"')

        if status:
            filter_parts.append(f'status="{status}"')

        if year_from:
            filter_parts.append(f'year-from="{year_from}"')

        if year_to:
            filter_parts.append(f'year-to="{year_to}"')

        if funding_from:
            filter_parts.append(f'funding-from="{funding_from}"')

        if funding_to:
            filter_parts.append(f'funding-to="{funding_to}"')

        if fellowships_only:
            filter_parts.append(f'fellowships-only="{fellowships_only}"')

        if lief_register:
            filter_parts.append(f'lief-register="{lief_register}"')

        if four_digit_for:
            filter_parts.append(f'four-digit-for="{four_digit_for}"')

        if two_digit_for:
            filter_parts.append(f'two-digit-for="{two_digit_for}"')

        # Combine filters with AND if both search text and filters exist
        if filter_query and filter_parts:
            return f"{filter_query} => ({' AND '.join(filter_parts)})"
        elif filter_parts:
            return f"=> ({' AND '.join(filter_parts)})"
        else:
            return filter_query

    def fetch_grants(self, filter_query=None, page_size=100, max_pages=None):
        """
        Fetch grants from the ARC API with pagination.

        Args:
            filter_query: Query string for filtering results
            page_size: Number of results per page (max 1000)
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            List of grant records
        """
        self.results = []
        page = 1
        total_pages = None

        print(f"Fetching data from ARC Grants API...")

        while True:
            # Build query parameters
            params = {
                "page[size]": min(page_size, 1000),  # API limit is 1000
                "page[number]": page,
            }

            if filter_query:
                params["filter"] = filter_query

            # Encode URL
            encoded_params = urllib.parse.urlencode(params)
            url = f"{self.BASE_URL}?{encoded_params}"

            # Make request
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                if response.status_code in (401, 403):
                    print("Authentication error or API access denied.")
                elif response.status_code == 500:
                    print("Server error. Check your query parameters.")
                else:
                    print(f"HTTP error: {response.status_code}")
                break

            # Process results
            if "data" not in data:
                print("No data found in response.")
                break

            # Add results to our collection
            self.results.extend(data["data"])

            # Update pagination info
            if total_pages is None and "meta" in data:
                total_pages = data["meta"].get("total-pages", 1)
                print(
                    f"Found {data['meta'].get('total-size', 0)} grants across {total_pages} pages"
                )

            # Check if we've reached the end
            if (
                "links" not in data
                or "next" not in data["links"]
                or not data["links"]["next"]
            ):
                print(f"Reached end of results at page {page}")
                break

            if max_pages and page >= max_pages:
                print(f"Reached maximum requested pages ({max_pages})")
                break

            # Move to next page
            page += 1
            print(f"Fetching page {page}/{total_pages}...")

        print(f"Total grants fetched: {len(self.results)}")
        return self.results

    def export_to_csv(self, filename):
        """Export results to CSV file."""
        if not self.results:
            print("No results to export.")
            return False

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                # Extract all possible field names from all records
                fieldnames = set()
                for grant in self.results:
                    if "attributes" in grant:
                        fieldnames.update(grant["attributes"].keys())

                fieldnames = sorted(list(fieldnames))
                fieldnames = ["id"] + fieldnames  # Add the ID field first

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for grant in self.results:
                    row = {"id": grant.get("id", "")}

                    if "attributes" in grant:
                        for key, value in grant["attributes"].items():
                            # Convert lists and dictionaries to JSON strings
                            if isinstance(value, (list, dict)):
                                row[key] = json.dumps(value)
                            else:
                                row[key] = value

                    writer.writerow(row)

            print(f"Exported {len(self.results)} grants to {filename}")
            return True

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False

    def export_to_sqlite(self, filename):
        """Export results to SQLite database."""
        if not self.results:
            print("No results to export.")
            return False

        try:
            # Create or connect to database
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()

            # Determine schema from the first record
            fieldnames = set()
            for grant in self.results:
                if "attributes" in grant:
                    fieldnames.update(grant["attributes"].keys())

            # Create table
            fields = ["id TEXT PRIMARY KEY"]
            for field in sorted(fieldnames):
                # Guess field type based on first non-null value
                field_type = "TEXT"
                for grant in self.results:
                    if "attributes" in grant and field in grant["attributes"]:
                        value = grant["attributes"][field]
                        if value is not None:
                            if isinstance(value, (int, float)):
                                field_type = "REAL"
                                break

                # SQLite column names can't contain hyphens
                safe_field = field.replace("-", "_")
                fields.append(f"{safe_field} {field_type}")

            # Drop table if it exists and create new one
            cursor.execute("DROP TABLE IF EXISTS grants")
            cursor.execute(f"CREATE TABLE grants ({', '.join(fields)})")

            # Insert data
            for grant in self.results:
                values = {"id": grant.get("id", "")}

                if "attributes" in grant:
                    for key, value in grant["attributes"].items():
                        # Convert lists and dictionaries to JSON strings
                        if isinstance(value, (list, dict)):
                            values[key.replace("-", "_")] = json.dumps(value)
                        else:
                            values[key.replace("-", "_")] = value

                # Prepare placeholders for query
                placeholders = ", ".join(["?" for _ in range(len(values))])
                columns = ", ".join([f"`{col}`" for col in values.keys()])

                cursor.execute(
                    f"INSERT INTO grants ({columns}) VALUES ({placeholders})",
                    list(values.values()),
                )

            conn.commit()
            conn.close()

            print(f"Exported {len(self.results)} grants to SQLite database: {filename}")
            return True

        except Exception as e:
            print(f"Error exporting to SQLite: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Query ARC Grants API and export results"
    )

    # Search parameters
    parser.add_argument("--search", help="Free text search query")
    parser.add_argument("--scheme", help="Filter by scheme name")
    parser.add_argument("--admin-org", help="Filter by administering organisation name")
    parser.add_argument(
        "--admin-org-short", help="Filter by administering organisation short name"
    )
    parser.add_argument("--status", help="Filter by status (Active, Closed, etc.)")
    parser.add_argument(
        "--year-from", help="Filter by funding commencement year (from)"
    )
    parser.add_argument("--year-to", help="Filter by funding commencement year (to)")
    parser.add_argument("--funding-from", help="Filter by minimum funding amount")
    parser.add_argument("--funding-to", help="Filter by maximum funding amount")
    parser.add_argument(
        "--fellowships-only",
        choices=["true", "false"],
        help="Filter to show only grants with fellowships",
    )
    parser.add_argument(
        "--lief-register",
        choices=["true", "false"],
        help="Filter to show only grants on LIEF Register",
    )
    parser.add_argument(
        "--four-digit-for", help="Filter by 4-digit Field of Research code"
    )
    parser.add_argument(
        "--two-digit-for", help="Filter by 2-digit Field of Research code"
    )

    # API parameters
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of results per page (max 1000)",
    )
    parser.add_argument(
        "--max-pages", type=int, help="Maximum number of pages to fetch"
    )

    # Output options
    parser.add_argument("--csv", help="CSV output filename")
    parser.add_argument("--sqlite", help="SQLite output filename")

    args = parser.parse_args()

    # Create timestamp for default filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Set default output filenames if not specified
    if not args.csv and not args.sqlite:
        args.csv = f"results/arc_grants_{timestamp}.csv"

    if not args.sqlite and args.csv:
        args.sqlite = args.csv.replace(".csv", ".db")

    if not args.csv and args.sqlite:
        args.csv = args.sqlite.replace(".db", ".csv")

    # Create API client
    api = ARCGrantsAPI()

    # Build filter query
    filter_query = api.build_filter_query(
        search_text=args.search,
        scheme=args.scheme,
        admin_org=args.admin_org,
        admin_org_short=args.admin_org_short,
        status=args.status,
        year_from=args.year_from,
        year_to=args.year_to,
        funding_from=args.funding_from,
        funding_to=args.funding_to,
        fellowships_only=args.fellowships_only,
        lief_register=args.lief_register,
        four_digit_for=args.four_digit_for,
        two_digit_for=args.two_digit_for,
    )

    # Fetch data
    if filter_query:
        print(f"Using filter query: {filter_query}")

    api.fetch_grants(
        filter_query=filter_query, page_size=args.page_size, max_pages=args.max_pages
    )

    # Export results
    if api.results:
        api.export_to_csv(args.csv)
        api.export_to_sqlite(args.sqlite)
        print(f"Export complete. Files saved as {args.csv} and {args.sqlite}")
    else:
        print("No results found. Nothing exported.")


if __name__ == "__main__":
    main()
