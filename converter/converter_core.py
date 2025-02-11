import os
import argparse
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
from converter.group_converter import convert_group_element  # For group handling
from converter.xml_builder import build_vector_drawable, write_vector_drawable


def get_viewport_dimensions(svg_attrib):
    """
    Determine the viewport dimensions (width and height) from the SVG attributes.

    If the SVG has a 'viewBox' attribute, this function uses its 3rd and 4th values.
    Otherwise, it falls back to the 'width' and 'height' attributes (removing any "px").
    If all attempts fail, default dimensions (24.0, 24.0) are returned.

    Parameters:
      svg_attrib (dict): The attribute dictionary from the SVG root element.

    Returns:
      tuple: (viewport_width, viewport_height) as floats.
    """
    viewBox = svg_attrib.get('viewBox')
    if viewBox:
        parts = viewBox.split()
        if len(parts) == 4:
            try:
                return float(parts[2]), float(parts[3])
            except Exception:
                pass  # If conversion fails, try alternative method
    try:
        vp_width = float(svg_attrib.get('width', '24').replace('px', ''))
        vp_height = float(svg_attrib.get('height', '24').replace('px', ''))
        return vp_width, vp_height
    except Exception:
        return 24.0, 24.0


def extract_gradients(root, ns, vp_width, vp_height):
    """
    Extract all gradient definitions (linear and radial) from the SVG.

    This function searches within the SVG root for <linearGradient> and <radialGradient>
    elements (using the provided namespace) and builds a dictionary mapping each gradient's
    id (normalized to lowercase) to its element.

    Parameters:
      root (Element): The root element of the SVG.
      ns (dict): A dictionary of namespaces.
      vp_width (float): Viewport width (used for percentage conversion if needed).
      vp_height (float): Viewport height.

    Returns:
      dict: A dictionary mapping gradient IDs (lowercase) to their corresponding elements.
    """
    gradients = {}
    ns_uri = ns.get('svg', 'http://www.w3.org/2000/svg')
    # Extract linear gradients
    for grad in root.findall('.//{{{}}}linearGradient'.format(ns_uri)):
        grad_id = grad.attrib.get('id')
        if grad_id:
            gradients[grad_id.lower()] = grad
    # Extract radial gradients
    for grad in root.findall('.//{{{}}}radialGradient'.format(ns_uri)):
        grad_id = grad.attrib.get('id')
        if grad_id:
            gradients[grad_id.lower()] = grad
    return gradients


def convert_svg_to_vector_drawable(svg_file, output_file):
    """
    Convert an SVG file into an Android Vector Drawable XML file.

    This function:
      - Parses the input SVG.
      - Determines viewport dimensions.
      - Extracts gradient definitions.
      - Iterates over the SVG's direct child elements and converts each supported element
        (including group elements) to an intermediate dictionary format.
      - Builds the final vector drawable XML using the intermediate format.
      - Writes the XML to the output file.

    Parameters:
      svg_file (str): Path to the input SVG file.
      output_file (str): Path to the output XML file.
    """
    # Parse the SVG file and obtain the root and namespace dictionary.
    root, ns = parse_svg(svg_file)
    svg_attrib = root.attrib
    # Get viewport dimensions from viewBox or width/height.
    vp_width, vp_height = get_viewport_dimensions(svg_attrib)
    # Extract gradient definitions from the SVG.
    gradients = extract_gradients(root, ns, vp_width, vp_height)
    elements = []
    # Iterate only over the direct children of the SVG root.
    for elem in root:
        # Get the local tag name (ignoring the namespace).
        tag = elem.tag.split('}')[-1].lower()
        if tag == 'g':
            # For group elements, use convert_group_element and extend the list with its children.
            # The additional parameter (1, 0, 0, 1, 0, 0) is the identity matrix for transforms.
            group_children = convert_group_element(elem, gradients, vp_width, vp_height, (1, 0, 0, 1, 0, 0))
            elements.extend(group_children)
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
        elif tag == 'image':
            print(
                f"Attention : l'élément <image> dans {svg_file} est ignoré (non supporté dans les Vector Drawables Android).")
        elif tag in ['text', 'clippath', 'mask']:
            print(f"Warning : l'élément <{tag}> dans {svg_file} n'est pas entièrement supporté.")
        else:
            # Ignore other tags (such as <defs>).
            pass

    # Build the Android vector drawable XML structure from the intermediate elements.
    vector = build_vector_drawable(svg_attrib, elements, vp_width, vp_height)
    # Write the XML to the output file.
    write_vector_drawable(vector, output_file)


if __name__ == '__main__':
    # Create an argument parser for the command-line interface.
    parser = argparse.ArgumentParser(
        description='Convertir des fichiers SVG en fichiers XML Vector Drawable Android'
    )
    # Add required arguments: source directory/file and output directory/file.
    parser.add_argument('-s', '--src', required=True,
                        help='Dossier source contenant les fichiers SVG')
    parser.add_argument('-o', '--out', required=True,
                        help='Dossier de sortie pour les fichiers XML générés')
    args = parser.parse_args()
    # Convert the SVG(s) to Vector Drawable XML.
    convert_svg_to_vector_drawable(args.src, args.out)