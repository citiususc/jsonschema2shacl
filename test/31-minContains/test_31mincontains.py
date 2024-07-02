import os
from rdflib import compare, Graph
from src.file_parser import parse_json_schema
from src.json_schema_to_shacl import JsonSchemaToShacl


def test_31mincontains():
    expected_graph = Graph()
    expected_graph.parse(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), 'test_shape.ttl'), format="turtle")

    result_graph = Graph()
    json_schema = parse_json_schema(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mapping.json'))
    result_graph = JsonSchemaToShacl().translate(
        json_schema)

    assert compare.isomorphic(expected_graph, result_graph)
