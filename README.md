# Australian Research Council Grant Search

A Python script for querying the Australian Research Council's API and returning results in CSV and SQLite formats.

## Installation

The project was built using [uv](https://github.com/astral-sh/uv) to manage dependencies and other project metadata. The project is initialised with a `pyproject.toml` file, which is used to manage dependencies and other project metadata.

## Usage

This project uses the [ARC Grants API](https://dataportal.arc.gov.au/NCGP/Web/Grant/Help) to search for grants.

Results are returned in CSV and SQLite formats.

The default output filenames are `results/arc_grants_{timestamp}.csv` and `results/arc_grants_{timestamp}.db` respectively.

### Search parameters

The following parameters can be used to filter the results:

- `--search`: Free text search query
- `--scheme`: Filter by scheme name
- `--admin-org`: Filter by administering organisation name
- `--admin-org-short`: Filter by administering organisation short name
- `--status`: Filter by status (Active, Closed, etc.)
- `--year-from`: Filter by funding commencement year (from)
- `--year-to`: Filter by funding commencement year (to)
- `--funding-from`: Filter by minimum funding amount
- `--funding-to`: Filter by maximum funding amount
- `--fellowships-only`: Filter to show only grants with fellowships
- `--lief-register`: Filter to show only grants on LIEF Register
- `--four-digit-for`: Filter by 4-digit Field of Research code
- `--two-digit-for`: Filter by 2-digit Field of Research code

### Free text search parameters

In the `--search` parameter, you can use a number of logical operators to search for specific terms:

- `"exact phrase"`: Search for exact phrases
- `OR`: Search for results that match any search term
- `-`: Exclude results that match the search term
- `()`: Group search terms

Other operators are also available, and can be found in the [ARC Grants API documentation](https://dataportal.arc.gov.au/NCGP/Web/Grant/Help).

### API parameters

The following parameters can be used to control the API request:

- `--page-size`: Number of results per page (max 1000)
- `--max-pages`: Maximum number of pages to fetch

### Output options

The script exports both CSV and SQLite files to the `results` directory by default.

The following options can be used to specify the output format:

- `--csv`: CSV output filename
- `--sqlite`: SQLite output filename

## Example usage

To search for grants with the phrase "climate change" and export the results to a CSV file:

```
python search.py --search 'climate change' --csv "arc_grants.csv"
```

To search for grants with the phrase "climate change" and export the results to a SQLite database:

```
python search.py --search 'climate change' --sqlite "arc_grants.db"
```

To search for grants with the phrase "climate change" and export the results to a CSV file, limiting the results to 100 per page and only fetching the first 10 pages:

```
python search.py --search 'climate change' --csv "arc_grants.csv" --page-size 100 --max-pages 10
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
