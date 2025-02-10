# SVG2AndroidXml

SVG2AndroidXml is a Python-based command-line tool that converts SVG files into Android Vector Drawable XML files. The tool supports conversion of multiple SVG element types (such as paths, polygons, polylines, circles, ellipses, rectangles, lines, and groups) and also processes linear and radial gradients. It even warns you about elements like text, clip paths, and masks that require more advanced handling.

## Features

- **SVG Element Support**  
  Converts common SVG elements into Android-compatible vector drawable XML:
  - `<path>`
  - `<polygon>`
  - `<polyline>`
  - `<circle>`
  - `<ellipse>`
  - `<rect>`
  - `<line>`
  - `<g>` (group elements with simple transform and style inheritance)


- **Gradient Support**  
  Supports both linear and radial gradients. Gradients are converted into an Android `<gradient>` element nested inside an `<aapt:attr>` element, ensuring that Android Studio’s Vector Asset Studio–compatible XML is generated.

- **Readable Output**  
  Produces well-indented and formatted XML output.

- **Extensible Design**  
  Built in a modular way, allowing you to extend or customize the conversion for more advanced features (e.g., full text-to-path conversion, clip path/mask processing).

## Requirements

- Python 3.6 or higher  
- Uses Python’s built-in libraries (e.g., `xml.etree.ElementTree`, `re`, and standard modules)  

## Installation

Clone the repository:

    git clone https://github.com/yourusername/SVG2Android.git
    cd SVG2AndroidXml

## Usage

Run the converter by specifying a source SVG file or directory and an output directory. For example:

    python main.py -s path/to/svg/folder -o path/to/output/folder

This command will process all SVG files in the source directory and generate corresponding Android Vector Drawable XML files in the output directory.

## Directory Structure

````
SVG2Android/
├── converter/            # Modules for parsing SVG and converting to Android XML.
│   ├── __init__.py
│   ├── converter_core.py
│   ├── shape_converter.py
│   ├── group_converter.py   # (Optional) for group handling.
│   └── xml_builder.py
├── tests/                # Unit tests for the converter.
│   └── soon.py
├── main.py               # Command-line interface entry point.
└── README.md             
````

## Running Tests

To run the test suite, use Python’s unittest framework:

    python -m unittest discover tests

This will execute tests for each SVG element type, making it easier to debug and verify individual functionality.

## Contributing

Contributions are welcome! You can help by:

- Adding support for additional SVG features (e.g., more complex group handling, text-to-path conversion, clip paths, and masks).
- Improving the gradient conversion logic.
- Fixing bugs and enhancing documentation.

Please follow the standard GitHub pull request workflow and include tests for any new features or bug fixes.

## License

This project is licensed under the MIT License.

