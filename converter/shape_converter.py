"""
SVG to Android Vector Drawable Converter Utilities

This module provides functions for converting various SVG elements (paths, shapes,
gradients, etc.) into a dictionary format that represents Android vector drawable
attributes.
"""

import re
import math
from svg.path import parse_path, Move, Line, CubicBezier, QuadraticBezier, Arc, Close, Path

# --- Transformation helper functions ---

def multiply_matrices(m1, m2):
    """
    Multiply two 2D affine transformation matrices.

    The matrices m1 and m2 are represented as 6-tuples (a, b, c, d, e, f),
    which correspond to the 3x3 matrix:
        | a  c  e |
        | b  d  f |
        | 0  0  1 |

    This function returns the product of m1 and m2 in the same 6-tuple format.

    Parameters:
        m1 (tuple): The first matrix (a1, b1, c1, d1, e1, f1).
        m2 (tuple): The second matrix (a2, b2, c2, d2, e2, f2).

    Returns:
        tuple: The resulting matrix as a 6-tuple.
    """
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    a = a1 * a2 + c1 * b2
    b = b1 * a2 + d1 * b2
    c = a1 * c2 + c1 * d2
    d = b1 * c2 + d1 * d2
    e = a1 * e2 + c1 * f2 + e1
    f = b1 * e2 + d1 * f2 + f1
    return a, b, c, d, e, f

def parse_transform_attr(transform_str):
    """
    Parse a transform string into an affine transformation matrix.

    This function supports the following transformation types:
      - translate(tx [, ty])
      - scale(sx [, sy])
      - rotate(angle [, cx, cy])
      - matrix(a, b, c, d, e, f)

    The result is a 6-tuple representing the affine matrix (a, b, c, d, e, f).

    Parameters:
        transform_str (str): The transform attribute string from an SVG element.

    Returns:
        tuple: The resulting transformation matrix as a 6-tuple.
    """
    # Start with the identity matrix.
    matrix = (1, 0, 0, 1, 0, 0)
    # Iterate over all transformation functions found in the string.
    for part in re.finditer(r'(\w+)\(([^)]+)\)', transform_str):
        name = part.group(1)
        # Extract numerical values from the transformation parameters.
        values = list(map(float, re.findall(r'-?[\d\.]+', part.group(2))))
        if name == 'translate':
            tx = values[0]
            ty = values[1] if len(values) > 1 else 0
            m = (1, 0, 0, 1, tx, ty)
        elif name == 'scale':
            sx = values[0]
            sy = values[1] if len(values) > 1 else sx
            m = (sx, 0, 0, sy, 0, 0)
        elif name == 'rotate':
            # Convert angle from degrees to radians.
            angle = math.radians(values[0])
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            if len(values) > 2:
                # Rotation about a specified point (cx, cy)
                cx = values[1]
                cy = values[2]
                m = (cos_a, sin_a, -sin_a, cos_a,
                     -cx * cos_a + cx + cy * sin_a,
                     -cx * sin_a - cy * cos_a + cy)
            else:
                # Simple rotation about the origin.
                m = (cos_a, sin_a, -sin_a, cos_a, 0, 0)
        elif name == 'matrix' and len(values) == 6:
            m = tuple(values)
        else:
            # Unsupported transformation; use identity.
            m = (1, 0, 0, 1, 0, 0)
        # Multiply the current matrix with the new transformation matrix.
        matrix = multiply_matrices(matrix, m)
    return matrix

def apply_transform_to_point(x, y, matrix):
    """
    Apply an affine transformation to a 2D point.

    The transformation matrix is given as a 6-tuple (a, b, c, d, e, f).

    Parameters:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        matrix (tuple): The transformation matrix.

    Returns:
        tuple: The transformed (x, y) coordinates.
    """
    a, b, c, d, e, f = matrix
    new_x = a * x + c * y + e
    new_y = b * x + d * y + f
    return new_x, new_y

def transform_complex(z, matrix):
    """
    Apply an affine transformation to a complex number representing a point.

    Parameters:
        z (complex): The complex number (x + yj) representing the point.
        matrix (tuple): The transformation matrix (a, b, c, d, e, f).

    Returns:
        complex: The transformed point as a complex number.
    """
    x = z.real
    y = z.imag
    a, b, c, d, e, f = matrix
    return complex(a * x + c * y + e, b * x + d * y + f)

