"""
SVG to Android Vector Drawable Converter Utilities

This module provides functions for converting various SVG elements (paths, shapes,
gradients, etc.) into a dictionary format that represents Android vector drawable
attributes. The code handles inline CSS styles, gradient definitions, and constructs
the proper Android attributes for each element.
"""

def parse_style(style):
    """
    Parse a CSS style string into a dictionary.

    Splits a style string (e.g., "fill:#000; stroke:none;") into a dictionary mapping
    CSS property names to values.

    Parameters:
        style (str): A CSS style string.

    Returns:
        dict: A dictionary of style properties and their values.
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
    Extract the color from an SVG <stop> element, accounting for style overrides and opacity.

    Checks for a 'style' attribute to override the default 'stop-color'. If an opacity
    value is provided (either in the style or as an attribute), it is converted from a
    0–1 range into a hexadecimal alpha value, which is inserted into the color (if the
    color is in "#RRGGBB" format).

    Parameters:
        stop_elem (Element): An XML element representing an SVG <stop>.

    Returns:
        str: A hexadecimal color string (e.g., "#FF0000" or "#AARRGGBB" if opacity is applied).
    """
    style = stop_elem.attrib.get('style', '')
    color = stop_elem.attrib.get('stop-color', '#000000')
    if style:
        style_dict = parse_style(style)
        # Override the stop-color if specified in the style.
        if 'stop-color' in style_dict:
            color = style_dict['stop-color']
        # Retrieve stop-opacity from style or attribute.
        opacity = style_dict.get('stop-opacity', stop_elem.attrib.get('stop-opacity', ''))
    else:
        opacity = stop_elem.attrib.get('stop-opacity', '')
    if opacity:
        try:
            opacity_float = float(opacity)
            # Convert opacity (0.0–1.0) to a 2-digit hex value.
            hex_opacity = format(int(opacity_float * 255), '02X')
            # If the color is in the "#RRGGBB" format, insert the alpha channel.
            if len(color) == 7 and color.startswith('#'):
                color = '#' + hex_opacity + color[1:]
        except Exception:
            pass
    return color

def _convert_percentage(value, reference):
    """
    Convert a percentage value to an absolute value based on a reference.

    If the value ends with '%', it is interpreted as a percentage of the reference;
    otherwise, the original value is returned.

    Parameters:
        value (str): A numeric string or percentage (e.g., "50%" or "100").
        reference (float): The reference value to use if value is a percentage.

    Returns:
        str: The absolute value (as a string) if conversion was possible; otherwise, the original value.
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
    Format a number by removing unnecessary decimals.

    Converts the string to a float and returns an integer string if the value is whole,
    otherwise returns the float as a string.

    Parameters:
        val (str): A string representing a number.

    Returns:
        str: A formatted number.
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
    Convert an SVG <linearGradient> element to an Android gradient structure.

    Converts percentage-based gradient coordinates (x1, y1, x2, y2) to absolute values
    based on the viewport dimensions and extracts the first and last <stop> colors to form
    a two-color gradient.

    Parameters:
        grad_elem (Element): An XML element for an SVG linear gradient.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary representing the Android gradient attributes or an empty
              dictionary if no <stop> elements are found.
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
    Convert an SVG <radialGradient> element to an Android gradient structure.

    The center coordinates (cx, cy) and radius (r) may be specified in percentages,
    so they are converted based on the viewport dimensions (or the smaller of the two for r).

    Parameters:
        grad_elem (Element): An XML element for an SVG radial gradient.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary representing the Android gradient attributes or an empty
              dictionary if no <stop> elements are found.
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
    Check if a fill attribute specifies a gradient and, if so, convert it.

    If the fill value starts with "url(", it is treated as a reference to a gradient.
    The function extracts the gradient ID, locates the corresponding SVG gradient element,
    and then converts it based on its type (linear or radial).

    Parameters:
        fill_value (str): The fill attribute value from an SVG element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width for percentage calculations.
        vp_height (float): The viewport height for percentage calculations.

    Returns:
        tuple: A pair (has_gradient, gradient_structure) where has_gradient is a boolean
               indicating whether a gradient was found, and gradient_structure is the converted
               gradient dictionary (or {} if not applicable).
    """
    if fill_value.startswith("url("):
        # Extract the gradient ID from the fill reference.
        grad_id = fill_value[fill_value.find('#')+1:fill_value.find(')')].lower()
        grad_elem = gradients.get(grad_id)
        if grad_elem is not None:
            tag = grad_elem.tag.split('}')[-1].lower()
            if tag == 'lineargradient':
                return True, convert_linear_gradient(grad_elem, vp_width, vp_height)
            elif tag == 'radialgradient':
                return True, convert_radial_gradient(grad_elem, vp_width, vp_height)
    return False, {}

def extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000'):
    """
    Extract fill, stroke, and stroke-width properties from an SVG element,
    handling inline styles and gradient references.

    The fill property is first taken from the element's attribute and then
    overridden by any inline style. If the fill value references a gradient (via "url(...)"),
    the helper function `handle_gradient` is used to convert it. Stroke attributes are also
    extracted in a similar manner.

    Parameters:
        elem (Element): The SVG element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width (for percentage calculations).
        vp_height (float): The viewport height.
        default_fill (str): The default fill color to use if none is provided.

    Returns:
        dict: A dictionary of Android vector drawable attributes that may include:
              - 'android:fillColor' or 'gradient'
              - 'android:strokeColor'
              - 'android:strokeWidth'
    """
    # Extract fill from attribute and override with style if present.
    fill = elem.attrib.get('fill', '')
    style = elem.attrib.get('style', '')
    if style:
        style_dict = parse_style(style)
        if 'fill' in style_dict:
            fill = style_dict['fill']

    result = {}
    # Check for a gradient reference in the fill.
    has_gradient, gradient_struct = handle_gradient(fill, gradients, vp_width, vp_height)
    if has_gradient:
        result['gradient'] = gradient_struct
    else:
        result['android:fillColor'] = fill if fill else default_fill

    # Extract stroke and stroke-width.
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
    Extract stroke and stroke-width properties from an SVG element,
    taking into account inline style overrides.

    Parameters:
        elem (Element): The SVG element.

    Returns:
        dict: A dictionary that may include 'android:strokeColor' and 'android:strokeWidth'.
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

