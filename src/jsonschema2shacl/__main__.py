import argparse
import os
from .file_parser import parse_json_schema
from .json_schema_to_shacl import JsonSchemaToShacl


def main():
    """Main function to execute"""
    parser = argparse.ArgumentParser(
        description="Translate JSON Schema to SHACL")
    parser.add_argument("json_file", type=str,
                        help="Path to JSON Schema file")
    args = parser.parse_args()

    file_path = args.json_file
    schema = parse_json_schema(file_path)

    json_converter = JsonSchemaToShacl()

    if schema is not None:
        json_converter.translate(schema)
        # Remove the last component of the path
        base_path = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[
            0]  # Remove the .json extension
        # Construct the new file name with .shape.ttl extension
        file_name = os.path.join(base_path, base_name + "_shape.ttl")
        json_converter.shacl.serialize(format="turtle", destination=file_name)


if __name__ == "__main__":
    main()