def transform_segment(seg, matrix):
    """
    Transform an SVG path segment using the given affine matrix.

    This function supports multiple segment types:
      - Move, Line, CubicBezier, QuadraticBezier, Arc, and Close.
      - If the segment is an Arc, it is converted into cubic Bézier curves,
        each of which is then transformed.

    Parameters:
        seg: An SVG path segment.
        matrix (tuple): The transformation matrix.

    Returns:
        The transformed segment. If the segment converts to multiple segments,
        a list of segments is returned.
    """
    if isinstance(seg, Move):
        return Move(transform_complex(seg.start, matrix))
    elif isinstance(seg, Line):
        return Line(transform_complex(seg.start, matrix), transform_complex(seg.end, matrix))
    elif isinstance(seg, CubicBezier):
        return CubicBezier(
            transform_complex(seg.start, matrix),
            transform_complex(seg.control1, matrix),
            transform_complex(seg.control2, matrix),
            transform_complex(seg.end, matrix)
        )
    elif isinstance(seg, QuadraticBezier):
        return QuadraticBezier(
            transform_complex(seg.start, matrix),
            transform_complex(seg.control, matrix),
            transform_complex(seg.end, matrix)
        )
    elif isinstance(seg, Arc):
        # Convert Arc to cubic Bézier curves, then transform each curve.
        curves = seg.as_cubic_curves()
        return [transform_segment(curve, matrix) for curve in curves]
    elif isinstance(seg, Close):
        # Transform the starting point; if the segment has an end, transform it as well.
        pt = transform_complex(seg.start, matrix)
        try:
            end_pt = transform_complex(seg.end, matrix)
        except AttributeError:
            end_pt = pt
        return Close(pt, end_pt)
    else:
        return seg

def transform_path(path_obj, matrix):
    """
    Apply an affine transformation to an entire SVG path object.

    Each segment of the path is transformed using transform_segment.

    Parameters:
        path_obj (Path): The SVG path object.
        matrix (tuple): The transformation matrix.

    Returns:
        Path: A new path object with all segments transformed.
    """
    new_segments = []
    for seg in path_obj:
        t = transform_segment(seg, matrix)
        if isinstance(t, list):
            new_segments.extend(t)
        else:
            new_segments.append(t)
    return Path(*new_segments)

# --- End transformation helpers ---

def parse_style(style):
    """
    Parse a CSS style string into a dictionary.

    This function works identically to the one defined earlier, splitting the style
    string on semicolons and then colons to build a dictionary of property-value pairs.

    Parameters:
        style (str): A CSS style string.

    Returns:
        dict: A dictionary mapping CSS properties to values.
    """
    style_dict = {}
    for part in style.split(';'):
        part = part.strip()
        if part and ':' in part:
            key, value = part.split(':', 1)
            style_dict[key.strip()] = value.strip()
    return style_dict

def extract_stop_color(stop_elem):
    """
    Extract the stop color from an SVG <stop> element, accounting for opacity.

    If the element has a style attribute, the function first attempts to extract the
    'stop-color' and 'stop-opacity' from it. If an opacity value is found, it is
    converted to a hexadecimal string and prepended to the color.

    Parameters:
        stop_elem (Element): The SVG <stop> element.

    Returns:
        str: The color value as a hex string (e.g., "#FF00FF").
    """
    style = stop_elem.attrib.get('style', '')
    color = stop_elem.attrib.get('stop-color', '#000000')
    if style:
        style_dict = parse_style(style)
        if 'stop-color' in style_dict:
            color = style_dict['stop-color']
        opacity = style_dict.get('stop-opacity', stop_elem.attrib.get('stop-opacity', ''))
    else:
        opacity = stop_elem.attrib.get('stop-opacity', '')
    if opacity:
        try:
            opacity_float = float(opacity)
            hex_opacity = format(int(opacity_float * 255), '02X')
            if len(color) == 7 and color.startswith('#'):
                color = '#' + hex_opacity + color[1:]
        except Exception:
            pass
    return color

