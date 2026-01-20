"""
CV Evaluation Pipeline - Manual Test Runner

This script allows manual testing of the CV evaluation pipeline
using existing CV files from the uploads folder or raw text input.

Usage:
    # From the dux directory, run:
    python -m server.cv.test_cv_pipeline
    
    # Or with specific options:
    python -m server.cv.test_cv_pipeline --file uploads/example.pdf
    python -m server.cv.test_cv_pipeline --list
    python -m server.cv.test_cv_pipeline --all
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directories to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.cv.cv_pipeline import CVEvaluationPipeline, evaluate_cv_file, load_evaluation
from server.cv.cv_schemas import EvaluationResult
from server.methods.upload import extract_text_from_file

# Default uploads directory
UPLOADS_DIR = PROJECT_ROOT / "uploads"


def list_available_cvs() -> list[Path]:
    """List all CV files in the uploads directory"""
    if not UPLOADS_DIR.exists():
        logger.warning(f"Uploads directory not found: {UPLOADS_DIR}")
        return []
    
    cv_files = []
    for ext in ['.pdf', '.docx', '.doc', '.txt']:
        cv_files.extend(UPLOADS_DIR.glob(f'*{ext}'))
    
    return sorted(cv_files)


def print_evaluation_summary(result: EvaluationResult):
    """Print a human-readable summary of the evaluation"""
    # Set console encoding for Windows compatibility
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "=" * 80)
    print("CV EVALUATION SUMMARY")
    print("=" * 80)
    
    print(f"\nEvaluation ID: {result.evaluation_id}")
    print(f"CV File: {result.cv_filename or 'N/A'}")
    print(f"Processing Time: {result.processing_time_seconds}s")
    
    # Overall score
    print(f"\n{'─' * 40}")
    print(f"OVERALL SCORE: {result.scores.overall_score}/100")
    print(f"{'─' * 40}")
    print(f"\n{result.scores.overall_summary}")
    
    # Dimension scores
    print(f"\n{'─' * 40}")
    print("DIMENSION SCORES")
    print(f"{'─' * 40}")
    
    dimensions = [
        ("Completeness", result.scores.completeness),
        ("Experience Quality", result.scores.experience_quality),
        ("Skills Relevance", result.scores.skills_relevance),
        ("Impact Evidence", result.scores.impact_evidence),
        ("Clarity", result.scores.clarity),
        ("Consistency", result.scores.consistency),
    ]
    
    for name, dim in dimensions:
        print(f"\n{name}: {dim.score}/100")
        print(f"  → {dim.justification}")
    
    # Derived features highlights
    print(f"\n{'─' * 40}")
    print("KEY METRICS")
    print(f"{'─' * 40}")
    
    df = result.derived_features
    print(f"• Total Experience: {df.total_experience_years or 'N/A'} years ({df.experience_count} positions)")
    print(f"• Education Entries: {df.education_count}")
    print(f"• Skills Listed: {df.skills_count}")
    print(f"• Projects: {df.projects_count}")
    print(f"• Certifications: {df.certifications_count}")
    print(f"• Quantified Results: {df.quantified_results_count}")
    print(f"• Average Tenure: {df.avg_tenure_months:.1f if df.avg_tenure_months else 'N/A'} months")
    
    if df.timeline_gaps:
        print(f"• Employment Gaps: {len(df.timeline_gaps)}")
    if df.job_hopping_flag:
        print("• ⚠️  Job Hopping Detected")
    
    # Strengths and weaknesses
    print(f"\n{'─' * 40}")
    print("STRENGTHS")
    print(f"{'─' * 40}")
    for strength in result.scores.strengths:
        print(f"  ✓ {strength}")
    
    print(f"\n{'─' * 40}")
    print("AREAS FOR IMPROVEMENT")
    print(f"{'─' * 40}")
    for weakness in result.scores.weaknesses:
        print(f"  • {weakness}")
    
    # Red flags
    if result.scores.red_flags:
        print(f"\n{'─' * 40}")
        print("⚠️  RED FLAGS")
        print(f"{'─' * 40}")
        for flag in result.scores.red_flags:
            print(f"  ⚠ {flag}")
    
    # Recommendations
    print(f"\n{'─' * 40}")
    print("RECOMMENDATIONS")
    print(f"{'─' * 40}")
    for i, rec in enumerate(result.scores.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 80)


def evaluate_single_cv(file_path: Path, save: bool = True) -> Optional[EvaluationResult]:
    """Evaluate a single CV file"""
    print(f"\nEvaluating: {file_path.name}")
    print("-" * 40)
    
    try:
        result = evaluate_cv_file(str(file_path), save_result=save)
        print_evaluation_summary(result)
        return result
    except Exception as e:
        logger.error(f"Failed to evaluate {file_path.name}: {e}")
        print(f"ERROR: {e}")
        return None


def evaluate_all_cvs(save: bool = True) -> list[EvaluationResult]:
    """Evaluate all CV files in the uploads directory"""
    cv_files = list_available_cvs()
    
    if not cv_files:
        print("No CV files found in uploads directory")
        return []
    
    print(f"\nFound {len(cv_files)} CV files to evaluate")
    results = []
    
    for i, file_path in enumerate(cv_files, 1):
        print(f"\n[{i}/{len(cv_files)}] Processing {file_path.name}...")
        result = evaluate_single_cv(file_path, save=save)
        if result:
            results.append(result)
    
    # Print summary
    print("\n" + "=" * 80)
    print("BATCH EVALUATION COMPLETE")
    print("=" * 80)
    print(f"Processed: {len(cv_files)} files")
    print(f"Successful: {len(results)} evaluations")
    print(f"Failed: {len(cv_files) - len(results)} evaluations")
    
    if results:
        avg_score = sum(r.scores.overall_score for r in results) / len(results)
        print(f"Average Score: {avg_score:.1f}/100")
    
    return results


def evaluate_from_text(text: str, save: bool = True) -> Optional[EvaluationResult]:
    """Evaluate CV from raw text input"""
    print("\nEvaluating CV from text input...")
    print("-" * 40)
    
    try:
        pipeline = CVEvaluationPipeline(save_results=save)
        result = pipeline.evaluate(text, cv_filename="text_input")
        print_evaluation_summary(result)
        return result
    except Exception as e:
        logger.error(f"Failed to evaluate text: {e}")
        print(f"ERROR: {e}")
        return None


def interactive_mode():
    """Run in interactive mode with menu"""
    while True:
        print("\n" + "=" * 50)
        print("CV EVALUATION PIPELINE - Interactive Mode")
        print("=" * 50)
        print("\n1. List available CVs")
        print("2. Evaluate a specific CV")
        print("3. Evaluate all CVs")
        print("4. Evaluate text input")
        print("5. Load and view saved evaluation")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            cv_files = list_available_cvs()
            if cv_files:
                print(f"\nFound {len(cv_files)} CV files:")
                for i, f in enumerate(cv_files, 1):
                    print(f"  {i}. {f.name}")
            else:
                print("\nNo CV files found")
        
        elif choice == "2":
            cv_files = list_available_cvs()
            if not cv_files:
                print("\nNo CV files found")
                continue
            
            print("\nAvailable CVs:")
            for i, f in enumerate(cv_files, 1):
                print(f"  {i}. {f.name}")
            
            idx = input("\nEnter number to evaluate (or filename): ").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(cv_files):
                    evaluate_single_cv(cv_files[idx])
                else:
                    print("Invalid selection")
            except ValueError:
                # Try as filename
                file_path = UPLOADS_DIR / idx
                if file_path.exists():
                    evaluate_single_cv(file_path)
                else:
                    print(f"File not found: {idx}")
        
        elif choice == "3":
            confirm = input("\nEvaluate all CVs? (y/n): ").strip().lower()
            if confirm == 'y':
                evaluate_all_cvs()
        
        elif choice == "4":
            print("\nPaste CV text (enter 'END' on a new line when done):")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            
            if lines:
                evaluate_from_text('\n'.join(lines))
            else:
                print("No text provided")
        
        elif choice == "5":
            eval_dir = Path(__file__).parent / "evaluations"
            if not eval_dir.exists():
                print("\nNo evaluations directory found")
                continue
            
            eval_files = list(eval_dir.glob("*.json"))
            if not eval_files:
                print("\nNo saved evaluations found")
                continue
            
            print("\nSaved evaluations:")
            for i, f in enumerate(eval_files, 1):
                print(f"  {i}. {f.name}")
            
            idx = input("\nEnter number to load: ").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(eval_files):
                    result = load_evaluation(str(eval_files[idx]))
                    print_evaluation_summary(result)
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")
        
        elif choice == "6":
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid option")


def main():
    parser = argparse.ArgumentParser(
        description="CV Evaluation Pipeline - Manual Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m server.cv.test_cv_pipeline                    # Interactive mode
  python -m server.cv.test_cv_pipeline --list             # List available CVs
  python -m server.cv.test_cv_pipeline --file cv.pdf      # Evaluate specific file
  python -m server.cv.test_cv_pipeline --all              # Evaluate all CVs
  python -m server.cv.test_cv_pipeline --no-save          # Don't save results
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to CV file to evaluate"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available CV files in uploads directory"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Evaluate all CVs in uploads directory"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save evaluation results to JSON"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    save = not args.no_save
    
    # Handle different modes
    if args.list:
        cv_files = list_available_cvs()
        if cv_files:
            print(f"Found {len(cv_files)} CV files in {UPLOADS_DIR}:")
            for f in cv_files:
                print(f"  - {f.name}")
        else:
            print(f"No CV files found in {UPLOADS_DIR}")
    
    elif args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            # Try relative to uploads directory first
            if (UPLOADS_DIR / file_path).exists():
                file_path = UPLOADS_DIR / file_path
            elif not file_path.exists():
                # Try relative to project root
                file_path = PROJECT_ROOT / file_path
        
        if file_path.exists():
            evaluate_single_cv(file_path, save=save)
        else:
            print(f"File not found: {args.file}")
            sys.exit(1)
    
    elif args.all:
        evaluate_all_cvs(save=save)
    
    elif args.interactive or len(sys.argv) == 1:
        # Default to interactive mode
        interactive_mode()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

