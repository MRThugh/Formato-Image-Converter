import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any
from config import SUPPORTED_FORMATS, RESIZE_MODES, WATERMARK_POSITIONS


@dataclass
class ConversionSettings:
    schema_version: int = 1

    # Format & Quality
    fmt: str = "WEBP"
    qual: int = 85
    smart: bool = False
    target_kb: int = 150

    # Resize
    mode: str = "Fit (Maintain AR)"
    res_w_str: str = ""
    res_h_str: str = ""

    # Adjustments
    adj_b: float = 1.0   # Brightness (0.1 to 2.5)
    adj_c: float = 1.0   # Contrast (0.1 to 2.5)
    adj_s: float = 1.0   # Saturation/Color (0.0 to 2.5)
    adj_sh: float = 1.0  # Sharpness (0.0 to 3.0)

    # Filters
    f_gray: bool = False
    f_auto: bool = False
    f_sharp: bool = False
    f_blur: bool = False
    f_contour: bool = False
    f_emboss: bool = False
    f_edge: bool = False

    # Watermark
    wm: str = ""
    wm_pos: str = "Bottom Right"
    wm_size: float = 0.20   # 0.05 to 1.0
    wm_opacity: float = 0.75 # 0.05 to 1.0
    wm_margin_x: int = 15
    wm_margin_y: int = 15

    # Metadata
    exif: bool = True       # Preserve original EXIF when True
    meta_en: bool = False   # Enable custom metadata injection
    meta_auth: str = ""
    meta_copy: str = ""
    meta_desc: str = ""

    # Naming & Output
    pref: str = ""
    suff: str = ""
    out_dir: str = ""

    def validate(self) -> None:
        """Sanitizes and clamps all values to valid bounds."""
        if self.fmt.upper() not in SUPPORTED_FORMATS:
            self.fmt = "WEBP"
        self.qual = max(1, min(100, int(self.qual)))
        self.target_kb = max(1, int(self.target_kb))

        if self.mode not in RESIZE_MODES:
            self.mode = "Fit (Maintain AR)"

        self.adj_b = max(0.1, min(3.0, float(self.adj_b)))
        self.adj_c = max(0.1, min(3.0, float(self.adj_c)))
        self.adj_s = max(0.0, min(3.0, float(self.adj_s)))
        self.adj_sh = max(0.0, min(4.0, float(self.adj_sh)))

        if self.wm_pos not in WATERMARK_POSITIONS:
            self.wm_pos = "Bottom Right"
        self.wm_size = max(0.01, min(1.0, float(self.wm_size)))
        self.wm_opacity = max(0.0, min(1.0, float(self.wm_opacity)))
        self.wm_margin_x = max(0, int(self.wm_margin_x))
        self.wm_margin_y = max(0, int(self.wm_margin_y))

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversionSettings":
        # Extract known fields only, graceful fallback on older schemas
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        instance = cls(**filtered)
        instance.validate()
        return instance

    def save_preset_file(self, file_path: Path) -> None:
        self.validate()
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_preset_file(cls, file_path: Path) -> "ConversionSettings":
        file_path = Path(file_path)
        if not file_path.exists():
            return cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
