import os
import argparse
from converter.converter_core import convert_svg_to_vector_drawable

def batch_convert(src_dir, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for filename in os.listdir(src_dir):
        if filename.lower().endswith('.svg'):
            input_path = os.path.join(src_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.xml'
            output_path = os.path.join(out_dir, output_filename)
            print(f"Converting {input_path} -> {output_path}")
            try:
                convert_svg_to_vector_drawable(input_path, output_path)
                print("Conversion successful.")
            except Exception as e:
                print(f"Error converting {filename}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert SVG files to Android Vector Drawable XML files'
    )
    parser.add_argument('-s', '--src', required=True,
                        help='Source directory containing SVG files')
    parser.add_argument('-o', '--out', required=True,
                        help='Output directory for generated XML files')
    args = parser.parse_args()
    batch_convert(args.src, args.out)