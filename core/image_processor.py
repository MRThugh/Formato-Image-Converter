"""
Compatibility wrapper delegating to core.pipeline.
"""
from pathlib import Path
from typing import Dict, Any
from core.pipeline import process_image
from models.conversion_settings import ConversionSettings


def convert_image(input_path: str, output_path: str, p: Dict[str, Any]) -> Dict[str, Any]:
    settings = ConversionSettings.from_dict(p)
    res = process_image(
        source=input_path,
        settings=settings,
        output_path=output_path,
        preview=False
    )
    return res.to_dict()