def _convert_percentage(value, reference):
    """
    Convert a percentage string into an absolute value based on a reference.

    If the value ends with '%', it is converted to an absolute value using the reference.
    Otherwise, the value is returned as is.

    Parameters:
        value (str): The value to convert (e.g., "50%").
        reference (float): The reference value for conversion.

    Returns:
        str: The absolute value as a string.
    """
    if value.endswith('%'):
        try:
            perc = float(value.strip('%'))
            abs_val = perc * reference / 100.0
            return str(abs_val)
        except Exception:
            return value
    return value

def _fmt_number(val):
    """
    Format a numeric value as a string, removing the decimal if the number is an integer.

    For example, 100.0 becomes "100" and 100.5 becomes "100.5".

    Parameters:
        val: A value convertible to float.

    Returns:
        str: The formatted number as a string.
    """
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        else:
            return str(f)
    except Exception:
        return val

def convert_linear_gradient(grad_elem, vp_width, vp_height):
    """
    Convert an SVG <linearGradient> element into a dictionary representing an Android linear gradient.

    The function converts the gradient's x1, y1, x2, and y2 attributes (which may be percentages)
    using the viewport dimensions. It then builds a dictionary with the appropriate Android attributes
    and items (gradient stops).

    Parameters:
        grad_elem (Element): The SVG <linearGradient> element.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary representing the linear gradient.
    """
    x1 = _convert_percentage(grad_elem.attrib.get('x1', '0%'), vp_width)
    y1 = _convert_percentage(grad_elem.attrib.get('y1', '0%'), vp_height)
    x2 = _convert_percentage(grad_elem.attrib.get('x2', '100%'), vp_width)
    y2 = _convert_percentage(grad_elem.attrib.get('y2', '0%'), vp_height)
    stops = grad_elem.findall('.//{http://www.w3.org/2000/svg}stop')
    if stops:
        start_color = extract_stop_color(stops[0])
        end_color = extract_stop_color(stops[-1])
        gradient_structure = {
            'aapt_attr': True,
            'tag': 'gradient',
            'attributes': {
                'android:type': 'linear',
                'android:startX': _fmt_number(x1),
                'android:startY': _fmt_number(y1),
                'android:endX': _fmt_number(x2),
                'android:endY': _fmt_number(y2)
            },
            'items': [
                {'android:offset': "0", 'android:color': start_color},
                {'android:offset': "1", 'android:color': end_color}
            ]
        }
        return gradient_structure
    return {}

def convert_radial_gradient(grad_elem, vp_width, vp_height):
    """
    Convert an SVG <radialGradient> element into a dictionary representing an Android radial gradient.

    It converts the gradient's center (cx, cy) and radius (r) attributes (which may be percentages)
    based on the viewport dimensions. The resulting dictionary includes gradient stops as items.

    Parameters:
        grad_elem (Element): The SVG <radialGradient> element.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary representing the radial gradient.
    """
    cx = _convert_percentage(grad_elem.attrib.get('cx', '50%'), vp_width)
    cy = _convert_percentage(grad_elem.attrib.get('cy', '50%'), vp_height)
    ref = min(vp_width, vp_height)
    r  = _convert_percentage(grad_elem.attrib.get('r', '50%'), ref)
    stops = grad_elem.findall('.//{http://www.w3.org/2000/svg}stop')
    if stops:
        start_color = extract_stop_color(stops[0])
        end_color = extract_stop_color(stops[-1])
        gradient_structure = {
            'aapt_attr': True,
            'tag': 'gradient',
            'attributes': {
                'android:type': 'radial',
                'android:centerX': _fmt_number(cx),
                'android:centerY': _fmt_number(cy),
                'android:gradientRadius': _fmt_number(r)
            },
            'items': [
                {'android:offset': "0", 'android:color': start_color},
                {'android:offset': "1", 'android:color': end_color}
            ]
        }
        return gradient_structure
    return {}

