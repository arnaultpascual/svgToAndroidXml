import re
from converter.shape_converter import parse_style
from converter import shape_converter

def _parse_transform(transform_str):
    """
    A very simple transform parser for demonstration.
    Currently, supports only translate(x, y). For example: "translate(10,20)"
    Returns a dict with keys 'translateX' and 'translateY'.
    """
    result = {}
    m = re.search(r'translate\(([^,\)]+),?([^\)]+)?\)', transform_str)
    if m:
        tx = m.group(1).strip()
        ty = m.group(2).strip() if m.group(2) else "0"
        result['android:translateX'] = tx
        result['android:translateY'] = ty
    # (You can extend this to support scale, rotate, etc.)
    return result


def merge_styles(parent_style, child_style):
    """
    Merge two style dictionaries, with child values overriding parent's.
    """
    merged = parent_style.copy() if parent_style else {}
    if child_style:
        merged.update(child_style)
    return merged


def convert_group_element(elem, gradients, vp_width, vp_height, inherited_style=None):
    """
    Convert an SVG <g> element.
    - Merge the group's own style with any inherited style.
    - Parse a simple transform (currently only translate).
    - Recursively convert child elements.
    Returns a dictionary representing a group.
    """
    group_attribs = {}

    # Parse group's transform attribute (if present)
    transform_str = elem.attrib.get('transform', '')
    if transform_str:
        group_attribs.update(_parse_transform(transform_str))

    # Merge style: first, extract the group's own style (if any)
    group_style = parse_style(elem.attrib.get('style', ''))
    merged_style = merge_styles(inherited_style, group_style)

    # Process children recursively.
    children = []
    for child in list(elem):
        tag = child.tag.split('}')[-1].lower()
        if tag == 'g':
            # Nested group: pass along the merged style.
            children.append(convert_group_element(child, gradients, vp_width, vp_height, merged_style))
        elif tag in ['path', 'polygon', 'polyline', 'circle', 'ellipse', 'rect', 'line']:
            # Use your existing conversion functions.
            if tag == 'path':
                children.append(shape_converter.convert_path_element(child, gradients, vp_width, vp_height))
            elif tag == 'polygon':
                children.append(shape_converter.convert_polygon_element(child, gradients, vp_width, vp_height))
            elif tag == 'polyline':
                children.append(shape_converter.convert_polyline_element(child, gradients, vp_width, vp_height))
            elif tag == 'circle':
                children.append(shape_converter.convert_circle_element(child, gradients, vp_width, vp_height))
            elif tag == 'ellipse':
                children.append(shape_converter.convert_ellipse_element(child, gradients, vp_width, vp_height))
            elif tag == 'rect':
                children.append(shape_converter.convert_rect_element(child, gradients, vp_width, vp_height))
            elif tag == 'line':
                children.append(shape_converter.convert_line_element(child, gradients, vp_width, vp_height))
        elif tag == 'text':
            print("Warning: <text> element encountered; text-to-path conversion not implemented.")
            # Optionally: children.append({}) to skip text.
        elif tag in ['clippath', 'mask']:
            print(f"Warning: <{tag}> element encountered; clip/mask handling not implemented.")
        else:
            print(f"Warning: Unsupported element <{tag}> encountered in group.")

    return {
        'group': True,
        'attributes': group_attribs,
        'children': children,
        'style': merged_style
    }