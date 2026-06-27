import os
import io
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from utils import get_resize_dimensions


def apply_watermark(im, p):
    if p.get("wm") and os.path.exists(p["wm"]):
        orig_mode = im.mode 
        
        with Image.open(p["wm"]).convert("RGBA") as wm:
            target_w = int(im.size[0] * p["wm_size"])
            if target_w <= 0: return im
            
            ratio = target_w / float(wm.size[0])
            target_h = int(float(wm.size[1]) * ratio)
            if target_h <= 0: return im
            
            wm = wm.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            if p["wm_opacity"] < 1.0:
                alpha = wm.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(p["wm_opacity"])
                wm.putalpha(alpha)
            
            mx = p["wm_margin_x"]
            my = p["wm_margin_y"]
            
            pos_str = p["wm_pos"]
            if pos_str == "Top Left":
                x, y = mx, my
            elif pos_str == "Top Right":
                x, y = im.size[0] - wm.size[0] - mx, my
            elif pos_str == "Bottom Left":
                x, y = mx, im.size[1] - wm.size[1] - my
            elif pos_str == "Center":
                x, y = (im.size[0] - wm.size[0]) // 2, (im.size[1] - wm.size[1]) // 2
            else:
                x, y = im.size[0] - wm.size[0] - mx, im.size[1] - wm.size[1] - my
            
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            layer = Image.new("RGBA", im.size, (0,0,0,0))
            layer.paste(wm, (x, y))
            im = Image.alpha_composite(im, layer)
            
            if orig_mode == "L":
                im = im.convert("L")
            elif p["fmt"].upper() in ("JPEG", "JPG"):
                im = im.convert("RGB")
    return im


def convert_image(input_path, output_path, p):
    try:
        is_gif = p["fmt"].upper() == "GIF"
        
        if is_gif:
            with Image.open(input_path) as im:
                if getattr(im, "is_animated", False):
                    frames = []
                    durations = []
                    for frame_idx in range(im.n_frames):
                        im.seek(frame_idx)
                        frame = im.copy()
                        frame = ImageOps.exif_transpose(frame)
                        
                        if p["f_gray"]: frame = frame.convert("L")
                        if p["f_auto"]:
                            try: frame = ImageOps.autocontrast(frame.convert("RGB"))
                            except: pass
                        if p["f_sharp"]: frame = frame.filter(ImageFilter.SHARPEN)
                        if p["f_blur"]: frame = frame.filter(ImageFilter.BLUR)
                        if p["f_contour"]: frame = frame.filter(ImageFilter.CONTOUR)
                        if p["f_emboss"]: frame = frame.filter(ImageFilter.EMBOSS)
                        if p["f_edge"]: frame = frame.filter(ImageFilter.EDGE_ENHANCE_MORE)

                        if p["adj_b"] != 1.0: frame = ImageEnhance.Brightness(frame).enhance(p["adj_b"])
                        if p["adj_c"] != 1.0: frame = ImageEnhance.Contrast(frame).enhance(p["adj_c"])
                        if p["adj_s"] != 1.0: frame = ImageEnhance.Color(frame).enhance(p["adj_s"])
                        if p["adj_sh"] != 1.0: frame = ImageEnhance.Sharpness(frame).enhance(p["adj_sh"])

                        res_dim = get_resize_dimensions(frame.size, p.get("res_w_str", ""), p.get("res_h_str", ""))
                        if res_dim:
                            if p["mode"] == "Fit (Maintain AR)": frame = ImageOps.contain(frame, res_dim, Image.Resampling.LANCZOS)
                            elif p["mode"] == "Fill/Crop": frame = ImageOps.fit(frame, res_dim, Image.Resampling.LANCZOS)
                            else: frame = frame.resize(res_dim, Image.Resampling.LANCZOS)

                        frame = apply_watermark(frame, p)
                        frames.append(frame)
                        durations.append(im.info.get('duration', 100))
                        
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    frames[0].save(
                        output_path,
                        save_all=True,
                        append_images=frames[1:],
                        loop=im.info.get('loop', 0),
                        duration=durations,
                        optimize=True
                    )
                    return {"success": True}

        with Image.open(input_path) as im:
            im = ImageOps.exif_transpose(im)
            
            if p["f_gray"]: im = im.convert("L")
            if p["f_auto"]:
                try: im = ImageOps.autocontrast(im.convert("RGB"))
                except: pass
            if p["f_sharp"]: im = im.filter(ImageFilter.SHARPEN)
            if p["f_blur"]: im = im.filter(ImageFilter.BLUR)
            if p["f_contour"]: im = im.filter(ImageFilter.CONTOUR)
            if p["f_emboss"]: im = im.filter(ImageFilter.EMBOSS)
            if p["f_edge"]: im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)

            if p["adj_b"] != 1.0: im = ImageEnhance.Brightness(im).enhance(p["adj_b"])
            if p["adj_c"] != 1.0: im = ImageEnhance.Contrast(im).enhance(p["adj_c"])
            if p["adj_s"] != 1.0: im = ImageEnhance.Color(im).enhance(p["adj_s"])
            if p["adj_sh"] != 1.0: im = ImageEnhance.Sharpness(im).enhance(p["adj_sh"])

            res_dim = get_resize_dimensions(im.size, p.get("res_w_str", ""), p.get("res_h_str", ""))
            if res_dim:
                if p["mode"] == "Fit (Maintain AR)": im = ImageOps.contain(im, res_dim, Image.Resampling.LANCZOS)
                elif p["mode"] == "Fill/Crop": im = ImageOps.fit(im, res_dim, Image.Resampling.LANCZOS)
                else: im = im.resize(res_dim, Image.Resampling.LANCZOS)

            kwargs = {}
            exif = im.info.get("exif") if p["exif"] and "exif" in im.info else None
            
            if p["meta_en"] and p["fmt"].upper() in ("JPEG", "JPG", "TIFF"):
                if not exif:
                    exif = Image.Exif()
                else:
                    exif = im.getexif()
                if p["meta_auth"]: exif[315] = p["meta_auth"]
                if p.get("meta_copy"): exif[33432] = p["meta_copy"]
                if p.get("meta_desc"): exif[270] = p["meta_desc"]
                try:
                    kwargs["exif"] = exif.tobytes()
                except:
                    pass
            elif exif and p["fmt"].upper() in ("JPEG", "JPG"):
                kwargs["exif"] = exif

            if p["fmt"].upper() in ("JPEG", "JPG") and im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P": im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1] if 'A' in im.getbands() else None)
                im = bg

            im = apply_watermark(im, p)

            if p["fmt"].upper() in ("JPEG", "WEBP"):
                kwargs["quality"] = p["qual"]
                kwargs["optimize"] = True
            if p["fmt"].upper() == "PNG": kwargs["compress_level"] = 6

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if p["smart"] and p["fmt"].upper() in ("JPEG", "JPG", "WEBP"):
                low, high = 10, 100
                best_quality = p["qual"]
                target_bytes = p["target_kb"] * 1024
                
                for _ in range(7):
                    mid = (low + high) // 2
                    kwargs["quality"] = mid
                    buf = io.BytesIO()
                    im.save(buf, p["fmt"], **kwargs)
                    size = buf.tell()
                    
                    if size <= target_bytes:
                        best_quality = mid
                        low = mid + 1
                    else:
                        high = mid - 1
                
                kwargs["quality"] = best_quality
                im.save(output_path, p["fmt"], **kwargs)
            else:
                im.save(output_path, p["fmt"], **kwargs)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}