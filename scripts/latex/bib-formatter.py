import argparse
from pathlib import Path
from typing import List
from ures.literature import (
	CitationManager,
	LanguageAsciiNormalizationMiddleware,
	DateSpiltToYearMonthDayMiddleware,
	ProceedingsNormalizationMiddleware,
	FieldNormalizationMiddleware,
	TypeNormalizationMiddleware,
	RuleBasedValidationMiddleware,
)


def parse_arguments() -> argparse.Namespace:
	"""Parse command line arguments."""
	parser = argparse.ArgumentParser(
		description="Process bibliography and citation files using CitationManager",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  %(prog)s -b references.bib -c main.tex main.bbl
  %(prog)s --bibliography ref1.bib ref2.bib --citation-files dist/main.tex dist/main.bbl -o output.bib
  %(prog)s -b *.bib -c dist/*.tex dist/*.bbl --output custom-references.bib
        """
	)

	parser.add_argument(
		"-b", "--bibliography",
		nargs="+",
		type=Path,
		required=True,
		help="Bibliography file(s) to process (supports multiple files)"
	)

	parser.add_argument(
		"-c", "--citation-files",
		nargs="+",
		type=Path,
		required=True,
		help="Citation file(s) to import (supports multiple files)"
	)

	parser.add_argument(
		"-o", "--output",
		type=str,
		default="references-edited.bib",
		help="Output file name (default: references-edited.bib)"
	)

	parser.add_argument(
		"--style",
		type=str,
		default="default",
		choices=["acm", "default"],
		help="Bibliography style (default: acm)"
	)

	return parser.parse_args()


def validate_files(files: List[Path]) -> List[Path]:
	"""Validate that all files exist and return resolved paths."""
	validated_files = []
	for file_path in files:
		resolved_path = file_path.resolve()
		if not resolved_path.exists():
			raise FileNotFoundError(f"File not found: {resolved_path}")
		if not resolved_path.is_file():
			raise ValueError(f"Path is not a file: {resolved_path}")
		validated_files.append(resolved_path)
	return validated_files


def main():
	"""Main function with enhanced argument parsing."""
	args = parse_arguments()

	try:
		# Validate input files
		bibliography_files = validate_files(args.bibliography)
		citation_files = validate_files(args.citation_files)

		print(f"Processing {len(bibliography_files)} bibliography file(s):")
		for bib_file in bibliography_files:
			print(f"  - {bib_file}")

		print(f"Processing {len(citation_files)} citation file(s):")
		for citation_file in citation_files:
			print(f"  - {citation_file}")

		# Initialize citation manager
		citation_manager = CitationManager(
			bibliography_files=[],
			bibliography_style=args.style
		)

		# Process each bibliography file
		middlewares = [
			LanguageAsciiNormalizationMiddleware,
			DateSpiltToYearMonthDayMiddleware,
			ProceedingsNormalizationMiddleware,
			FieldNormalizationMiddleware,
			TypeNormalizationMiddleware,
			RuleBasedValidationMiddleware,
		]

		for bib_file in bibliography_files:
			print(f"Appending bibliography: {bib_file}")
			citation_manager.manager.append_bibliography(
				bib_file,
				middlewares=middlewares
			)

		# Import citation files
		citation_manager.import_citations(citation_files, cleanup=True)

		# Save the processed bibliography
		output_path = Path(args.output).resolve()
		print(f"Saving processed bibliography to: {output_path}")
		citation_manager.save_bibliography(str(output_path))

		print("✓ Processing completed successfully!")

	except FileNotFoundError as e:
		print(f"Error: {e}")
		return 1
	except ValueError as e:
		print(f"Error: {e}")
		return 1
	except Exception as e:
		print(f"Unexpected error: {e}")
		return 1

	return 0


if __name__ == '__main__':
	exit(main())