def handle_gradient(fill_value, gradients, vp_width, vp_height):
    """
    Determine if a fill value refers to a gradient and, if so, convert it.

    If the fill_value starts with "url(", this function extracts the gradient ID,
    looks it up in the gradients dictionary (using lower-case keys), and converts the
    gradient using either the linear or radial conversion function.

    Parameters:
        fill_value (str): The fill attribute value from an SVG element.
        gradients (dict): Dictionary mapping gradient IDs to gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        tuple: (True, gradient_structure) if a gradient is found, otherwise (False, {}).
    """
    if fill_value.startswith("url("):
        grad_id = fill_value[fill_value.find('#')+1:fill_value.find(')')].lower()
        grad_elem = gradients.get(grad_id)
        if grad_elem is not None:
            tag = grad_elem.tag.split('}')[-1].lower()
            if tag == 'lineargradient':
                return True, convert_linear_gradient(grad_elem, vp_width, vp_height)
            elif tag == 'radialgradient':
                return True, convert_radial_gradient(grad_elem, vp_width, vp_height)
    return False, {}

def extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000', inherited_style=None):
    """
    Extract fill and stroke attributes from an SVG element, taking into account inline styles
    and inherited styles.

    Parameters:
        elem (Element): The SVG element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        default_fill (str): The default fill color if none is specified.
        inherited_style (dict): A dictionary of styles inherited from parent elements.

    Returns:
        dict: A dictionary containing the fill and stroke attributes for Android Vector Drawable.
    """
    # Get the fill from the element's attributes and inline style.
    fill = elem.attrib.get('fill', '')
    style = elem.attrib.get('style', '')
    if style:
        style_dict = parse_style(style)
        if 'fill' in style_dict:
            fill = style_dict['fill']
    # If no fill is defined, try using the inherited style.
    if not fill and inherited_style and 'fill' in inherited_style:
        fill = inherited_style['fill']
    result = {}
    has_gradient, gradient_struct = handle_gradient(fill, gradients, vp_width, vp_height)
    if has_gradient:
        result['gradient'] = gradient_struct
    else:
        result['android:fillColor'] = fill if fill else default_fill
    # Process stroke attributes.
    stroke = elem.attrib.get('stroke', '')
    if style:
        style_dict = parse_style(style)
        if 'stroke' in style_dict:
            stroke = style_dict['stroke']
    if stroke:
        result['android:strokeColor'] = stroke
    stroke_width = elem.attrib.get('stroke-width', '')
    if stroke_width:
        result['android:strokeWidth'] = stroke_width
    return result

def extract_stroke_and_width(elem):
    """
    Extract stroke color and stroke-width from an SVG element.

    Parameters:
        elem (Element): The SVG element.

    Returns:
        dict: A dictionary with 'android:strokeColor' and 'android:strokeWidth' if available.
    """
    result = {}
    style = elem.attrib.get('style', '')
    stroke = elem.attrib.get('stroke', '')
    if style:
        style_dict = parse_style(style)
        if 'stroke' in style_dict:
            stroke = style_dict['stroke']
    if stroke:
        result['android:strokeColor'] = stroke
    stroke_width = elem.attrib.get('stroke-width', '')
    if stroke_width:
        result['android:strokeWidth'] = stroke_width
    return result

# --- Updated conversion functions with inherited_style support ---

def convert_path_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <path> element into a dictionary of Android Vector Drawable attributes.

    This function processes the element's "d" attribute, applies any transformations,
    and extracts fill and stroke properties (including gradient conversion if applicable).

    Parameters:
        elem (Element): The SVG <path> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix to apply. Default is the identity.
        inherited_style (dict): Inherited style from parent elements, if any.

    Returns:
        dict: A dictionary containing Android vector drawable attributes for the path.
    """
    path_data = elem.attrib.get('d', '')
    own_transform = elem.attrib.get('transform', '')
    if own_transform:
        own_matrix = parse_transform_attr(own_transform)
        transform_matrix = multiply_matrices(transform_matrix, own_matrix)
    # If a transformation matrix is applied, transform the path data.
    if transform_matrix != (1, 0, 0, 1, 0, 0):
        try:
            path_obj = parse_path(path_data)
            transformed_path = transform_path(path_obj, transform_matrix)
            new_d = transformed_path.d()
        except Exception as e:
            print(f"Error processing path: {path_data}\n{e}")
            new_d = path_data
    else:
        new_d = path_data
    attributes = {'android:pathData': new_d}
    # Merge fill and stroke information.
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000', inherited_style=inherited_style))
    return attributes

def convert_polygon_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <polygon> element into a path-based representation.

    The "points" attribute is converted into a pathData string, and then fill and stroke
    attributes are extracted (with support for transformations and inherited styles).

    Parameters:
        elem (Element): The SVG <polygon> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix to apply.
        inherited_style (dict): Inherited style from parent elements.

    Returns:
        dict: A dictionary of Android vector drawable attributes.
    """
    points = elem.attrib.get('points', '')
    if not points:
        return {}
    coords = points.replace(',', ' ').split()
    if len(coords) % 2 != 0:
        raise ValueError("Invalid number of coordinates in polygon.")
    transformed_pairs = []
    for i in range(0, len(coords), 2):
        x = float(coords[i])
        y = float(coords[i+1])
        if transform_matrix != (1, 0, 0, 1, 0, 0):
            x, y = apply_transform_to_point(x, y, transform_matrix)
        transformed_pairs.append(f"{x} {y}")
    d = "M " + transformed_pairs[0] + " L " + " L ".join(transformed_pairs[1:]) + " Z"
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000', inherited_style=inherited_style))
    return attributes

