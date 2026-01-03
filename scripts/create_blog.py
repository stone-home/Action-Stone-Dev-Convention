import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ures.markdown import MarkdownDocument
from ures.timedate import time_now


class ReleasePostMetadata:
	"""Represents metadata for a release post."""

	def __init__(
		self,
		project_name: str,
		release_version: str,
		release_url: str,
		category_path: Path,  # Now a Path object for easier manipulation
		is_draft: bool = False,
		post_tags: List[str] = None,
		post_categories: List[str] = None,
		sidebar_weight: int = 10,
		hero_image: str = None,
	):
		self.project_name = project_name
		self.release_version = release_version
		self.release_url = release_url
		self.category_path = category_path
		self.is_draft = is_draft
		self.post_tags = post_tags or ["project", "release"]
		self.post_categories = post_categories or ["repository"]
		self.sidebar_weight = sidebar_weight
		self.hero_image = hero_image

	@property
	def parent_identifier(self) -> str:
		"""The parent of the version-post is the project identifier."""
		return self.project_name

	def create_sidebar_config(self) -> Dict:
		"""Generate sidebar navigation configuration."""
		return {
			"sidebar": {
				"name": self.release_version,
				"identifier": f"{self.project_name}-{self.release_version}",
				"parent": self.parent_identifier,
				"weight": self.sidebar_weight,
			}
		}

	def to_dict(self) -> Dict:
		"""Convert metadata to dictionary."""
		_data = {
			"date": time_now(iso8601=False, format="%Y-%m-%dT%H:%M:%SZ"),
			"draft": self.is_draft,
			"title": f"{self.project_name} {self.release_version}",
			"description": f"Release notes for {self.project_name} version {self.release_version}",
			"menu": self.create_sidebar_config(),
			"tags": self.post_tags,
			"categories": self.post_categories,
			"link": self.release_url,
		}
		if self.hero_image is not None:
			_data["hero"] = self.hero_image
		return _data


class ReleasePost(MarkdownDocument):
	"""Manages creation and storage of project release posts."""

	def __init__(self, metadata: ReleasePostMetadata, release_notes: str):
		self._metadata_obj = metadata
		metadata_dict = metadata.to_dict()
		super().__init__(content=release_notes, metadata=metadata_dict)
		self.add_content(
			f"Read more at [{self._metadata_obj.project_name}]({self._metadata_obj.release_url})",
			append=True,
		)

	def get_content_root(self, base_dir: str) -> Path:
		"""
		Determines the root path for the file.
		Structure: base_dir/content/posts/[category_path]/[project_name]
		"""
		return Path(base_dir).joinpath(
			"content/posts",
			self._metadata_obj.category_path,
			self._metadata_obj.project_name
		)

	def generate_post_path(self, base_dir: str) -> Path:
		"""Generate the full file path for the release post."""
		project_root = self.get_content_root(base_dir)
		# Final path: .../project_name/v1.0.0/index.md
		return project_root.joinpath(
			f"{self._metadata_obj.release_version}/index.md"
		)

	def _create_section_index(self, folder_path: Path, title: str, identifier: str, parent_id: Optional[str],
	                          weight: int = 10):
		"""Helper to create an _index.md if it doesn't exist."""
		index_path = folder_path.joinpath("_index.md")

		if index_path.exists():
			return

		print(f"Creating missing index: {index_path}")

		menu_config = {
			"name": title,
			"identifier": identifier,
			"weight": weight
		}
		if parent_id:
			menu_config["parent"] = parent_id

		metadata = {
			"title": title,
			"menu": {
				"sidebar": menu_config
			}
		}

		doc = MarkdownDocument(metadata=metadata)
		folder_path.mkdir(parents=True, exist_ok=True)
		doc.save(index_path)

	def ensure_hierarchy_exists(self, base_dir: str) -> None:
		"""
		Recursively creates _index.md files based on the split path.
		"""

		# 1. Base path: content/posts
		current_path = Path(base_dir).joinpath("content/posts")
		parent_id = None

		# 2. Iterate through CATEGORIES (e.g., tech -> backend)
		# We assume category_path is a Path object, e.g., Path("tech/backend")
		# If path is ".", parts will be empty
		category_parts = self._metadata_obj.category_path.parts

		for part in category_parts:
			if part == ".": continue

			current_path = current_path.joinpath(part)
			current_id = part
			display_name = part.replace("-", " ").title()

			self._create_section_index(
				folder_path=current_path,
				title=display_name,
				identifier=current_id,
				parent_id=parent_id,
				weight=10
			)
			parent_id = current_id

		# 3. Create the PROJECT index (e.g., my-tool)
		# The parent is the last category ID (or None if at root)
		project_path = current_path.joinpath(self._metadata_obj.project_name)
		project_id = self._metadata_obj.project_name
		project_title = self._metadata_obj.project_name.replace("-", " ").title()

		self._create_section_index(
			folder_path=project_path,
			title=project_title,
			identifier=project_id,
			parent_id=parent_id,
			weight=self._metadata_obj.sidebar_weight
		)

	def save_to_disk(self, base_dir: str) -> None:
		"""Save the post and hierarchy."""
		self.ensure_hierarchy_exists(base_dir)
		post_path = self.generate_post_path(base_dir)
		post_path.parent.mkdir(parents=True, exist_ok=True)
		super().save(post_path)


def parse_path_argument(path_str: str) -> Tuple[str, Path]:
	"""
	Splits a relative path into (Project Name, Category Path).
	Example: "tech/backend/my-tool" -> ("my-tool", Path("tech/backend"))
	Example: "my-tool" -> ("my-tool", Path("."))
	"""
	p = Path(path_str)
	project_name = p.name
	category_path = p.parent
	return project_name, category_path


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate a release post.")

	# CHANGED: 'path' now implies project location relative to posts/
	parser.add_argument(
		"--path",
		required=True,
		help="Relative path to project under posts/ (e.g., 'tech/backend/my-project')"
	)

	parser.add_argument("--version", "-v", required=True, help="Release version")
	parser.add_argument("--url", "-u", required=True, help="URL to the release")
	parser.add_argument("--notes", "-n", required=True, help="Note Content")
	parser.add_argument("--output-dir", "-o", required=True, help="Base directory")

	parser.add_argument("--draft", "-d", action="store_true")
	parser.add_argument("--tags", "-t", nargs="+")
	parser.add_argument("--categories", "-c", nargs="+")
	parser.add_argument("--weight", "-w", type=int, default=10)
	parser.add_argument("--hero", type=str, default=None)

	return parser.parse_args()


def main() -> None:
	args = parse_args()

	# 1. Parse the path to separate project name from folders
	project_name, category_path = parse_path_argument(args.path)

	metadata = ReleasePostMetadata(
		project_name=project_name,
		category_path=category_path,
		release_version=args.version,
		release_url=args.url,
		is_draft=args.draft,
		post_tags=args.tags,
		post_categories=args.categories,
		sidebar_weight=args.weight,
		hero_image=args.hero,
	)

	post = ReleasePost(metadata=metadata, release_notes=args.notes)
	post.save_to_disk(args.output_dir)
	print(f"Release post created at: {post.generate_post_path(args.output_dir)}")


if __name__ == "__main__":
	# python blog.py \
	#   --path "tech/tools/csv-parser" \
	#   --version "v1.2.0" \
	#   --output-dir "./my-site" \
	#   --notes "xxxxxxxx" \
	#   --url "www.google.com"
	main()
