import re
from converter.shape_converter import (
    parse_style,
    convert_path_element,
    convert_polygon_element,
    convert_polyline_element,
    convert_circle_element,
    convert_ellipse_element,
    convert_rect_element,
    convert_line_element,
    parse_transform_attr,
    multiply_matrices
)


def merge_styles(parent_style, child_style):
    """
    Merge two style dictionaries with child_style taking precedence over parent_style.

    Parameters:
        parent_style (dict): The style dictionary inherited from a parent element.
        child_style (dict): The style dictionary defined on the current element.

    Returns:
        dict: A new dictionary containing merged styles.
    """
    # If parent_style exists, copy it; otherwise, start with an empty dictionary.
    merged = parent_style.copy() if parent_style else {}
    # Update with child's style values (child overrides parent)
    if child_style:
        merged.update(child_style)
    return merged


def convert_group_element(elem, gradients, vp_width, vp_height,
                          inherited_transform=(1, 0, 0, 1, 0, 0),
                          inherited_style=None, warnings=None):
    """
    Convert an SVG <g> (group) element into a list of flattened child elements.

    This function processes the group's transformation and style, merges them with
    any inherited values, and then recursively converts all child elements. It effectively
    "flattens" groups so that the individual elements inherit the group's transform and style.

    Parameters:
        elem (Element): The SVG group (<g>) element.
        gradients (dict): A dictionary of gradient definitions.
        vp_width (float): The viewport width.
        vp_height (float): The viewport height.
        inherited_transform (tuple): The transformation matrix inherited from parent elements,
                                      in the form (a, b, c, d, e, f). Default is identity.
        inherited_style (dict): A dictionary of inherited style properties. Default is None.
        warnings (list): An optional list to which warning messages can be appended.

    Returns:
        list: A list of converted child elements (each represented as a dictionary) from the group.
    """
    # Retrieve the group's style from the "style" attribute (if present)
    group_style = {}
    if 'style' in elem.attrib:
        group_style = parse_style(elem.attrib.get('style', ''))
    # If the group directly defines a fill attribute (but not in the style), add it to the style.
    if 'fill' not in group_style and 'fill' in elem.attrib:
        group_style['fill'] = elem.attrib['fill']
    # Merge the inherited style with the group's own style (child values override parent values).
    merged_style = merge_styles(inherited_style, group_style)

    # Process the group's transformation.
    transform_str = elem.attrib.get('transform', '')
    current_transform = inherited_transform
    if transform_str:
        # Parse the group's transform attribute into a transformation matrix.
        group_transform = parse_transform_attr(transform_str)
        # Multiply the inherited transformation matrix with the group's matrix.
        current_transform = multiply_matrices(inherited_transform, group_transform)

    # Initialize a list to hold converted child elements.
    children = []
    # Iterate over the group's child elements.
    for child in list(elem):
        # Get the local tag name (ignoring namespace) and convert it to lowercase.
        tag = child.tag.split('}')[-1].lower()
        if tag == 'g':
            # Recursively process nested groups.
            children.extend(
                convert_group_element(child, gradients, vp_width, vp_height,
                                      current_transform, merged_style, warnings=warnings)
            )
        elif tag == 'path':
            conv = convert_path_element(child, gradients, vp_width, vp_height,
                                        current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'polygon':
            conv = convert_polygon_element(child, gradients, vp_width, vp_height,
                                           current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'polyline':
            conv = convert_polyline_element(child, gradients, vp_width, vp_height,
                                            current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'circle':
            conv = convert_circle_element(child, gradients, vp_width, vp_height,
                                          current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'ellipse':
            conv = convert_ellipse_element(child, gradients, vp_width, vp_height,
                                           current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'rect':
            conv = convert_rect_element(child, gradients, vp_width, vp_height,
                                        current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'line':
            conv = convert_line_element(child, gradients, vp_width, vp_height,
                                        current_transform, inherited_style=merged_style)
            if conv:
                children.append(conv)
        elif tag == 'image':
            # Issue a warning for unsupported elements.
            if warnings is not None:
                warnings.append(f"Attention : l'élément <image> (id={child.attrib.get('id', 'inconnu')}) est ignoré.")
        elif tag in ['text', 'clippath', 'mask']:
            # Issue a warning for partially supported elements.
            if warnings is not None:
                warnings.append(f"Warning : l'élément <{tag}> n'est pas entièrement supporté.")
        else:
            # For any other unsupported element within a group, issue a warning.
            if warnings is not None:
                warnings.append(f"Warning : élément <{tag}> non supporté dans un groupe.")
    # Return the list of converted (flattened) child elements.
    return children