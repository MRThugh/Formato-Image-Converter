import io
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from models.conversion_settings import ConversionSettings
from core.watermark import apply_watermark
from utils.helpers import get_resize_dimensions
from utils.filenames import get_temp_output_path


class ProcessingResult:
    def __init__(
        self,
        success: bool,
        output_path: Optional[Path] = None,
        error_msg: str = "",
        actual_size_bytes: int = 0,
        target_size_bytes: int = 0,
        target_size_achieved: bool = True,
        final_quality: int = 85,
        preview_image: Optional[Image.Image] = None,
        was_cancelled: bool = False
    ):
        self.success = success
        self.output_path = output_path
        self.error_msg = error_msg
        self.actual_size_bytes = actual_size_bytes
        self.target_size_bytes = target_size_bytes
        self.target_size_achieved = target_size_achieved
        self.final_quality = final_quality
        self.preview_image = preview_image
        self.was_cancelled = was_cancelled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "error": self.error_msg,
            "actual_size": self.actual_size_bytes,
            "target_size": self.target_size_bytes,
            "target_achieved": self.target_size_achieved,
            "quality": self.final_quality,
            "cancelled": self.was_cancelled
        }


def _apply_frame_transformations(
    im: Image.Image,
    s: ConversionSettings,
    preview_mode: bool = False
) -> Image.Image:
    """
    Applies filters, color/contrast/brightness adjustments, and resize to a single frame.
    This logic is identical for previews, single conversions, and animated GIF frames.
    """
    # 1. Filters
    if s.f_gray:
        im = im.convert("L")

    if s.f_auto:
        try:
            if im.mode == "L":
                im = ImageOps.autocontrast(im)
            else:
                im = ImageOps.autocontrast(im.convert("RGB"))
        except Exception:
            pass

    if s.f_sharp:
        im = im.filter(ImageFilter.SHARPEN)
    if s.f_blur:
        im = im.filter(ImageFilter.BLUR)
    if s.f_contour:
        im = im.filter(ImageFilter.CONTOUR)
    if s.f_emboss:
        im = im.filter(ImageFilter.EMBOSS)
    if s.f_edge:
        im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)

    # 2. Adjustments (Brightness, Contrast, Saturation, Sharpness)
    if s.adj_b != 1.0:
        im = ImageEnhance.Brightness(im).enhance(s.adj_b)
    if s.adj_c != 1.0:
        im = ImageEnhance.Contrast(im).enhance(s.adj_c)
    if s.adj_s != 1.0 and im.mode not in ("L", "1"):
        im = ImageEnhance.Color(im).enhance(s.adj_s)
    if s.adj_sh != 1.0:
        im = ImageEnhance.Sharpness(im).enhance(s.adj_sh)

    # 3. Resize Calculation
    res_dim = get_resize_dimensions(im.size, s.res_w_str, s.res_h_str)
    if res_dim:
        mode_lower = s.mode.lower()
        if "fit" in mode_lower:
            im = ImageOps.contain(im, res_dim, Image.Resampling.LANCZOS)
        elif "fill" in mode_lower or "crop" in mode_lower:
            im = ImageOps.fit(im, res_dim, Image.Resampling.LANCZOS)
        else:  # Stretch
            im = im.resize(res_dim, Image.Resampling.LANCZOS)

    # 4. Watermark
    if s.wm:
        im = apply_watermark(
            im=im,
            watermark_path=s.wm,
            position=s.wm_pos,
            scale_ratio=s.wm_size,
            opacity=s.wm_opacity,
            margin_x=s.wm_margin_x,
            margin_y=s.wm_margin_y,
            target_format=s.fmt
        )

    return im