def convert_polyline_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <polyline> element into a path-based representation.

    Similar to polygon, but the shape is not automatically closed.

    Parameters:
        elem (Element): The SVG <polyline> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix.
        inherited_style (dict): Inherited style from parent elements.

    Returns:
        dict: A dictionary of Android vector drawable attributes.
    """
    points = elem.attrib.get('points', '')
    if not points:
        return {}
    coords = points.replace(',', ' ').split()
    if len(coords) % 2 != 0:
        raise ValueError("Invalid number of coordinates in polyline.")
    transformed_pairs = []
    for i in range(0, len(coords), 2):
        x = float(coords[i])
        y = float(coords[i+1])
        if transform_matrix != (1, 0, 0, 1, 0, 0):
            x, y = apply_transform_to_point(x, y, transform_matrix)
        transformed_pairs.append(f"{x} {y}")
    d = "M " + transformed_pairs[0] + " L " + " L ".join(transformed_pairs[1:])
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='none', inherited_style=inherited_style))
    return attributes

def convert_circle_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <circle> element into a path-based representation.

    The circle is approximated by converting its center (cx, cy) and radius (r) into
    a pathData string (using two arcs). Transformations are applied if provided.

    Parameters:
        elem (Element): The SVG <circle> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix.
        inherited_style (dict): Inherited style from parent elements.

    Returns:
        dict: A dictionary of Android vector drawable attributes for the circle.
    """
    cx = float(elem.attrib.get('cx', '0'))
    cy = float(elem.attrib.get('cy', '0'))
    r = float(elem.attrib.get('r', '0'))
    if transform_matrix != (1, 0, 0, 1, 0, 0):
        # Apply transformation to the center.
        cx, cy = apply_transform_to_point(cx, cy, transform_matrix)
        # Compute transformed radius based on the distance of a point on the circle.
        px, py = apply_transform_to_point(cx + r, cy, transform_matrix)
        r = math.hypot(px - cx, py - cy)
    d = ("M {x} {y}".format(x=cx - r, y=cy) +
         " a {r} {r} 0 1 0 {diam} 0".format(r=r, diam=2*r) +
         " a {r} {r} 0 1 0 -{diam} 0".format(r=r, diam=2*r))
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000', inherited_style=inherited_style))
    return attributes

