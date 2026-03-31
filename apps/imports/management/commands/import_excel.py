from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.imports.services import import_excel_file


class Command(BaseCommand):
    help = "Import grief issues from an Excel (.xlsx / .xlsm) file"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "file",
            type=str,
            help="Path to the Excel file (e.g. data/Grief_003.xlsm)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse the file and report what would be imported, without writing to the DB",
        )

    def handle(self, *args, **options) -> None:
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run mode — no data will be written"))
            # Still parse to surface errors
            from apps.imports.services import (
                import_formulas_sheet,
                import_grief_sheet,
                import_loc_codes_sheet,
                ImportResult,
            )
            import pandas as pd
            result = ImportResult()
            sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
            self.stdout.write(f"Sheets found: {list(sheets.keys())}")
            for sheet, df in sheets.items():
                self.stdout.write(f"  {sheet}: {df.shape[0]} rows × {df.shape[1]} cols")
            return

        self.stdout.write(f"Importing from: {path}")
        result = import_excel_file(path)

        if result.errors:
            for err in result.errors:
                self.stderr.write(self.style.WARNING(f"  WARN: {err}"))

        self.stdout.write(self.style.SUCCESS(result.summary()))
