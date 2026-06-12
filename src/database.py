"""
Database management utilities for CGPSC Intelligence System.

Handles storage, retrieval, and aggregation of analyzed exam papers
across multiple years for trend analysis.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_ROOT = PROJECT_ROOT / "database"
QUESTIONS_DB = DATABASE_ROOT / "questions"


@dataclass
class PaperMetadata:
    """Metadata for an analyzed paper."""
    year: int
    exam: str
    total_questions: int
    taxonomy_version: str
    ingested_at: str = ""
    source_file: Optional[str] = ""
    schema_version: str = "analyzer-record-v1"
    
    def __post_init__(self):
        if not self.ingested_at:
            self.ingested_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PaperDatabase:
    """
    Manages storage and retrieval of analyzed CGPSC papers.
    
    Single responsibility: Database operations for question records.
    Designed for multi-year aggregation pipelines.
    """
    
    def __init__(self, db_root: Optional[Path] = None):
        """
        Initialize the paper database.
        
        Args:
            db_root: Root path for database (default: database/)
        """
        self.db_root = db_root or DATABASE_ROOT
        self.questions_dir = self.db_root / "questions"
        self.metadata_dir = self.db_root / "metadata"
        self.index_file = self.db_root / "index.json"
        
        # Create directories
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database initialized at {self.db_root}")
    
    def get_paper_path(self, year: int) -> Path:
        """
        Get the file path for a paper of a given year.
        
        Args:
            year: Exam year
            
        Returns:
            Path to the paper JSON file
        """
        return self.questions_dir / f"{year}.json"
    
    def get_metadata_path(self, year: int) -> Path:
        """
        Get the metadata file path for a paper.
        
        Args:
            year: Exam year
            
        Returns:
            Path to the metadata JSON file
        """
        return self.metadata_dir / f"{year}_metadata.json"
    
    def paper_exists(self, year: int) -> bool:
        """
        Check if a paper for a given year exists in the database.
        
        Args:
            year: Exam year
            
        Returns:
            True if paper exists, False otherwise
        """
        return self.get_paper_path(year).exists()
    
    def ingest_paper(
        self,
        analyzed_file: Path,
        year: int,
        overwrite: bool = False
    ) -> Tuple[bool, str]:
        """
        Ingest an analyzed paper into the database.
        
        Args:
            analyzed_file: Path to analyzed JSON file
            year: Exam year
            overwrite: Whether to overwrite existing paper
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If paper already exists and overwrite=False
        """
        # Validate input file
        if not analyzed_file.exists():
            raise FileNotFoundError(f"Input file not found: {analyzed_file}")
        
        # Check for existing paper
        paper_path = self.get_paper_path(year)
        if paper_path.exists() and not overwrite:
            msg = f"Paper for {year} already exists. Use overwrite=True to replace."
            logger.warning(msg)
            return False, msg
        
        try:
            # Load analyzed data
            logger.info(f"Loading analyzed paper from {analyzed_file}")
            with open(analyzed_file, 'r', encoding='utf-8') as f:
                analyzed_data = json.load(f)
            
            # Validate schema
            if analyzed_data.get('schema_version') != 'analyzer-record-v1':
                raise ValueError(
                    f"Invalid schema version: {analyzed_data.get('schema_version')}. "
                    "Expected: analyzer-record-v1"
                )
            
            # Verify year consistency
            data_year = analyzed_data.get('year')
            if data_year != year:
                raise ValueError(
                    f"Year mismatch: provided {year}, but file contains {data_year}"
                )
            
            # Extract metadata
            metadata = PaperMetadata(
                year=year,
                exam=analyzed_data.get('exam', 'CGPSC Prelims'),
                total_questions=len(analyzed_data.get('questions', [])),
                taxonomy_version=analyzed_data.get('taxonomy_version'),
                source_file=str(analyzed_file)
            )
            
            # Save paper
            logger.info(f"Saving paper for {year} to {paper_path}")
            with open(paper_path, 'w', encoding='utf-8') as f:
                json.dump(analyzed_data, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata_path = self.get_metadata_path(year)
            logger.info(f"Saving metadata for {year} to {metadata_path}")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update index
            self._update_index(year, metadata)
            
            msg = f"✓ Paper for {year} ingested successfully ({metadata.total_questions} questions)"
            logger.info(msg)
            return True, msg
            
        except json.JSONDecodeError as e:
            msg = f"Failed to parse JSON from {analyzed_file}: {e}"
            logger.error(msg)
            raise
        except Exception as e:
            msg = f"Error ingesting paper for {year}: {e}"
            logger.error(msg)
            raise
    
    def load_paper(self, year: int) -> Dict[str, Any]:
        """
        Load an analyzed paper from the database.
        
        Args:
            year: Exam year
            
        Returns:
            Analyzed paper dictionary
            
        Raises:
            FileNotFoundError: If paper doesn't exist
        """
        paper_path = self.get_paper_path(year)
        
        if not paper_path.exists():
            raise FileNotFoundError(f"Paper for {year} not found in database")
        
        logger.info(f"Loading paper for {year} from database")
        with open(paper_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_questions(self, year: int) -> List[Dict[str, Any]]:
        """
        Load questions from a paper.
        
        Args:
            year: Exam year
            
        Returns:
            List of question dictionaries
            
        Raises:
            FileNotFoundError: If paper doesn't exist
        """
        paper = self.load_paper(year)
        return paper.get('questions', [])
    
    def load_metadata(self, year: int) -> PaperMetadata:
        """
        Load metadata for a paper.
        
        Args:
            year: Exam year
            
        Returns:
            PaperMetadata object
            
        Raises:
            FileNotFoundError: If metadata doesn't exist
        """
        metadata_path = self.get_metadata_path(year)
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata for {year} not found in database")
        
        logger.info(f"Loading metadata for {year}")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PaperMetadata(**data)
    
    def list_papers(self) -> List[int]:
        """
        List all years with papers in the database.
        
        Returns:
            Sorted list of years
        """
        years = []
        for path in self.questions_dir.glob('*.json'):
            try:
                year = int(path.stem)
                years.append(year)
            except ValueError:
                continue
        
        return sorted(years, reverse=True)
    
    def get_papers_metadata(self) -> List[PaperMetadata]:
        """
        Get metadata for all papers in the database.
        
        Returns:
            List of PaperMetadata objects, sorted by year (newest first)
        """
        papers = []
        for year in self.list_papers():
            try:
                metadata = self.load_metadata(year)
                papers.append(metadata)
            except FileNotFoundError:
                logger.warning(f"Metadata not found for {year}")
                continue
        
        return papers
    
    def _update_index(self, year: int, metadata: PaperMetadata) -> None:
        """
        Update the database index with paper information.
        
        Args:
            year: Exam year
            metadata: Paper metadata
        """
        # Load existing index
        index = {}
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        
        # Update entry
        index[str(year)] = {
            'year': year,
            'exam': metadata.exam,
            'total_questions': metadata.total_questions,
            'taxonomy_version': metadata.taxonomy_version,
            'ingested_at': metadata.ingested_at
        }
        
        # Save updated index
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated database index")
    
    def get_index(self) -> Dict[str, Any]:
        """
        Get the database index.
        
        Returns:
            Dictionary mapping year strings to paper info
        """
        if not self.index_file.exists():
            return {}
        
        with open(self.index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def print_database_status(self) -> None:
        """Print human-readable database status to console."""
        papers = self.get_papers_metadata()
        
        print("\n" + "="*70)
        print("CGPSC INTELLIGENCE DATABASE STATUS")
        print("="*70)
        
        if not papers:
            print("\n(No papers in database)\n")
            print("="*70 + "\n")
            return
        
        print(f"\nTotal Papers: {len(papers)}\n")
        
        total_questions = sum(p.total_questions for p in papers)
        print(f"{'Year':<8} {'Exam':<20} {'Questions':<12} {'Ingested':<20}")
        print("-" * 70)
        
        for metadata in papers:
            ingested_date = metadata.ingested_at.split('T')[0]
            print(
                f"{metadata.year:<8} {metadata.exam:<20} "
                f"{metadata.total_questions:<12} {ingested_date:<20}"
            )
        
        print("-" * 70)
        print(f"Total Questions Across All Papers: {total_questions}\n")
        print("="*70 + "\n")


def main():
    """Example usage of the database."""
    db = PaperDatabase()
    db.print_database_status()


if __name__ == "__main__":
    main()