def convert_ellipse_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <ellipse> element into a path-based representation.

    The ellipse is approximated using arcs. If the fill attribute is a gradient reference,
    the gradient is overridden to use the ellipse's center (cx, cy) and its rx as the gradient radius.

    Parameters:
        elem (Element): The SVG <ellipse> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix.
        inherited_style (dict): Inherited style from parent elements.

    Returns:
        dict: A dictionary of Android vector drawable attributes for the ellipse.
    """
    cx = float(elem.attrib.get('cx', '0'))
    cy = float(elem.attrib.get('cy', '0'))
    rx = float(elem.attrib.get('rx', '0'))
    ry = float(elem.attrib.get('ry', '0'))
    if transform_matrix != (1, 0, 0, 1, 0, 0):
        # Apply transformation to the center and recalculate rx and ry.
        cx, cy = apply_transform_to_point(cx, cy, transform_matrix)
        px, py = apply_transform_to_point(cx + rx, cy, transform_matrix)
        rx = math.hypot(px - cx, py - cy)
        qx, qy = apply_transform_to_point(cx, cy + ry, transform_matrix)
        ry = math.hypot(qx - cx, qy - cy)
    d = ("M {x} {y}".format(x=cx - rx, y=cy) +
         " a {rx} {ry} 0 1 0 {diam_x} 0".format(rx=rx, ry=ry, diam_x=2*rx) +
         " a {rx} {ry} 0 1 0 -{diam_x} 0".format(rx=rx, ry=ry, diam_x=2*rx))
    attributes = {'android:pathData': d}
    style = elem.attrib.get('style', '')
    fill = elem.attrib.get('fill', '')
    if style:
        style_dict = parse_style(style)
        if 'fill' in style_dict:
            fill = style_dict['fill']
    if fill.startswith("url("):
        # Override the gradient using the ellipse's center and rx.
        grad_structure = {
            'aapt_attr': True,
            'tag': 'gradient',
            'attributes': {
                'android:type': 'radial',
                'android:centerX': _fmt_number(cx),
                'android:centerY': _fmt_number(cy),
                'android:gradientRadius': _fmt_number(rx)
            },
            'items': []
        }
        grad_id = fill[fill.find('#')+1:fill.find(')')].lower()
        grad_elem = gradients.get(grad_id)
        if grad_elem is not None:
            stops = grad_elem.findall('.//{http://www.w3.org/2000/svg}stop')
            if stops:
                start_color = extract_stop_color(stops[0])
                end_color = extract_stop_color(stops[-1])
                grad_structure['items'] = [
                    {'android:offset': "0", 'android:color': start_color},
                    {'android:offset': "1", 'android:color': end_color}
                ]
        attributes['gradient'] = grad_structure
    else:
        attributes['android:fillColor'] = fill if fill else '#000000'
    # Add stroke and stroke-width attributes.
    attributes.update(extract_stroke_and_width(elem))
    return attributes

def convert_rect_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <rect> element into a path-based representation.

    The rectangle is converted into a closed path by drawing lines between its four corners.

    Parameters:
        elem (Element): The SVG <rect> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix.
        inherited_style (dict): Inherited style from parent elements.

    Returns:
        dict: A dictionary of Android vector drawable attributes for the rectangle.
    """
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    width = float(elem.attrib.get('width', '0'))
    height = float(elem.attrib.get('height', '0'))
    pts = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    if transform_matrix != (1, 0, 0, 1, 0, 0):
        pts = [apply_transform_to_point(px, py, transform_matrix) for (px, py) in pts]
    d = "M {0} {1} L {2} {3} L {4} {5} L {6} {7} Z".format(
        pts[0][0], pts[0][1], pts[1][0], pts[1][1],
        pts[2][0], pts[2][1], pts[3][0], pts[3][1]
    )
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000', inherited_style=inherited_style))
    return attributes

def convert_line_element(elem, gradients, vp_width, vp_height, transform_matrix=(1,0,0,1,0,0), inherited_style=None):
    """
    Convert an SVG <line> element into a path-based representation.

    The line is represented using a "move to" (M) command followed by a "line to" (L) command.

    Parameters:
        elem (Element): The SVG <line> element.
        gradients (dict): Dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        transform_matrix (tuple): An affine transformation matrix.
        inherited_style (dict): Inherited style from parent elements.

    Returns:
        dict: A dictionary of Android vector drawable attributes for the line.
    """
    x1 = float(elem.attrib.get('x1', '0'))
    y1 = float(elem.attrib.get('y1', '0'))
    x2 = float(elem.attrib.get('x2', '0'))
    y2 = float(elem.attrib.get('y2', '0'))
    if transform_matrix != (1, 0, 0, 1, 0, 0):
        x1, y1 = apply_transform_to_point(x1, y1, transform_matrix)
        x2, y2 = apply_transform_to_point(x2, y2, transform_matrix)
    d = "M {0} {1} L {2} {3}".format(x1, y1, x2, y2)
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='none', inherited_style=inherited_style))
    return attributes