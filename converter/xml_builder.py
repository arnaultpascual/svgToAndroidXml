import xml.etree.ElementTree as ETree

ETree.register_namespace("aapt", "http://schemas.android.com/aapt")


def _parse_dimension(dim_str):
    try:
        return float(dim_str.replace("px", ""))
    except Exception:
        return 24.0


def build_vector_drawable(svg_attrib, elements, vp_width, vp_height):
    raw_width = svg_attrib.get('width', str(vp_width))
    raw_height = svg_attrib.get('height', str(vp_height))
    width_val = _parse_dimension(raw_width)
    height_val = _parse_dimension(raw_height)

    final_width = f"{int(width_val)}dp"
    final_height = f"{int(height_val)}dp"

    viewBox = svg_attrib.get('viewBox')
    if viewBox:
        parts = viewBox.split()
        if len(parts) == 4:
            viewportWidth = str(int(float(parts[2])))
            viewportHeight = str(int(float(parts[3])))
        else:
            viewportWidth = str(int(vp_width))
            viewportHeight = str(int(vp_height))
    else:
        viewportWidth = str(int(vp_width))
        viewportHeight = str(int(vp_height))

    vector = ETree.Element('vector', {
        'xmlns:android': 'http://schemas.android.com/apk/res/android',
        'android:width': final_width,
        'android:height': final_height,
        'android:viewportWidth': viewportWidth,
        'android:viewportHeight': viewportHeight,
    })

    for elem_dict in elements:
        _build_element(elem_dict, vector)

    return vector


def _build_element(elem_dict, parent):
    # If this is a group element, create a <group> element.
    if elem_dict.get('group'):
        group_elem = ETree.SubElement(parent, 'group', elem_dict.get('attributes', {}))
        for child in elem_dict.get('children', []):
            _build_element(child, group_elem)
    else:
        path_elem = ETree.SubElement(parent, 'path')
        for key, value in elem_dict.items():
            if key not in ['gradient', 'group', 'children', 'style']:
                if value:
                    path_elem.set(key, value)
        if 'gradient' in elem_dict:
            aapt_attr = ETree.SubElement(path_elem, '{http://schemas.android.com/aapt}attr', {'name': 'android:fillColor'})
            grad_struct = elem_dict['gradient']
            grad_elem = ETree.SubElement(aapt_attr, grad_struct.get('tag', 'gradient'))
            for k, v in grad_struct.get('attributes', {}).items():
                if v:
                    grad_elem.set(k, v)
            for item in grad_struct.get('items', []):
                item_elem = ETree.SubElement(grad_elem, 'item')
                for k, v in item.items():
                    if v:
                        item_elem.set(k, v)


def write_vector_drawable(xml_elem, output_file):
    tree = ETree.ElementTree(xml_elem)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)