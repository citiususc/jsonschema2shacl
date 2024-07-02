from rdflib import Graph, Namespace, Literal, URIRef, BNode
from jsonpath_ng import parse
# from pyshacl import validate
from .constants import build_in_types, format_types
from .utils import check_type, check_if_object_has_properties_or_restrictions


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

        if self.shapes:
            for shape in self.shapes:
                if entry_name in str(shape):
                    self.shacl.add(
                        (pre_subject, self.shacl_ns.property, shape))
                    return shape

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
                    type_details = check_type(details)
                    if type_details == "SimpleType":
                        self.trans_element_simple(name, details, subject)
                    elif type_details == "ComplexType":
                        self.trans_element_complex(name, details, subject)
                    elif type_details == "ArrayType":
                        self.trans_element_array(name, details, subject)
                    elif type_details == "RefType":
                        self.trans_element_ref(name, details, subject)
                    elif type_details == "LogicalType":
                        self.trans_element_logical(name, details, subject)

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
                    type_details = check_type(details)
                    if type_details == "SimpleType":
                        self.trans_element_simple(name, details, subject)
                    elif type_details == "ComplexType":
                        self.trans_element_complex(name, details, subject)
                    elif type_details == "ArrayType":
                        self.trans_element_array(name, details, subject)
                    elif type_details == "RefType":
                        self.trans_element_ref(name, details, subject)

            self.trans_complex_restrictions(entry, subject)
        else:
            self.trans_simple_restrictions(entry, pre_subject)

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
                        elif check_type(item) == "ArrayType":
                            self.trans_element_array(
                                f"{entry_name}P{number_of_items}", item, subject)
                        elif check_type(item) == "RefType":
                            self.trans_element_ref(
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
                        else:
                            p = self.shacl_ns.minCount
                            o = Literal(1)
                            self.shacl.add((new_contains_shape, p, o))
                        if entry.get('maxContains'):
                            p = self.shacl_ns.maxCount
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
                    elif check_type(item) == "ArrayType":
                        self.trans_element_array(
                            f"{entry_name}", item, subject_property)
                    elif check_type(item) == "RefType":
                        self.trans_element_ref(
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
                    else:
                        p = self.shacl_ns.minCount
                        o = Literal(1)
                        self.shacl.add((subject_property, p, o))
                    if entry.get('maxContains'):
                        p = self.shacl_ns.maxCount
                        o = Literal(entry.get('maxContains'))
                        self.shacl.add((subject_property, p, o))
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
                    elif check_type(prefix_item) == "ArrayType":
                        self.trans_element_array(
                            f"{entry_name}P{number_of_items}", prefix_item, subject)
                    elif check_type(prefix_item) == "RefType":
                        self.trans_element_ref(
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
                    elif check_type(item) == "ArrayType":
                        self.trans_element_array(
                            f"{entry_name}P{number_of_items}", item, subject)
                    elif check_type(item) == "RefType":
                        self.trans_element_ref(
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
                    else:
                        p = self.shacl_ns.minCount
                        o = Literal(1)
                        self.shacl.add((new_contains_shape, p, o))
                    if entry.get('maxContains'):
                        p = self.shacl_ns.maxCount
                        o = Literal(entry.get('maxContains'))
                        self.shacl.add((new_contains_shape, p, o))
                    number_of_items += 1

        self.trans_array_restrictions(entry, subject)

    def trans_element_ref(self, name: str, ref_dict: dict, subject) -> None:
        ref_path = ref_dict["$ref"]
        if ref_path.startswith("#"):
            ref_path = ref_path.replace("#", "$.").split("./")[1]
            jsonpath_expr_str = '$.'
            for split_name in ref_path.split("/"):
                jsonpath_expr_str += f'["{split_name}"]'
        else:
            return None

        ref_name = ref_path.split("/")[-1]
        jsonpath_expr = parse(jsonpath_expr_str)

        ref_element = [
            match.value for match in jsonpath_expr.find(self.schema)][0]

        print(ref_element)
        print(ref_name)
        # Check the type of the referenced element
        ref_type = check_type(ref_element)

        # Depending on the type, call the appropriate translation function
        if ref_type == "SimpleType":
            self.trans_element_simple(name, ref_element, subject)
        elif ref_type == "ComplexType":
            ref_node_shape = self.trans_complex(ref_element, ref_name)
            ref_subject_property = self.ns[f'PropertyShape/{name}']
            self.shacl.add(
                (subject, self.shacl_ns.property, ref_subject_property))
            self.shacl.add(
                (ref_subject_property, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
            self.shacl.add((ref_subject_property, self.shacl_ns.path,
                            self.xsd_target_ns[name]))
            self.shapes.append(ref_subject_property)
            self.shacl.add(
                (ref_subject_property, self.shacl_ns.node, ref_node_shape))
        elif ref_type == "ArrayType":
            ref_node_shape = self.trans_array(ref_element, ref_name)
            ref_subject_property = self.ns[f'PropertyShape/{name}']
            self.shacl.add(
                (subject, self.shacl_ns.property, ref_subject_property))
            self.shacl.add(
                (ref_subject_property, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
            self.shacl.add((ref_subject_property, self.shacl_ns.path,
                            self.xsd_target_ns[name]))
            self.shapes.append(ref_subject_property)
            self.shacl.add(
                (ref_subject_property, self.shacl_ns.node, ref_node_shape))

    def trans_element_logical(self, entry_name: str, entry: dict, pre_subject: URIRef) -> None:

        logical_list = BNode()

        if entry.get('allOf'):
            entry_name = f'{entry_name}AllOf'
            elements = entry.get('allOf')
            self.shacl.add((pre_subject, self.shacl_ns.and_, logical_list))
        elif entry.get('anyOf'):
            entry_name = f'{entry_name}AnyOf'
            elements = entry.get('anyOf')
            self.shacl.add((pre_subject, self.shacl_ns.or_, logical_list))
        elif entry.get('oneOf'):
            entry_name = f'{entry_name}OneOf'
            elements = entry.get('oneOf')
            self.shacl.add((pre_subject, self.shacl_ns.xone, logical_list))
        elif entry.get('not'):
            entry_name = f'{entry_name}Not'
            elements = entry.get('not')
            self.shacl.add((pre_subject, self.shacl_ns.not_, logical_list))

        empty_first_time = True
        iterator_number = 0
        length_elements = len(elements)
        length_parity = length_elements % 2
        for schema in elements:
            node_element = BNode()
            if empty_first_time:
                self.shacl.add(
                    (logical_list, self.rdf_syntax.first, node_element))
                schema_type = check_type(schema)
                if schema_type == "SimpleType":
                    self.trans_element_simple(
                        f'{entry_name}{iterator_number}', schema, node_element)
                elif schema_type == "ComplexType":
                    self.trans_element_complex(
                        f'{entry_name}{iterator_number}', schema, node_element)
                elif schema_type == "ArrayType":
                    self.trans_element_array(
                        f'{entry_name}{iterator_number}', schema, node_element)
                elif schema_type == "RefType":
                    self.trans_element_ref(
                        f'{entry_name}{iterator_number}', schema, node_element)
                elif schema_type == "LogicalType":
                    self.trans_element_logical(
                        f'{entry_name}{iterator_number}', schema, node_element)
                empty_first_time = False
            else:
                if iterator_number < length_elements - 1:
                    next_node = BNode()
                    self.shacl.add(
                        (node_element, self.rdf_syntax.rest, next_node))
                    node_element = next_node
                    schema_type = check_type(schema)
                    if schema_type == "SimpleType":
                        self.trans_element_simple(
                            f'{entry_name}{iterator_number}', schema, node_element)
                    elif schema_type == "ComplexType":
                        self.trans_element_complex(
                            f'{entry_name}{iterator_number}', schema, node_element)
                    elif schema_type == "ArrayType":
                        self.trans_element_array(
                            f'{entry_name}{iterator_number}', schema, node_element)
                    elif schema_type == "RefType":
                        self.trans_element_ref(
                            f'{entry_name}{iterator_number}', schema, node_element)
                    elif schema_type == "LogicalType":
                        self.trans_element_logical(
                            f'{entry_name}{iterator_number}', schema, node_element)
                else:
                    if length_parity == 0:
                        next_node = BNode()
                        self.shacl.add(
                            (node_element, self.rdf_syntax.rest, next_node))
                        schema_type = check_type(schema)
                        if schema_type == "SimpleType":
                            self.trans_element_simple(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "ComplexType":
                            self.trans_element_complex(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "ArrayType":
                            self.trans_element_array(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "RefType":
                            self.trans_element_ref(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "LogicalType":
                            self.trans_element_logical(
                                f'{entry_name}{iterator_number}', schema, node_element)
                    else:
                        next_node = BNode()
                        self.shacl.add(
                            (node_element, self.rdf_syntax.rest, next_node))
                        node_element = next_node
                        schema_type = check_type(schema)
                        if schema_type == "SimpleType":
                            self.trans_element_simple(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "ComplexType":
                            self.trans_element_complex(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "ArrayType":
                            self.trans_element_array(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "RefType":
                            self.trans_element_ref(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        elif schema_type == "LogicalType":
                            self.trans_element_logical(
                                f'{entry_name}{iterator_number}', schema, node_element)
                        self.shacl.add(
                            (node_element, self.rdf_syntax.rest, self.rdf_syntax.nil))
            iterator_number += 1

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
        if element.get('if'):
            or_node = BNode()
            self.shacl.add((subject, self.shacl_ns.or_, or_node))

            and_list = BNode()
            and_node = BNode()
            self.shacl.add((and_list, self.shacl_ns.and_, and_node))
            self.shacl.add((or_node, self.rdf_syntax.first, and_list))

            if_node = BNode()
            self.shacl.add((and_node, self.rdf_syntax.first, if_node))
            element_if = element.get('if')
            if element_if.get('properties') is not None:
                for name, details in element_if.get('properties', {}).items():
                    exiting_shape = False
                    if self.shapes:
                        for shape in self.shapes:
                            if f'PropertyShape/{name}' in str(shape):
                                self.shacl.add((if_node, self.shacl_ns.path,
                                               self.xsd_target_ns[name]))
                                self.trans_simple_restrictions(
                                    details, if_node)
                                self.trans_complex_restrictions(
                                    details, if_node)
                                self.trans_array_restrictions(
                                    details, if_node)
                                exiting_shape = True
                    if not exiting_shape:
                        type_details = check_type(details)
                        if type_details == "SimpleType":
                            self.trans_element_simple(
                                name, details, if_node)
                        elif type_details == "ComplexType":
                            self.trans_element_complex(
                                name, details, if_node)
                        elif type_details == "ArrayType":
                            self.trans_element_array(
                                name, details, if_node)
                        elif type_details == "RefType":
                            self.trans_element_ref(
                                name, details, if_node)

            then_node = BNode()
            self.shacl.add((and_node, self.rdf_syntax.rest, then_node))
            element_then = element.get('then')
            # Print
            print(self.shacl.serialize(format="turtle"))
            if element_then.get('type') is not None:
                then_element_type = element_then.get('type')
                type_then_element = check_type(then_element_type)
                if type_then_element == "SimpleType":
                    self.trans_element_simple(
                        f"{subject.split('/')[-1]}Then", element_then, then_node)
                elif type_then_element == "ComplexType":
                    self.trans_element_complex(
                        f"{subject.split('/')[-1]}Then", element_then, then_node)
                elif type_then_element == "ArrayType":
                    self.trans_element_array(
                        f"{subject.split('/')[-1]}Then", element_then, then_node)
                elif type_then_element == "RefType":
                    self.trans_element_ref(
                        f"{subject.split('/')[-1]}Then", element_then, then_node)
            elif element_then.get('properties') is not None:
                for name, details in element_then.get('properties', {}).items():
                    exiting_shape = False
                    if self.shapes:
                        for shape in self.shapes:
                            if f'PropertyShape/{name}' in str(shape):
                                self.shacl.add((then_node, self.shacl_ns.path,
                                               self.xsd_target_ns[name]))
                                self.trans_simple_restrictions(
                                    details, then_node)
                                self.trans_complex_restrictions(
                                    details, then_node)
                                self.trans_array_restrictions(
                                    details, then_node)
                                exiting_shape = True
                    if not exiting_shape:
                        type_details = check_type(details)
                        if type_details == "SimpleType":
                            self.shacl.add((then_node, self.shacl_ns.path,
                                            self.xsd_target_ns[name]))
                            self.trans_simple_restrictions(
                                details, then_node)
                            self.trans_complex_restrictions(
                                details, then_node)
                            self.trans_array_restrictions(
                                details, then_node)
                            # self.trans_element_simple(
                            #     name, details, then_node)
                        elif type_details == "ComplexType":
                            self.trans_element_complex(
                                name, details, then_node)
                        elif type_details == "ArrayType":
                            self.trans_element_array(
                                name, details, then_node)
                        elif type_details == "RefType":
                            self.trans_element_ref(
                                name, details, then_node)
            elif check_if_object_has_properties_or_restrictions(element_then) is True:
                self.trans_complex_restrictions(element_then, then_node)

            # Print
            print("-------------------")
            # Print
            print(self.shacl.serialize(format="turtle"))
            if element.get('else'):
                else_node = BNode()
                self.shacl.add((or_node, self.rdf_syntax.rest, else_node))
                element_else = element.get('else')
                if element_else.get('type') is not None:
                    else_element_type = element_else.get('type')
                    if check_type(else_element_type) == "SimpleType":
                        self.trans_element_simple(
                            f"{subject.split('/')[-1]}Then", element_else, else_node)
                    elif check_type(else_element_type) == "ComplexType":
                        self.trans_element_complex(
                            f"{subject.split('/')[-1]}Then", element_else, else_node)
                    elif check_type(else_element_type) == "ArrayType":
                        self.trans_element_array(
                            f"{subject.split('/')[-1]}Then", element_else, else_node)
                    elif check_type(else_element_type) == "RefType":
                        self.trans_element_ref(
                            f"{subject.split('/')[-1]}Then", element_else, else_node)
                elif element_else.get('properties') is not None:
                    for name, details in element_else.get('properties', {}).items():
                        exiting_shape = False
                        if self.shapes:
                            for shape in self.shapes:
                                if f'PropertyShape/{name}' in str(shape):
                                    self.shacl.add((else_node, self.shacl_ns.path,
                                                    self.xsd_target_ns[name]))
                                    self.trans_simple_restrictions(
                                        details, else_node)
                                    self.trans_complex_restrictions(
                                        details, else_node)
                                    self.trans_array_restrictions(
                                        details, else_node)
                                    exiting_shape = True
                        if not exiting_shape:
                            if type_details == "SimpleType":
                                self.shacl.add((else_node, self.shacl_ns.path,
                                                self.xsd_target_ns[name]))
                                self.trans_simple_restrictions(
                                    details, else_node)
                                self.trans_complex_restrictions(
                                    details, else_node)
                                self.trans_array_restrictions(
                                    details, else_node)
                                # self.trans_element_simple(
                                #     name, details, else_node)
                            elif check_type(details) == "ComplexType":
                                self.trans_element_complex(
                                    name, details, else_node)
                            elif check_type(details) == "ArrayType":
                                self.trans_element_array(
                                    name, details, else_node)
                            elif check_type(details) == "RefType":
                                self.trans_element_ref(
                                    name, details, else_node)
                elif check_if_object_has_properties_or_restrictions(element_then) is True:
                    self.trans_complex_restrictions(element_then, else_node)
            else:
                self.shacl.add(
                    (or_node, self.rdf_syntax.rest, self.rdf_syntax.nil))

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

    def trans_simple(self, element: dict, ref_name: str = None) -> URIRef:
        """A function to translate elements of SimpleType"""

        if ref_name is not None:
            entry_name = ref_name
        else:
            entry_name = element.get("name")

        subject = self.ns[f'PropertyShape/{entry_name}']

        if self.shapes:
            for shape in self.shapes:
                if entry_name in str(shape):
                    return shape

        self.shapes.append(subject)
        self.shacl.add(
            (subject, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))
        self.shacl.add((subject, self.shacl_ns.path,
                        self.xsd_target_ns[entry_name]))

        self.trans_simple_restrictions(element, subject)

        return subject

    def trans_array(self, element: dict, ref_name: str = None) -> None:
        """A function to translate arrays inside a ComplexType"""

        if ref_name is not None:
            element_name = ref_name
        else:
            element_name = element.get("name")

        subject = self.ns[f'NodeShape/{element_name}']

        if self.shapes:
            for shape in self.shapes:
                if element_name in str(shape):
                    if "NodeShape" in str(shape):
                        return shape

        if element.get('items') is not None:
            type_items = check_type(element.get('items'))
        else:
            type_items = None

        if element.get('prefixItems') is not None or type_items != "SimpleType":
            self.shacl.add(
                (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
            self.shacl.add(
                (subject, self.shacl_ns.name, Literal(element_name)))
            self.shapes.append(subject)

        if element.get('prefixItems') is None:
            item = element.get('items')
            contains = element.get('contains')

            if contains is not None and item is not None:
                number_of_items = 0
                item = element.get('items')
                if item is not None:
                    if item == "true" or item == "false":
                        self.shacl.add(
                            (subject, self.shacl_ns.closed, Literal(item)))
                    else:
                        if check_type(item) == "SimpleType":
                            self.trans_element_simple(
                                f"{element_name}P{number_of_items}", item, subject)
                        elif check_type(item) == "ComplexType":
                            self.trans_element_complex(
                                f"{element_name}P{number_of_items}", item, subject)
                        number_of_items += 1

                contains = element.get('contains')
                if contains is not None:
                    if check_type(contains) == "SimpleType":
                        new_contains_shape = self.trans_element_simple(
                            f"{element_name}P{number_of_items}", contains, subject)
                        if element.get('minContains'):
                            p = self.shacl_ns.minCount
                            o = Literal(element.get('minContains'))
                            self.shacl.add((new_contains_shape, p, o))
                        if element.get('maxContains'):
                            p = self.shacl_ns.maxCount
                            o = Literal(element.get('maxContains'))
                            self.shacl.add((new_contains_shape, p, o))
                        number_of_items += 1
            elif item is not None:
                if item == "true" or item == "false":
                    self.shacl.add(
                        (subject, self.shacl_ns.closed, Literal(item)))
                else:
                    if check_type(item) == "SimpleType":
                        self.trans_element_simple(
                            element_name, item, subject)
                    elif check_type(item) == "ComplexType":
                        self.trans_element_complex_array(
                            element_name, item, subject)
            elif contains is not None:
                if check_type(contains) == "SimpleType":
                    subject_property = self.trans_element_simple(
                        element_name, item, subject)
                    if element.get('minContains'):
                        p = self.shacl_ns.minCount
                        o = Literal(element.get('minContains'))
                        self.shacl.add((subject_property, p, o))
                    else:
                        p = self.shacl_ns.minCount
                        o = Literal(1)
                        self.shacl.add((subject_property, p, o))
                    if element.get('maxContains'):
                        p = self.shacl_ns.maxCount
                        o = Literal(element.get('maxContains'))
                        self.shacl.add((subject_property, p, o))
        else:
            number_of_items = 0

            if element.get('prefixItems') is not None:
                for prefix_item in element.get('prefixItems'):
                    if check_type(prefix_item) == "SimpleType":
                        self.trans_element_simple(
                            f"{element_name}P{number_of_items}", prefix_item, subject)
                    elif check_type(prefix_item) == "ComplexType":
                        self.trans_element_complex(
                            f"{element_name}P{number_of_items}", prefix_item, subject)
                    number_of_items += 1

            item = element.get('items')
            if item is not None:
                if item == "true" or item == "false":
                    self.shacl.add(
                        (subject, self.shacl_ns.closed, Literal(item)))
                else:
                    if check_type(item) == "SimpleType":
                        self.trans_element_simple(
                            f"{element_name}P{number_of_items}", item, subject)
                    elif check_type(item) == "ComplexType":
                        self.trans_element_complex(
                            f"{element_name}P{number_of_items}", item, subject)
                    number_of_items += 1

            contains = element.get('contains')
            if contains is not None:
                if check_type(contains) == "SimpleType":
                    new_contains_shape = self.trans_element_simple(
                        f"{element_name}P{number_of_items}", contains, subject)
                    if element.get('minContains'):
                        p = self.shacl_ns.minCount
                        o = Literal(element.get('minContains'))
                        self.shacl.add((new_contains_shape, p, o))
                    if element.get('maxContains'):
                        p = self.shacl_ns.maxCount
                        o = Literal(element.get('maxContains'))
                        self.shacl.add((new_contains_shape, p, o))
                    number_of_items += 1

        self.trans_array_restrictions(element, subject)
        return subject

    def trans_complex(self, element: dict, ref_name: str = None) -> URIRef:
        """A function to translate ComplexType elements"""
        if ref_name is not None:
            element_name = ref_name
        else:
            element_name = element.get("name")

        subject = self.ns[f'NodeShape/{element_name}']

        if self.shapes:
            for shape in self.shapes:
                if element_name in str(shape):
                    if "NodeShape" in str(shape):
                        return shape

        self.shapes.append(subject)
        self.shacl.add(
            (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
        self.shacl.add((subject, self.shacl_ns.name, Literal(element_name)))

        self.shacl.add((subject, self.shacl_ns.targetClass,
                        self.xsd_target_ns[element_name]))

        if element.get('properties') is not None:
            for name, details in element.get('properties', {}).items():
                type_details = check_type(details)
                if type_details == "SimpleType":
                    self.trans_element_simple(name, details, subject)
                elif type_details == "ComplexType":
                    self.trans_element_complex(name, details, subject)
                elif type_details == "ArrayType":
                    self.trans_element_array(name, details, subject)
                elif type_details == "RefType":
                    self.trans_element_ref(name, details, subject)
                elif type_details == "LogicalType":
                    self.trans_element_logical(name, details, subject)

        self.trans_simple_restrictions(element, subject)
        self.trans_complex_restrictions(element, subject)

        return subject

    def translate(self, element: dict) -> Graph:
        """Function to translate JSON Schema to SHACL"""
        self.schema = element
        type_element = check_type(element)
        if type_element == "ComplexType":
            self.trans_complex(element)
        elif type_element == "ArrayType":
            self.trans_array(element)
        elif type_element == "SimpleType":
            self.trans_simple(element)

        return self.shacl
