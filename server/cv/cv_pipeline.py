"""
CV Evaluation Pipeline - Step 4: Pipeline Orchestrator

Ties all steps together and produces traceable output:
1. Takes raw CV text as input
2. Runs LLM extraction (Step 1)
3. Runs deterministic validation (Step 2)
4. Runs LLM scoring (Step 3)
5. Saves complete evaluation result as JSON

All intermediate outputs are preserved for traceability and auditability.
"""

import json
import logging
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from server.cv.cv_schemas import EvaluationResult, StructuredCV, DerivedFeatures, CVScores
from server.cv.cv_extractor import extract_cv_facts
from server.cv.cv_validator import validate_and_compute_features
from server.cv.cv_scorer import score_cv

logger = logging.getLogger(__name__)

# Default output directory for evaluation results
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "evaluations"


class CVEvaluationPipeline:
    """
    Complete CV evaluation pipeline with full traceability.
    
    Usage:
        pipeline = CVEvaluationPipeline()
        result = pipeline.evaluate(raw_cv_text)
        pipeline.save_result(result)
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        model: Optional[str] = None,
        save_results: bool = True,
    ):
        """
        Initialize the pipeline.
        
        Args:
            output_dir: Directory to save evaluation results (default: ./evaluations)
            model: OpenAI model to use (default: from settings)
            save_results: Whether to automatically save results
        """
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.model = model
        self.save_results = save_results
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate(
        self,
        raw_cv_text: str,
        cv_filename: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Run the complete CV evaluation pipeline.
        
        Args:
            raw_cv_text: Raw text content of the CV
            cv_filename: Optional original filename for reference
        
        Returns:
            EvaluationResult: Complete evaluation with all intermediate outputs
        
        Raises:
            ValueError: If any step fails
        """
        start_time = time.time()
        evaluation_id = str(uuid.uuid4())
        errors = []
        
        logger.info(f"Starting CV evaluation pipeline (ID: {evaluation_id})")
        
        # Step 1: Extract structured facts
        logger.info("Step 1: Extracting structured facts from CV...")
        try:
            structured_cv = extract_cv_facts(raw_cv_text, model=self.model)
            logger.info("Step 1 complete: Structured CV extracted")
        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            errors.append(f"Extraction failed: {e}")
            raise ValueError(f"Pipeline failed at Step 1 (Extraction): {e}")
        
        # Step 2: Validate and compute features
        logger.info("Step 2: Validating and computing derived features...")
        try:
            derived_features = validate_and_compute_features(structured_cv)
            logger.info(f"Step 2 complete: {derived_features.experience_count} experiences, "
                       f"{len(derived_features.timeline_gaps)} gaps detected")
        except Exception as e:
            logger.error(f"Step 2 failed: {e}")
            errors.append(f"Validation failed: {e}")
            raise ValueError(f"Pipeline failed at Step 2 (Validation): {e}")
        
        # Step 3: Score the CV
        logger.info("Step 3: Scoring CV...")
        try:
            scores = score_cv(structured_cv, derived_features, model=self.model)
            logger.info(f"Step 3 complete: Overall score = {scores.overall_score}")
        except Exception as e:
            logger.error(f"Step 3 failed: {e}")
            errors.append(f"Scoring failed: {e}")
            raise ValueError(f"Pipeline failed at Step 3 (Scoring): {e}")
        
        # Step 4: Assemble final result
        processing_time = time.time() - start_time
        
        result = EvaluationResult(
            evaluation_id=evaluation_id,
            cv_filename=cv_filename,
            raw_cv_text=raw_cv_text,
            structured_cv=structured_cv,
            derived_features=derived_features,
            scores=scores,
            processing_time_seconds=round(processing_time, 2),
            errors=errors,
        )
        
        logger.info(f"Pipeline complete in {processing_time:.2f}s")
        
        # Auto-save if enabled
        if self.save_results:
            self.save_result(result)
        
        return result
    
    def save_result(self, result: EvaluationResult) -> Path:
        """
        Save evaluation result to JSON file.
        
        Args:
            result: The evaluation result to save
        
        Returns:
            Path: Path to the saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if result.cv_filename:
            # Remove extension from filename
            base_name = Path(result.cv_filename).stem
            filename = f"{base_name}_{timestamp}.json"
        else:
            filename = f"cv_evaluation_{timestamp}_{result.evaluation_id[:8]}.json"
        
        output_path = self.output_dir / filename
        
        # Convert to JSON-serializable dict
        result_dict = result.model_dump(mode='json')
        
        # Write to file with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Evaluation saved to: {output_path}")
        return output_path
    
    def evaluate_from_file(
        self,
        file_path: str,
        extract_text: bool = True,
    ) -> EvaluationResult:
        """
        Evaluate a CV from a file.
        
        Args:
            file_path: Path to CV file (PDF, DOCX, or TXT)
            extract_text: If True, extract text from file; if False, read as plain text
        
        Returns:
            EvaluationResult: Complete evaluation
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CV file not found: {file_path}")
        
        if extract_text and file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
            # Use the existing upload module for text extraction
            from server.methods.upload import extract_text_from_file
            raw_text = extract_text_from_file(file_path, file_path.suffix.lower())
        else:
            # Read as plain text
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        
        return self.evaluate(raw_text, cv_filename=file_path.name)


def evaluate_cv(
    raw_cv_text: str,
    cv_filename: Optional[str] = None,
    save_result: bool = True,
    model: Optional[str] = None,
) -> EvaluationResult:
    """
    Convenience function to run the full evaluation pipeline.
    
    Args:
        raw_cv_text: Raw CV text content
        cv_filename: Optional original filename
        save_result: Whether to save the result to JSON
        model: Optional model override
    
    Returns:
        EvaluationResult: Complete evaluation
    """
    pipeline = CVEvaluationPipeline(model=model, save_results=save_result)
    return pipeline.evaluate(raw_cv_text, cv_filename)


def evaluate_cv_file(
    file_path: str,
    save_result: bool = True,
    model: Optional[str] = None,
) -> EvaluationResult:
    """
    Convenience function to evaluate a CV from file.
    
    Args:
        file_path: Path to CV file
        save_result: Whether to save the result
        model: Optional model override
    
    Returns:
        EvaluationResult: Complete evaluation
    """
    pipeline = CVEvaluationPipeline(model=model, save_results=save_result)
    return pipeline.evaluate_from_file(file_path)


def load_evaluation(file_path: str) -> EvaluationResult:
    """
    Load a saved evaluation result from JSON file.
    
    Args:
        file_path: Path to the evaluation JSON file
    
    Returns:
        EvaluationResult: Loaded evaluation
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return EvaluationResult.model_validate(data)


