import xml.etree.ElementTree as ET

def parse_svg(svg_file):
    """
    Parse the SVG file and return the root element and a namespace dict.
    """
    tree = ET.parse(svg_file)
    root = tree.getroot()
    ns = {}
    # If there is a namespace in the root tag, extract it.
    if '}' in root.tag:
        uri = root.tag.split('}')[0].strip('{')
        ns['svg'] = uri
    return root, ns