from converter.svg_parser import parse_svg
from converter.shape_converter import (
    convert_path_element,
    convert_polygon_element,
    convert_polyline_element,
    convert_circle_element,
    convert_ellipse_element,
    convert_rect_element,
    convert_line_element
)
from converter.group_converter import convert_group_element  # if using groups
from converter.xml_builder import build_vector_drawable, write_vector_drawable

def get_viewport_dimensions(svg_attrib):
    viewBox = svg_attrib.get('viewBox')
    if viewBox:
        parts = viewBox.split()
        if len(parts) == 4:
            try:
                return float(parts[2]), float(parts[3])
            except Exception:
                pass
    try:
        vp_width = float(svg_attrib.get('width', '24').replace('px',''))
        vp_height = float(svg_attrib.get('height', '24').replace('px',''))
        return vp_width, vp_height
    except Exception:
        return 24.0, 24.0

def extract_gradients(root, ns, vp_width, vp_height):
    gradients = {}
    ns_uri = ns.get('svg', 'http://www.w3.org/2000/svg')
    for grad in root.findall('.//{{{}}}linearGradient'.format(ns_uri)):
        grad_id = grad.attrib.get('id')
        if grad_id:
            gradients[grad_id.lower()] = grad
    for grad in root.findall('.//{{{}}}radialGradient'.format(ns_uri)):
        grad_id = grad.attrib.get('id')
        if grad_id:
            gradients[grad_id.lower()] = grad
    return gradients

def convert_svg_to_vector_drawable(svg_file, output_file):
    root, ns = parse_svg(svg_file)
    svg_attrib = root.attrib
    vp_width, vp_height = get_viewport_dimensions(svg_attrib)
    gradients = extract_gradients(root, ns, vp_width, vp_height)
    elements = []
    for elem in root.iter():
        tag = elem.tag.split('}')[-1].lower()
        if tag == 'g':
            group_dict = convert_group_element(elem, gradients, vp_width, vp_height)
            elements.append(group_dict)
        elif tag == 'path':
            conv = convert_path_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag == 'polygon':
            conv = convert_polygon_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag == 'polyline':
            conv = convert_polyline_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag == 'circle':
            conv = convert_circle_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag == 'ellipse':
            conv = convert_ellipse_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag == 'rect':
            conv = convert_rect_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag == 'line':
            conv = convert_line_element(elem, gradients, vp_width, vp_height)
            if conv:
                elements.append(conv)
        elif tag in ['text', 'clippath', 'mask']:
            print(f"Warning: <{tag}> element encountered; conversion not fully implemented.")
        else:
            # Ignore defs and unsupported tags.
            pass

    vector = build_vector_drawable(svg_attrib, elements, vp_width, vp_height)
    write_vector_drawable(vector, output_file)