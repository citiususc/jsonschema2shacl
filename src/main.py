import argparse
from file_parser import leer_json_schema
from rdflib import Graph, Namespace, RDF

# Define namespaces
EX = Namespace("http://example.org/")
SHAPES = Namespace("http://www.w3.org/ns/shacl#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")


def detect_json_type(data):
    """
    Detects if the JSON data is of simple type (number, strings, booleans, integer)
    or complex type (object or array).
    """
    if isinstance(data, (int, float, str, bool)):
        return "simple"
    elif isinstance(data, dict):
        return "object"
    elif isinstance(data, list):
        return "array"
    else:
        return None


def translate_simple_to_shacl(g, property_name, property_type):
    """
    Translates a simple JSON property into its SHACL equivalent.
    """
    g.add((EX[property_name], RDF.type, SHAPES.PropertyShape))
    g.add((EX[property_name], SHAPES.path, EX[property_name]))
    g.add((EX[property_name], SHAPES.datatype, XSD[property_type]))


def translate_complex_to_shacl(g, property_name, property_data):
    """
    Translates a complex JSON complex (obj or array) property into its SHACL equivalent.
    """
    if isinstance(property_data, dict):  # Object
        node_shape = EX[property_name]
        g.add((node_shape, RDF.type, SHAPES.NodeShape))
        for key, value in property_data.items():
            translate_property_to_shacl(g, key, value, parent_shape=node_shape)
    elif isinstance(property_data, list):  # Array
        g.add((EX[property_name], RDF.type, SHAPES.PropertyShape))
        g.add((EX[property_name], SHAPES.path, EX[property_name]))
        g.add((EX[property_name], SHAPES.minCount, "1"))
        g.add((EX[property_name], SHAPES.maxCount, "-1"))
        g.add((EX[property_name], SHAPES.nodeKind, SHAPES.IRIOrLiteral))
        g.add((EX[property_name], SHAPES.datatype, XSD["string"]))


def translate_property_to_shacl(g, property_name, property_data, parent_shape=None):
    """
    Translates a JSON property into its SHACL equivalent.
    """
    property_type = detect_json_type(property_data)

    if property_type == "object" or property_type == "array":
        translate_complex_to_shacl(g, property_name, property_data)
    else:
        translate_simple_to_shacl(g, property_name, property_data)


def json_schema_to_shacl(json_schema):
    """
    Translates a JSON schema into its SHACL equivalent.
    """
    g = Graph()
    for property_name, property_data in json_schema["properties"].items():
        translate_property_to_shacl(g, property_name, property_data)

    return g.serialize(format="turtle")


def main():
    """

    """
    parser = argparse.ArgumentParser(
        description="Convertir JSON Schema a SHACL")
    parser.add_argument("archivo_json", type=str,
                        help="Ruta al archivo JSON Schema")
    args = parser.parse_args()

    ruta_archivo = args.archivo_json
    schema = leer_json_schema(ruta_archivo)

    if schema is not None:
        shacl_representation = json_schema_to_shacl(schema)
        print(shacl_representation)


if __name__ == "__main__":
    main()
