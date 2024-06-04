import argparse
from rdflib import Graph, Namespace, Literal, URIRef
from jsonpath_ng import jsonpath, parse
# from pyshacl import validate
from file_parser import parse_json_schema
from constants import build_in_types, format_types
from utils import check_type, check_if_object_has_properties_or_restrictions


class JsonSchemaToShacl:
    """
    Class to convert JSON Schema to SHACL
    """

    def __init__(self):
        """
        Initialize the JSONSCHEMAtoSHACL class
        """
        self.shacl_ns = Namespace('http://www.w3.org/ns/shacl#')
        self.rdf_syntax = Namespace(
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.xsd_ns = Namespace('http://www.w3.org/2001/XMLSchema#')
        self.xsd_target_ns = Namespace('http://example.com/')
        self.ns = Namespace('http://example.com/')
        # self.type_list = built_in_types()
        self.shacl = Graph()
        self.shapes = []
        self.schema = None

    def trans_element_simple(self, entry_name: str, entry: dict, pre_subject: URIRef) -> URIRef:
        """A function to translate elements of SimpleType inside a ComplexType"""
        subject = self.ns[f'PropertyShape/{entry_name}']

        self.shacl.add((pre_subject, self.shacl_ns.property, subject))
        self.shapes.append(subject)
        self.shacl.add(
            (subject, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))
        self.shacl.add((subject, self.shacl_ns.path,
                        self.xsd_target_ns[entry_name]))

        self.trans_simple_restrictions(entry, subject)

        return subject

    def trans_element_complex(self, entry_name: str, entry: dict, pre_subject: URIRef) -> URIRef:
        """A function to translate elements of ComplexType inside a ComplexType"""

        subject = self.ns[f'NodeShape/{entry_name}']
        subject_property = self.ns[f'PropertyShape/{entry_name}']

        self.shacl.add((pre_subject, self.shacl_ns.property, subject_property))
        self.shacl.add(
            (subject_property, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject_property, self.shacl_ns.path,
                        self.xsd_target_ns[entry_name]))
        self.shapes.append(subject_property)
        if check_if_object_has_properties_or_restrictions(entry) is True:
            self.shacl.add((subject_property, self.shacl_ns.node, subject))
            self.shapes.append(subject)
            self.shacl.add(
                (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
            self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))

            self.trans_simple_restrictions(entry, subject)

            if entry.get('properties') is not None:
                for name, details in entry.get('properties', {}).items():
                    if check_type(details) == "SimpleType":
                        self.trans_element_simple(name, details, subject)
                    elif check_type(details) == "ComplexType":
                        self.trans_element_complex(name, details, subject)
                    elif check_type(details) == "ArrayType":
                        self.trans_element_array(name, details, subject)

            self.trans_complex_restrictions(entry, subject)
        else:
            self.trans_simple_restrictions(entry, subject_property)

        return subject_property

    def trans_element_complex_contains(self, entry_name: str, entry: dict, pre_subject: URIRef) -> URIRef:
        """A function to translate elements of ComplexType inside a ComplexType"""

        subject = self.ns[f'NodeShape/{entry_name}']
        subject_property = self.ns[f'PropertyShape/{entry_name}']

        self.shacl.add((pre_subject, self.shacl_ns.property, subject_property))
        self.shacl.add(
            (subject_property, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject_property, self.shacl_ns.path,
                        self.xsd_target_ns[entry_name]))
        self.shapes.append(subject_property)
        if check_if_object_has_properties_or_restrictions(entry) is True:
            self.shacl.add(
                (subject_property, self.shacl_ns.qualifiedValueShape, subject))
            self.shapes.append(subject)
            self.shacl.add(
                (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
            self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))

            self.trans_simple_restrictions(entry, subject)

            if entry.get('properties') is not None:
                for name, details in entry.get('properties', {}).items():
                    if check_type(details) == "SimpleType":
                        self.trans_element_simple(name, details, subject)
                    elif check_type(details) == "ComplexType":
                        self.trans_element_complex(name, details, subject)
                    elif check_type(details) == "ArrayType":
                        self.trans_element_array(name, details, subject)

            self.trans_complex_restrictions(entry, subject)
        else:
            self.trans_simple_restrictions(entry, subject_property)

        return subject_property

    def trans_element_complex_array(self, entry_name: str, entry: dict, pre_subject: URIRef) -> None:
        """A function to translate a ComplexType object inside an Array"""

        if check_if_object_has_properties_or_restrictions(entry) is True:
            subject = self.ns[f'NodeShape/{entry_name}']
            self.shacl.add((pre_subject, self.shacl_ns.node, subject))
            self.shapes.append(subject)
            self.shacl.add(
                (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
            self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))

            self.trans_simple_restrictions(entry, subject)

            if entry.get('properties') is not None:
                for name, details in entry.get('properties', {}).items():
                    if check_type(details) == "SimpleType":
                        self.trans_element_simple(name, details, subject)
                    elif check_type(details) == "ComplexType":
                        self.trans_element_complex(name, details, subject)
                    elif check_type(details) == "ArrayType":
                        self.trans_element_array(name, details, subject)

            self.trans_complex_restrictions(entry, subject)
        else:
            self.trans_simple_restrictions(entry, pre_subject)

    def trans_element_complex_array_contains(self, entry_name: str, entry: dict, pre_subject: URIRef) -> URIRef:
        """A function to translate elements of ComplexType inside an Array with Contains"""

        subject = self.ns[f'NodeShape/{entry_name}']
        subject_property = self.ns[f'PropertyShape/{entry_name}']

        self.shacl.add((pre_subject, self.shacl_ns.property, subject_property))
        self.shacl.add(
            (subject_property, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject_property, self.shacl_ns.path,
                        self.xsd_target_ns[entry_name]))
        self.shapes.append(subject_property)
        if check_if_object_has_properties_or_restrictions(entry) is True:
            self.shacl.add(
                (subject_property, self.shacl_ns.qualifiedValueShape, subject))
            self.shapes.append(subject)
            self.shacl.add(
                (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
            self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))

            self.trans_simple_restrictions(entry, subject)

            if entry.get('properties') is not None:
                for name, details in entry.get('properties', {}).items():
                    if check_type(details) == "SimpleType":
                        self.trans_element_simple(name, details, subject)
                    elif check_type(details) == "ComplexType":
                        self.trans_element_complex(name, details, subject)
                    elif check_type(details) == "ArrayType":
                        self.trans_element_array(name, details, subject)

            self.trans_complex_restrictions(entry, subject)
        else:
            self.trans_simple_restrictions(entry, subject_property)

        return subject_property

    def trans_element_array(self, entry_name: str, entry: dict, pre_subject: URIRef) -> None:
        """A function to translate arrays inside a ComplexType"""

        subject_property = self.ns[f'PropertyShape/{entry_name}']
        subject = self.ns[f'NodeShape/{entry_name}']

        self.shacl.add((pre_subject, self.shacl_ns.property, subject_property))
        self.shacl.add(
            (subject_property, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject_property, self.shacl_ns.path,
                        self.xsd_target_ns[entry_name]))
        self.shapes.append(subject_property)
        if entry.get('prefixItems') is not None or check_type(entry.get('items')) != "SimpleType":
            self.shacl.add((subject_property, self.shacl_ns.node, subject))
            self.shapes.append(subject)
            self.shacl.add(
                (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
            self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))

        if entry.get('prefixItems') is None:
            item = entry.get('items')
            contains = entry.get('contains')

            if contains is not None and item is not None:
                number_of_items = 0
                item = entry.get('items')
                if item is not None:
                    if item == "true" or item == "false":
                        self.shacl.add(
                            (subject, self.shacl_ns.closed, Literal(item)))
                    else:
                        if check_type(item) == "SimpleType":
                            self.trans_element_simple(
                                f"{entry_name}P{number_of_items}", item, subject)
                        elif check_type(item) == "ComplexType":
                            self.trans_element_complex(
                                f"{entry_name}P{number_of_items}", item, subject)
                        number_of_items += 1

                contains = entry.get('contains')
                if contains is not None:
                    if check_type(contains) == "SimpleType":
                        new_contains_shape = self.trans_element_simple(
                            f"{entry_name}P{number_of_items}", contains, subject)
                        if entry.get('minContains'):
                            p = self.shacl_ns.minCount
                            o = Literal(entry.get('minContains'))
                            self.shacl.add((new_contains_shape, p, o))
                        if entry.get('maxContains'):
                            p = self.shacl_ns.maxCount
                            o = Literal(entry.get('maxContains'))
                            self.shacl.add((new_contains_shape, p, o))
                    elif check_type(contains) == "ComplexType":
                        new_contains_shape = self.trans_element_complex_contains(
                            f"{entry_name}P{number_of_items}", contains, subject)
                        if entry.get('minContains'):
                            p = self.shacl_ns.qualifiedMinCount
                            o = Literal(entry.get('minContains'))
                            self.shacl.add((new_contains_shape, p, o))
                        if entry.get('maxContains'):
                            p = self.shacl_ns.qualifiedMaxCount
                            o = Literal(entry.get('maxContains'))
                            self.shacl.add((new_contains_shape, p, o))
                    number_of_items += 1

            if item is not None:
                if item == "true" or item == "false":
                    self.shacl.add(
                        (subject, self.shacl_ns.closed, Literal(item)))
                else:
                    if check_type(item) == "SimpleType":
                        self.shacl.add(
                            (subject_property, self.shacl_ns.name, Literal(entry_name)))
                        self.trans_simple_restrictions(item, subject_property)
                    elif check_type(item) == "ComplexType":
                        self.trans_element_complex_array(
                            f"{entry_name}", item, subject_property)

            if contains is not None:
                if check_type(contains) == "SimpleType":
                    self.shacl.add(
                        (subject_property, self.shacl_ns.name, Literal(entry_name)))
                    self.trans_simple_restrictions(item, subject_property)
                    if entry.get('minContains'):
                        p = self.shacl_ns.minCount
                        o = Literal(entry.get('minContains'))
                        self.shacl.add((subject_property, p, o))
                    if entry.get('maxContains'):
                        p = self.shacl_ns.maxCount
                        o = Literal(entry.get('maxContains'))
                        self.shacl.add((subject_property, p, o))
                elif check_type(contains) == "ComplexType":
                    new_contains_shape = self.trans_element_complex_array_contains(
                        f"{entry_name}P{number_of_items}", contains, subject)
                    if entry.get('minContains'):
                        p = self.shacl_ns.qualifiedMinCount
                        o = Literal(entry.get('minContains'))
                        self.shacl.add((new_contains_shape, p, o))
                    if entry.get('maxContains'):
                        p = self.shacl_ns.qualifiedMaxCount
                        o = Literal(entry.get('maxContains'))
                        self.shacl.add((new_contains_shape, p, o))
                number_of_items += 1

        else:
            number_of_items = 0

            if entry.get('prefixItems') is not None:
                for prefix_item in entry.get('prefixItems'):
                    if check_type(prefix_item) == "SimpleType":
                        self.trans_element_simple(
                            f"{entry_name}P{number_of_items}", prefix_item, subject)
                    elif check_type(prefix_item) == "ComplexType":
                        self.trans_element_complex(
                            f"{entry_name}P{number_of_items}", prefix_item, subject)
                    number_of_items += 1

            item = entry.get('items')
            if item is not None:
                if item == "true" or item == "false":
                    self.shacl.add(
                        (subject, self.shacl_ns.closed, Literal(item)))
                else:
                    if check_type(item) == "SimpleType":
                        self.trans_element_simple(
                            f"{entry_name}P{number_of_items}", item, subject)
                    elif check_type(item) == "ComplexType":
                        self.trans_element_complex(
                            f"{entry_name}P{number_of_items}", item, subject)
                    number_of_items += 1

            contains = entry.get('contains')
            if contains is not None:
                if check_type(contains) == "SimpleType":
                    new_contains_shape = self.trans_element_simple(
                        f"{entry_name}P{number_of_items}", contains, subject)
                    if entry.get('minContains'):
                        p = self.shacl_ns.minCount
                        o = Literal(entry.get('minContains'))
                        self.shacl.add((new_contains_shape, p, o))
                    if entry.get('maxContains'):
                        p = self.shacl_ns.maxCount
                        o = Literal(entry.get('maxContains'))
                        self.shacl.add((new_contains_shape, p, o))
                elif check_type(contains) == "ComplexType":
                    new_contains_shape = self.trans_element_complex_contains(
                        f"{entry_name}P{number_of_items}", contains, subject)
                    if entry.get('minContains'):
                        p = self.shacl_ns.qualifiedMinCount
                        o = Literal(entry.get('minContains'))
                        self.shacl.add((new_contains_shape, p, o))
                    if entry.get('maxContains'):
                        p = self.shacl_ns.qualifiedMaxCount
                        o = Literal(entry.get('maxContains'))
                        self.shacl.add((new_contains_shape, p, o))
                number_of_items += 1

        self.trans_array_restrictions(entry, subject)

    # def trans_element_ref(self, name: str, ref_dict: dict, subject) -> None:
    #     ref_path = ref_dict["$ref"]
    #     if ref_path.startswith("#"):
    #         ref_path = ref_path.replace("#", "$.").split("./")[1]
    #         jsonpath_expr_str = '$.'
    #         for name in ref_path.split("/"):
    #             jsonpath_expr_str += f'["{name}"]'

    #     jsonpath_expr = parse(jsonpath_expr_str)

    #     ref_element = [
    #         match.value for match in jsonpath_expr.find(self.schema)][0]

    #     print(ref_element)
    #     # # Check the type of the referenced element
    #     # ref_type = check_type(ref_element)

    #     # # Depending on the type, call the appropriate translation function
    #     # if ref_type == "SimpleType":
    #     #     self.trans_element_simple(name, ref_element, subject)
    #     # elif ref_type == "ComplexType":
    #     #     self.trans_element_complex(name, ref_element, subject)
    #     # elif ref_type == "ArrayType":
    #     #     self.trans_element_array(name, ref_element, subject)

    def trans_simple_restrictions(self, element: dict, subject: URIRef) -> None:
        """A function to translate restrictions of SimpleType elements"""
        if element.get('const'):
            p = self.shacl_ns.hasValue
            o = Literal(element.get('const'))
            self.shacl.add((subject, p, o))
        elif element.get('enum'):
            for enum_literal in element.get('enum'):
                p = self.shacl_ns.in_
                o = Literal(enum_literal)
                self.shacl.add((subject, p, o))
        elif element.get('type'):
            json_type = element.get('type')
            xsd_type = build_in_types(json_type)
            if xsd_type:
                if xsd_type == "string":
                    if element.get('format'):
                        format_type = format_types(element.get('format'))
                        if format_type:
                            p = self.shacl_ns.datatype
                            o = self.xsd_ns[format_type]
                            self.shacl.add((subject, p, o))
                    else:
                        p = self.shacl_ns.datatype
                        o = self.xsd_ns[xsd_type]
                        self.shacl.add((subject, p, o))
                p = self.shacl_ns.datatype
                o = self.xsd_ns[xsd_type]
                self.shacl.add((subject, p, o))

        if element.get('minimum'):
            p = self.shacl_ns.minInclusive
            o = Literal(element.get('minimum'))
            self.shacl.add((subject, p, o))
        if element.get('exclusiveMinimum'):
            p = self.shacl_ns.minExclusive
            o = Literal(element.get('exclusiveMinimum'))
            self.shacl.add((subject, p, o))
        if element.get('maximum'):
            p = self.shacl_ns.minExclusive
            o = Literal(element.get('maximum'))
            self.shacl.add((subject, p, o))
        if element.get('exclusiveMaximum'):
            p = self.shacl_ns.maxExclusive
            o = Literal(element.get('exclusiveMaximum'))
            self.shacl.add((subject, p, o))
        if element.get('minLength'):
            p = self.shacl_ns.minLength
            o = Literal(element.get('minLength'))
            self.shacl.add((subject, p, o))
        if element.get('maxLength'):
            p = self.shacl_ns.maxLength
            o = Literal(element.get('maxLength'))
            self.shacl.add((subject, p, o))
        if element.get('pattern'):
            p = self.shacl_ns.pattern
            o = Literal(element.get('pattern'))
            self.shacl.add((subject, p, o))

    def trans_complex_restrictions(self, element: dict, subject: URIRef) -> None:
        if element.get('additionalProperties'):
            p = self.shacl_ns.closed
            o = Literal(not element.get('additionalProperties'))
            self.shacl.add((subject, p, o))
        if element.get('required'):
            required_elements = element.get('required')
            for required_element in required_elements:
                subject_property = ""
                for shapes in self.shapes:
                    if required_element in str(shapes):
                        if "NodeShape" in str(shapes):
                            subject_property_path = shapes.split(
                                "NodeShape/")[1]
                            subject_property = self.ns[f'NodeShape/{subject_property_path}']
                        elif "PropertyShape" in str(shapes):
                            subject_property_path = shapes.split(
                                "PropertyShape/")[1]
                            subject_property = self.ns[f'PropertyShape/{subject_property_path}']
                if subject_property != "":
                    p = self.shacl_ns.minCount
                    o = Literal(1)
                    self.shacl.add((subject_property, p, o))
                    p = self.shacl_ns.maxCount
                    o = Literal(1)
                    self.shacl.add((subject_property, p, o))
        if element.get('unevaluatedProperties'):
            p = self.shacl_ns.closed
            o = Literal(not element.get('unevaluatedProperties'))
            self.shacl.add((subject, p, o))
        if element.get('patternProperties'):
            pattern_properties_list = element.get('patternProperties')
            for pattern_property in pattern_properties_list:
                self.trans_element_simple(
                    pattern_property, pattern_properties_list.get(pattern_property), subject)
                p = self.shacl_ns.pattern
                o = Literal(pattern_property)
                self.shacl.add((subject, p, o))
        if element.get('propertyNames'):
            self.trans_element_simple(
                f"{subject.split('/')[-1]}PropertyNames", element.get('propertyNames'), subject)
        if element.get('dependentRequired'):
            self.shacl.add(
                (subject, self.shacl_ns.qualifiedMinCount, Literal(1)))

            for dependent_key, dependent_list in element.get('dependentRequired').items():
                subject_dependant_key = ""
                for shapes in self.shapes:
                    if dependent_key in str(shapes):
                        if "NodeShape" in str(shapes):
                            subject_dependant_key_path = shapes.split(
                                "NodeShape/")[1]
                            subject_dependant_key = self.ns[f'NodeShape/{subject_dependant_key_path}']
                        elif "PropertyShape" in str(shapes):
                            subject_dependant_key_path = shapes.split(
                                "PropertyShape/")[1]
                            subject_dependant_key = self.ns[f'PropertyShape/{subject_dependant_key_path}']
                if subject_dependant_key != "":
                    for dependent in dependent_list:
                        subject_dependant_path = ""
                        for shapes in self.shapes:
                            if dependent in str(shapes):
                                if "NodeShape" in str(shapes):
                                    subject_dependant_path = shapes.split(
                                        "NodeShape/")[1]
                                elif "PropertyShape" in str(shapes):
                                    subject_dependant_path = shapes.split(
                                        "PropertyShape/")[1]
                        if subject_dependant_path != "":
                            p = self.shacl_ns.qualifiedValueShape
                            dependent_object = self.ns[f'NodeShape/{dependent}QualifiedValueShape']
                            self.shacl.add(
                                (subject_dependant_key, p, dependent_object))
                            self.shapes.append(dependent_object)
                            self.shacl.add(
                                (dependent_object, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
                            self.shacl.add(
                                (dependent_object, self.shacl_ns.path, self.xsd_target_ns[subject_dependant_path]))

    def trans_array_restrictions(self, element: dict, subject: URIRef) -> None:
        if element.get('minItems'):
            p = self.shacl_ns.minInclusive
            o = Literal(element.get('minItems'))
            self.shacl.add((subject, p, o))
        if element.get('maxItems'):
            p = self.shacl_ns.maxInclusive
            o = Literal(element.get('maxItems'))
            self.shacl.add((subject, p, o))
        if element.get('uniqueItems'):
            p = self.shacl_ns.uniqueLang
            o = Literal(element.get('uniqueItems'))
            self.shacl.add((subject, p, o))
        if element.get('unevaluatedItems'):
            p = self.shacl_ns.closed
            o = Literal(not element.get('unevaluatedItems'))
            self.shacl.add((subject, p, o))

    def trans_complex(self, element: dict) -> None:
        """A function to translate ComplexType elements"""
        element_name = element.get("name")
        subject = self.ns[f'NodeShape/{element_name}']

        if self.shapes:
            pre_subject_path = ""
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]
            subject = self.ns[f'NodeShape/{pre_subject_path}/{element_name}']

        self.shapes.append(subject)
        self.shacl.add(
            (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
        self.shacl.add((subject, self.shacl_ns.name, Literal(element_name)))

        self.shacl.add((subject, self.shacl_ns.targetClass,
                        self.xsd_target_ns[element_name]))

        for name, details in element.get('properties', {}).items():
            if check_type(details) == "SimpleType":
                self.trans_element_simple(name, details, subject)
            elif check_type(details) == "ComplexType":
                self.trans_element_complex(name, details, subject)
            elif check_type(details) == "ArrayType":
                self.trans_element_array(name, details, subject)
            # elif check_type(details) == "RefType":
            #     self.trans_element_ref(name, details, subject)

        self.trans_simple_restrictions(element, subject)
        self.trans_complex_restrictions(element, subject)

    def translate(self, element: dict) -> None:
        """Function to translate JSON Schema to SHACL"""
        if check_type(element) == "ComplexType":
            self.trans_complex(element)
            self.schema = element


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
        file_name = f"{file_path}.shape.ttl"
        json_converter.shacl.serialize(format="turtle", destination=file_name)


if __name__ == "__main__":
    main()
