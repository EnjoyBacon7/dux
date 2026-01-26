"""
CV Evaluation Pipeline - Visual Analysis Module (VLM)

Analyzes CV documents visually using a Vision-Language Model via OpenAI-compatible API.
Focuses exclusively on visual/structural aspects: layout, typography, spacing, readability.
Does NOT evaluate content, skills, or candidate quality.
"""

import json
import logging
import base64
from io import BytesIO
from typing import Optional, List
from pathlib import Path

from openai import OpenAI
from PIL import Image

from server.config import settings
from server.cv.cv_schemas import VisualAnalysis
from server.methods.upload import convert_file_to_images
from server.utils.prompts import load_prompt_template

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


def create_vlm_client() -> OpenAI:
    """Create VLM client with settings from config"""
    if not settings.vlm_key:
        raise ValueError("VLM API key not configured. Set VLM_KEY in environment variables.")
    if not settings.vlm_base_url:
        raise ValueError("VLM base URL not configured. Set VLM_BASE_URL in environment variables.")
    
    return OpenAI(
        api_key=settings.vlm_key,
        base_url=settings.vlm_base_url,
    )


def image_to_base64(image: Image.Image) -> str:
    """
    Convert PIL Image to base64-encoded string for API transmission.
    
    Args:
        image: PIL Image object
        
    Returns:
        Base64-encoded string (data URL format)
    """
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def _call_vlm_for_analysis(
    client: OpenAI,
    images: List[Image.Image],
    model: str
) -> VisualAnalysis:
    """
    Shared VLM call logic for visual analysis.
    
    Prepares images, calls the VLM API, and parses the response.
    
    Args:
        client: OpenAI client instance
        images: List of PIL Image objects to analyze
        model: Model name to use
        
    Returns:
        VisualAnalysis: Parsed visual analysis results
        
    Raises:
        ValueError: If VLM returns empty response or parsing fails
    """
    # Load prompts on first use (lazy loading)
    system_prompt, analysis_prompt = _load_vlm_prompts()
    
    # Prepare image content for API
    image_contents = [
        {"type": "image_url", "image_url": {"url": image_to_base64(img)}}
        for img in images
    ]
    
    # Prepare messages for VLM
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": analysis_prompt},
                *image_contents
            ]
        }
    ]
    
    # Call VLM API
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,  # Low temperature for consistent analysis
    )
    
    response_text = response.choices[0].message.content
    if not response_text:
        raise ValueError("VLM returned empty response")
    
    # Extract JSON from response
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start == -1 or json_end == 0:
        logger.warning(f"No JSON found in response: {response_text[:500]}")
        return _default_visual_analysis("Could not parse model response")
    
    json_str = response_text[json_start:json_end]
    analysis_data = json.loads(json_str)
    return _parse_visual_analysis(analysis_data)


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
    client = create_vlm_client()
    
    logger.info(f"Starting visual analysis using model: {model}")
    
    try:
        # Convert file to images
        images = convert_file_to_images(file_path, file_extension)
        if not images:
            raise ValueError("No images generated from CV file")
        
        logger.info(f"Converted CV to {len(images)} image(s) for visual analysis")
        
        # Call VLM for analysis using shared helper
        visual_analysis = _call_vlm_for_analysis(client, images, model)
        
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
    client = create_vlm_client()
    
    logger.info(f"Starting visual analysis from {len(images)} image(s) using model: {model}")
    
    try:
        # Call VLM for analysis using shared helper
        visual_analysis = _call_vlm_for_analysis(client, images, model)
        
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