def convert_path_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <path> element to Android vector drawable attributes.

    Extracts the path data ('d' attribute), and then adds common fill, stroke,
    and stroke-width properties using the helper function.

    Parameters:
        elem (Element): An SVG <path> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary with keys like 'android:pathData', 'android:fillColor',
              'android:strokeColor', 'android:strokeWidth', or a 'gradient' entry.
    """
    path_data = elem.attrib.get('d', '')
    attributes = {'android:pathData': path_data}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000'))
    return attributes

def convert_polygon_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <polygon> element to Android vector drawable attributes.

    The function converts the list of points into a path data string, then adds
    fill, stroke, and stroke-width properties using the helper function.

    Parameters:
        elem (Element): An SVG <polygon> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary containing attributes such as 'android:pathData',
              'android:fillColor', 'android:strokeColor', and 'android:strokeWidth'.
    """
    points = elem.attrib.get('points', '')
    if not points:
        return {}
    coords = points.replace(',', ' ').split()
    if len(coords) % 2 != 0:
        raise ValueError("Invalid number of coordinates in polygon.")
    pairs = ["{} {}".format(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    d = "M " + pairs[0] + " L " + " L ".join(pairs[1:]) + " Z"
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000'))
    return attributes

def convert_polyline_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <polyline> element to Android vector drawable attributes.

    Similar to polygons but the shape is not closed (no 'Z' command is appended).
    Processes fill, stroke, and stroke-width using the common helper function.

    Parameters:
        elem (Element): An SVG <polyline> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary containing Android vector drawable attributes.
    """
    points = elem.attrib.get('points', '')
    if not points:
        return {}
    coords = points.replace(',', ' ').split()
    if len(coords) % 2 != 0:
        raise ValueError("Invalid number of coordinates in polyline.")
    pairs = ["{} {}".format(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    d = "M " + pairs[0] + " L " + " L ".join(pairs[1:])
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='none'))
    return attributes

def convert_circle_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <circle> element to Android vector drawable attributes.

    Constructs path data for a circle using two arc commands, and adds fill, stroke,
    and stroke-width properties.

    Parameters:
        elem (Element): An SVG <circle> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary containing keys such as 'android:pathData', 'android:fillColor',
              'android:strokeColor', and 'android:strokeWidth'.
    """
    cx = float(elem.attrib.get('cx', '0'))
    cy = float(elem.attrib.get('cy', '0'))
    r = float(elem.attrib.get('r', '0'))
    d = ("M {x} {y}".format(x=cx - r, y=cy) +
         " a {r} {r} 0 1 0 {diam} 0".format(r=r, diam=2*r) +
         " a {r} {r} 0 1 0 -{diam} 0".format(r=r, diam=2*r))
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000'))
    return attributes

def convert_ellipse_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <ellipse> element to Android vector drawable attributes.

    Constructs path data for an ellipse using arc commands. If the fill attribute
    references a gradient (via "url(...)"), a gradient is created as a radial gradient
    using the ellipse's center and x-radius. Stroke attributes are added separately.

    Parameters:
        elem (Element): An SVG <ellipse> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary containing attributes such as 'android:pathData',
              'android:fillColor' (or a 'gradient' entry), 'android:strokeColor',
              and 'android:strokeWidth'.
    """
    cx = float(elem.attrib.get('cx', '0'))
    cy = float(elem.attrib.get('cy', '0'))
    rx = float(elem.attrib.get('rx', '0'))
    ry = float(elem.attrib.get('ry', '0'))
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
        # Special handling for ellipse gradients.
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
    # Extract stroke and stroke-width using the helper.
    attributes.update(extract_stroke_and_width(elem))
    return attributes

def convert_rect_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <rect> element to Android vector drawable attributes.

    Constructs a rectangular path from the x, y, width, and height attributes and adds
    fill, stroke, and stroke-width properties.

    Parameters:
        elem (Element): An SVG <rect> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary containing attributes such as 'android:pathData',
              'android:fillColor', 'android:strokeColor', and 'android:strokeWidth'.
    """
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    width = float(elem.attrib.get('width', '0'))
    height = float(elem.attrib.get('height', '0'))
    d = "M {x} {y} L {x2} {y} L {x2} {y2} L {x} {y2} Z".format(
        x=x, y=y, x2=x+width, y2=y+height
    )
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='#000000'))
    return attributes

def convert_line_element(elem, gradients, vp_width, vp_height):
    """
    Convert an SVG <line> element to Android vector drawable attributes.

    Constructs a path from the line's start and end points and adds fill, stroke,
    and stroke-width properties.

    Parameters:
        elem (Element): An SVG <line> element.
        gradients (dict): A mapping of gradient IDs to SVG gradient elements.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.

    Returns:
        dict: A dictionary containing attributes such as 'android:pathData',
              'android:fillColor', 'android:strokeColor', and 'android:strokeWidth'.
    """
    x1 = float(elem.attrib.get('x1', '0'))
    y1 = float(elem.attrib.get('y1', '0'))
    x2 = float(elem.attrib.get('x2', '0'))
    y2 = float(elem.attrib.get('y2', '0'))
    d = "M {x1} {y1} L {x2} {y2}".format(x1=x1, y1=y1, x2=x2, y2=y2)
    attributes = {'android:pathData': d}
    attributes.update(extract_fill_and_stroke(elem, gradients, vp_width, vp_height, default_fill='none'))
    return attributes