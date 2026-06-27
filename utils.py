def parse_int(val, default=10):
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def get_resize_dimensions(im_size, w_str, h_str):
    w = int(w_str) if w_str and w_str.isdigit() else None
    h = int(h_str) if h_str and h_str.isdigit() else None
    orig_w, orig_h = im_size
    
    if w and not h:
        h = int(orig_h * (w / float(orig_w)))
    elif h and not w:
        w = int(orig_w * (h / float(orig_h)))
        
    return (w, h) if w and h else None