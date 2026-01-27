"""
CV Evaluation Pipeline - Visual Analysis Module (VLM)

Analyzes CV documents visually using a Vision-Language Model via OpenAI-compatible API.
Focuses exclusively on visual/structural aspects: layout, typography, spacing, readability.
Does NOT evaluate content, skills, or candidate quality.
"""

import json
import logging
from typing import Optional, List
from pathlib import Path

from PIL import Image

from server.config import settings
from server.cv.cv_schemas import VisualAnalysis
from server.methods.upload import convert_file_to_images
from server.utils.prompts import load_prompt_template
from server.utils.llm import call_llm_sync

logger = logging.getLogger(__name__)


# Lazy-loaded prompts (loaded on first use)
_VLM_SYSTEM_PROMPT: Optional[str] = None
_VLM_ANALYSIS_PROMPT: Optional[str] = None


def _load_vlm_prompts() -> tuple[str, str]:
    """
    Lazy-load VLM prompts on first use.
    
    Returns:
        Tuple of (system_prompt, analysis_prompt)
        
    Raises:
        FileNotFoundError: If prompt templates are missing
    """
    global _VLM_SYSTEM_PROMPT, _VLM_ANALYSIS_PROMPT
    
    if _VLM_SYSTEM_PROMPT is None or _VLM_ANALYSIS_PROMPT is None:
        _VLM_SYSTEM_PROMPT = load_prompt_template("cv_vlm_system")
        _VLM_ANALYSIS_PROMPT = load_prompt_template("cv_vlm_analysis")
    
    return _VLM_SYSTEM_PROMPT, _VLM_ANALYSIS_PROMPT


def _call_vlm_for_analysis(images: List[Image.Image], model: str) -> VisualAnalysis:
    """
    Shared VLM call logic for visual analysis.
    
    Prepares images, calls the VLM API, and parses the response.
    
    Args:
        images: List of PIL Image objects to analyze
        model: Model name to use
        
    Returns:
        VisualAnalysis: Parsed visual analysis results
        
    Raises:
        ValueError: If VLM returns empty response or parsing fails
    """
    # Load prompts on first use (lazy loading)
    system_prompt, analysis_prompt = _load_vlm_prompts()
    
    # Use consolidated LLM function with VLM request
    try:
        result = call_llm_sync(
            prompt=analysis_prompt,
            system_content=system_prompt,
            temperature=0.2,  # Low temperature for consistent analysis
            max_tokens=2000,
            parse_json=True,
            model=model,
            vlm_request={"images": images, "use_vlm_client": True}
        )
        
        analysis_data = result["data"]
        return _parse_visual_analysis(analysis_data)
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse VLM response as JSON")
        return _default_visual_analysis("Could not parse model response")
    except Exception as e:
        logger.exception(f"VLM analysis failed: {e}")
        raise ValueError(f"VLM analysis failed: {e}") from e


def analyze_cv_visuals(
    file_path: Path,
    file_extension: str,
    model: Optional[str] = None
) -> VisualAnalysis:
    """
    Analyze CV document visually using VLM.
    
    Args:
        file_path: Path to the CV file (PDF, DOCX, etc.)
        file_extension: File extension (e.g., ".pdf", ".docx")
        model: Optional model override (defaults to settings.vlm_model)
    
    Returns:
        VisualAnalysis: Visual analysis results
        
    Raises:
        ValueError: If analysis fails or returns invalid data
    """
    model = model or settings.vlm_model
    
    logger.info(f"Starting visual analysis using model: {model}")
    
    try:
        # Convert file to images
        images = convert_file_to_images(file_path, file_extension)
        if not images:
            raise ValueError("No images generated from CV file")
        
        logger.info(f"Converted CV to {len(images)} image(s) for visual analysis")
        
        # Call VLM for analysis using shared helper
        visual_analysis = _call_vlm_for_analysis(images, model)
        
        logger.info(f"Visual analysis complete: {len(visual_analysis.visual_strengths)} strengths, "
                   f"{len(visual_analysis.visual_weaknesses)} weaknesses, "
                   f"{len(visual_analysis.visual_recommendations)} recommendations")
        
        return visual_analysis
        
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse VLM response as JSON")
        return _default_visual_analysis(f"JSON parse error: {e}")
    except Exception as e:
        logger.exception("Visual analysis failed")
        raise ValueError(f"Visual analysis failed: {e}") from e


def analyze_cv_visuals_from_images(
    images: List[Image.Image],
    model: Optional[str] = None
) -> VisualAnalysis:
    """
    Analyze CV visuals directly from PIL Image objects.
    
    Useful when images are already available (e.g., from previous conversion).
    
    Args:
        images: List of PIL Image objects
        model: Optional model override
        
    Returns:
        VisualAnalysis: Visual analysis results
    """
    model = model or settings.vlm_model
    
    logger.info(f"Starting visual analysis from {len(images)} image(s) using model: {model}")
    
    try:
        # Call VLM for analysis using shared helper
        visual_analysis = _call_vlm_for_analysis(images, model)
        
        logger.info("Visual analysis complete from images")
        
        return visual_analysis
        
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse VLM response as JSON")
        return _default_visual_analysis(f"JSON parse error: {e}")
    except Exception as e:
        logger.exception("Visual analysis from images failed")
        raise ValueError(f"Visual analysis failed: {e}") from e


def _parse_visual_analysis(data: dict) -> VisualAnalysis:
    """
    Parse VLM JSON response into validated VisualAnalysis model.
    
    Handles missing fields gracefully and validates structure.
    """
    return VisualAnalysis(
        visual_strengths=data.get("visual_strengths", []),
        visual_weaknesses=data.get("visual_weaknesses", []),
        visual_recommendations=data.get("visual_recommendations", []),
        layout_assessment=data.get("layout_assessment"),
        typography_assessment=data.get("typography_assessment"),
        readability_assessment=data.get("readability_assessment"),
        image_quality_notes=data.get("image_quality_notes", []),
    )


def _default_visual_analysis(error_note: str) -> VisualAnalysis:
    """
    Return a default VisualAnalysis when parsing fails.
    """
    return VisualAnalysis(
        visual_strengths=[],
        visual_weaknesses=[],
        visual_recommendations=["Unable to perform visual analysis - please ensure the document is a clear PDF"],
        layout_assessment=None,
        typography_assessment=None,
        readability_assessment=None,
        image_quality_notes=[error_note],
    )