def process_image(
    source: Union[str, Path, Image.Image],
    settings: ConversionSettings,
    output_path: Optional[Union[str, Path]] = None,
    preview: bool = False,
    preview_max_dim: int = 800,
    cancel_event: Optional[threading.Event] = None
) -> ProcessingResult:
    """
    Central Image Processing Pipeline for Formato.
    Used uniformly by Preview, Single Conversion, and Batch Conversion.
    """
    settings.validate()

    if cancel_event and cancel_event.is_set():
        return ProcessingResult(success=False, was_cancelled=True, error_msg="Cancelled by user")

    # Step 1: Open Source Image
    temp_target_path: Optional[Path] = None
    try:
        if isinstance(source, Image.Image):
            base_img = source.copy()
        else:
            source_path = Path(source)
            if not source_path.exists():
                return ProcessingResult(success=False, error_msg=f"Source file not found: {source_path.name}")
            base_img = Image.open(source_path)

        fmt_upper = settings.fmt.upper()
        if fmt_upper == "JPG":
            fmt_upper = "JPEG"

        is_animated_gif = getattr(base_img, "is_animated", False) and fmt_upper == "GIF"

        if is_animated_gif:
            frames: List[Image.Image] = []
            durations: List[int] = []
            n_frames = getattr(base_img, "n_frames", 1)

            for frame_idx in range(n_frames):
                if cancel_event and cancel_event.is_set():
                    base_img.close()
                    return ProcessingResult(success=False, was_cancelled=True, error_msg="Cancelled by user")

                base_img.seek(frame_idx)
                f_copy = base_img.copy()
                try:
                    f_copy = ImageOps.exif_transpose(f_copy)
                except Exception:
                    pass

                if preview:
                    f_copy.thumbnail((preview_max_dim, preview_max_dim), Image.Resampling.LANCZOS)

                processed_f = _apply_frame_transformations(f_copy, settings, preview_mode=preview)
                frames.append(processed_f)
                durations.append(base_img.info.get("duration", 100))

                if preview:
                    break

            base_img.close()

            if preview:
                return ProcessingResult(
                    success=True,
                    preview_image=frames[0] if frames else None,
                    final_quality=settings.qual
                )

            # Save Animated GIF
            if not output_path:
                return ProcessingResult(success=False, error_msg="Output path must be specified")

            target_p = Path(output_path)
            target_p.parent.mkdir(parents=True, exist_ok=True)
            temp_target_path = get_temp_output_path(target_p)

            loop_val = base_img.info.get("loop", 0) if hasattr(base_img, "info") else 0
            frames[0].save(
                temp_target_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                loop=loop_val,
                duration=durations,
                optimize=True
            )

            actual_size = temp_target_path.stat().st_size
            os.replace(temp_target_path, target_p)

            return ProcessingResult(
                success=True,
                output_path=target_p,
                actual_size_bytes=actual_size,
                final_quality=settings.qual
            )

        # Step 2: EXIF Orientation Transpose for static images
        try:
            base_img = ImageOps.exif_transpose(base_img)
        except Exception:
            pass

        # Static Image Processing
        if preview:
            # Scale down before processing for swift real-time UI feedback
            base_img.thumbnail((preview_max_dim, preview_max_dim), Image.Resampling.LANCZOS)

        processed_img = _apply_frame_transformations(base_img, settings, preview_mode=preview)

        if cancel_event and cancel_event.is_set():
            base_img.close()
            return ProcessingResult(success=False, was_cancelled=True, error_msg="Cancelled by user")

        if preview:
            return ProcessingResult(
                success=True,
                preview_image=processed_img,
                final_quality=settings.qual
            )

        # Preparation for Export
        if not output_path:
            return ProcessingResult(success=False, error_msg="Output path not provided")

        target_p = Path(output_path)
        target_p.parent.mkdir(parents=True, exist_ok=True)
        temp_target_path = get_temp_output_path(target_p)

        save_kwargs: Dict[str, Any] = {}

        # Handle Metadata
        exif_bytes = None
        if settings.exif:
            # Extract existing EXIF if available
            orig_exif = base_img.info.get("exif")
            if orig_exif:
                exif_bytes = orig_exif

        if settings.meta_en and fmt_upper in ("JPEG", "TIFF"):
            try:
                exif_obj = base_img.getexif() if hasattr(base_img, "getexif") else Image.Exif()
                if not exif_obj:
                    exif_obj = Image.Exif()
                if settings.meta_auth:
                    exif_obj[315] = settings.meta_auth
                if settings.meta_copy:
                    exif_obj[33432] = settings.meta_copy
                if settings.meta_desc:
                    exif_obj[270] = settings.meta_desc
                exif_bytes = exif_obj.tobytes()
            except Exception:
                pass

        if exif_bytes and fmt_upper in ("JPEG", "TIFF", "WEBP"):
            save_kwargs["exif"] = exif_bytes

        # Mode Conversion based on format compatibility
        final_img = processed_img
        if fmt_upper in ("JPEG", "JPG"):
            if final_img.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", final_img.size, (255, 255, 255))
                if final_img.mode == "P":
                    final_img = final_img.convert("RGBA")
                mask = final_img.split()[-1] if "A" in final_img.getbands() else None
                bg.paste(final_img, mask=mask)
                final_img = bg
            elif final_img.mode not in ("RGB", "L"):
                final_img = final_img.convert("RGB")
        elif fmt_upper == "BMP":
            if final_img.mode != "RGB":
                final_img = final_img.convert("RGB")

        # Format-specific save options
        final_quality = settings.qual
        achieved_target = True
        target_bytes = settings.target_kb * 1024

        if fmt_upper in ("JPEG", "WEBP"):
            save_kwargs["optimize"] = True
            if settings.smart:
                # Binary search quality from 10 to 100 to target byte size
                low, high = 10, 100
                best_q = 10
                best_size = 0

                for _ in range(7):
                    if cancel_event and cancel_event.is_set():
                        return ProcessingResult(success=False, was_cancelled=True, error_msg="Cancelled by user")

                    mid_q = (low + high) // 2
                    buf = io.BytesIO()
                    save_kwargs["quality"] = mid_q
                    final_img.save(buf, format=fmt_upper, **save_kwargs)
                    cur_size = buf.tell()

                    if cur_size <= target_bytes:
                        best_q = mid_q
                        best_size = cur_size
                        low = mid_q + 1
                    else:
                        high = mid_q - 1

                # If even quality 10 exceeds target_bytes, measure actual at q=10
                if best_size == 0 or best_size > target_bytes:
                    best_q = 10
                    buf = io.BytesIO()
                    save_kwargs["quality"] = 10
                    final_img.save(buf, format=fmt_upper, **save_kwargs)
                    best_size = buf.tell()
                    if best_size > target_bytes:
                        achieved_target = False

                final_quality = best_q
                save_kwargs["quality"] = final_quality
            else:
                save_kwargs["quality"] = final_quality
        elif fmt_upper == "PNG":
            save_kwargs["compress_level"] = 6
            save_kwargs["optimize"] = True

        # Atomic Save via temporary file
        final_img.save(temp_target_path, format=fmt_upper, **save_kwargs)
        actual_size = temp_target_path.stat().st_size
        os.replace(temp_target_path, target_p)

        return ProcessingResult(
            success=True,
            output_path=target_p,
            actual_size_bytes=actual_size,
            target_size_bytes=target_bytes if settings.smart else 0,
            target_size_achieved=achieved_target,
            final_quality=final_quality
        )

    except Exception as e:
        if temp_target_path and temp_target_path.exists():
            try:
                temp_target_path.unlink()
            except Exception:
                pass
        return ProcessingResult(success=False, error_msg=str(e))
