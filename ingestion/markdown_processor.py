"""
Markdown file processor for Docusaurus book content.

Loads .md/.mdx files, strips frontmatter and navigation, extracts chapter/section
metadata from file paths and content.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """Processes Docusaurus Markdown files for ingestion."""

    def __init__(self, docs_path: str, book_title: str):
        """
        Initialize markdown processor.

        Args:
            docs_path: Path to Docusaurus docs directory
            book_title: Title of the book
        """
        self.docs_path = Path(docs_path)
        self.book_title = book_title

        if not self.docs_path.exists():
            raise ValueError(f"Docs path does not exist: {docs_path}")

        logger.info(f"Initialized MarkdownProcessor: docs_path={docs_path}")

    def find_markdown_files(self) -> List[Path]:
        """
        Find all .md and .mdx files in docs directory.

        Returns:
            List of Path objects
        """
        md_files = list(self.docs_path.rglob("*.md"))
        mdx_files = list(self.docs_path.rglob("*.mdx"))

        all_files = md_files + mdx_files
        all_files.sort()

        logger.info(f"Found {len(all_files)} markdown files")

        return all_files

    def strip_frontmatter(self, content: str) -> str:
        """
        Remove YAML frontmatter from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Content without frontmatter
        """
        # Match YAML frontmatter (--- ... ---)
        frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'
        content = re.sub(frontmatter_pattern, '', content, flags=re.DOTALL)

        return content

    def clean_content(self, content: str) -> str:
        """
        Clean markdown content by removing navigation and excessive whitespace.

        Args:
            content: Markdown content

        Returns:
            Cleaned content
        """
        # Strip frontmatter
        content = self.strip_frontmatter(content)

        # Remove import statements (common in .mdx)
        content = re.sub(r'^import\s+.*?;?\s*$', '', content, flags=re.MULTILINE)

        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Remove JSX components that are navigation-only
        # (e.g., <NavigationButtons />, <TOC />, etc.)
        content = re.sub(r'<[A-Z][a-zA-Z]*\s*/>', '', content)
        content = re.sub(r'<[A-Z][a-zA-Z]*>.*?</[A-Z][a-zA-Z]*>', '', content, flags=re.DOTALL)

        # Collapse multiple blank lines to single blank line
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # Strip leading/trailing whitespace
        content = content.strip()

        return content

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from file path and content.

        Args:
            file_path: Path to markdown file

        Returns:
            Metadata dict with book_title, chapter, section, source_file
        """
        # Relative path from docs root
        rel_path = file_path.relative_to(self.docs_path)

        # Extract chapter from directory name
        # e.g., "02-ros2-foundations" -> "02 ROS2 Foundations"
        parts = rel_path.parts
        chapter = "Introduction"

        if len(parts) > 1:
            chapter_dir = parts[0]
            # Remove number prefix and convert to title case
            chapter = re.sub(r'^\d+-', '', chapter_dir)
            chapter = chapter.replace('-', ' ').title()

        # Extract section from filename
        # e.g., "module-1-ros2.md" -> "Module 1 ROS2"
        section = rel_path.stem
        section = re.sub(r'^\d+-', '', section)
        section = section.replace('-', ' ').title()

        metadata = {
            "book_title": self.book_title,
            "chapter": chapter,
            "section": section,
            "source_file": str(rel_path)
        }

        return metadata

    def process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            Dict with 'content' and 'metadata', or None if file is empty/invalid
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # Clean content
            content = self.clean_content(raw_content)

            if not content:
                logger.warning(f"Empty content after cleaning: {file_path}")
                return None

            # Extract metadata
            metadata = self.extract_metadata(file_path)

            logger.info(
                f"Processed {file_path.name}: "
                f"chapter={metadata['chapter']}, section={metadata['section']}"
            )

            return {
                "content": content,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return None

    def process_all_files(self) -> List[Dict[str, Any]]:
        """
        Process all markdown files in docs directory.

        Returns:
            List of processed documents with 'content' and 'metadata'
        """
        files = self.find_markdown_files()
        documents = []

        logger.info(f"Processing {len(files)} markdown files")

        for file_path in files:
            doc = self.process_file(file_path)
            if doc:
                documents.append(doc)

        logger.info(f"Successfully processed {len(documents)} documents")

        return documents
