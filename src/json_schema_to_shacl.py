import argparse
from rdflib import Graph, Namespace, Literal
# from pyshacl import validate
from file_parser import leer_json_schema


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

    def is_simple_complex(self, element):
        """A function to determine whether the type of element is SimpleType or ComplexType"""
        element_type = element.get("type")
        if element_type == "object" or element_type == "array":
            return "ComplexType"
        else:
            return "SimpleType"

    def trans_element_simple(self, entry_name, entry, pre_subject=None):
        """A function to translate elements inside of a SimpleType

        Args:
            entry_name (str): name of the simple element
            entry (object): object with properties of json schema entry
        """
        subject = self.ns[f'NodeShape/{entry_name}']

        if pre_subject is None:
            pre_subject_path = ""
            pre_subject = self.ns
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
                pre_subject = self.ns[f'NodeShape/{pre_subject_path}']
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]
                pre_subject = self.ns[f'NodeShape/{pre_subject_path}']

        self.shacl.add((pre_subject, self.shacl_ns.property, subject))
        self.shapes.append(subject)
        self.shacl.add(
            (subject, self.rdf_syntax['type'], self.shacl_ns.PropertyShape))
        self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))
        self.shacl.add((subject, self.shacl_ns.path,
                       self.xsd_target_ns[entry_name]))
        # print(entry)

    def trans_element_complex(self, entry_name, entry, pre_subject=None):
        """A function to translate elements inside of a ComplexType

        Args:
            name (str): name of the entry
            element (object): object with properties of json schema entry
        """
        subject = self.ns[f'NodeShape/{entry_name}']

        if pre_subject is None:
            pre_subject_path = ""
            pre_subject = self.ns
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
                pre_subject = self.ns[f'NodeShape/{pre_subject_path}']
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]
                pre_subject = self.ns[f'PropertyShape/{pre_subject_path}']

        self.shacl.add((pre_subject, self.shacl_ns.node, subject))
        self.shapes.append(subject)
        self.shacl.add(
            (subject, self.rdf_syntax['type'], self.shacl_ns.NodeShape))
        self.shacl.add((subject, self.shacl_ns.name, Literal(entry_name)))

        self.shacl.add((subject, self.shacl_ns.targetClass,
                       self.xsd_target_ns[entry_name]))

        for name, details in entry.get('properties', {}).items():
            if self.is_simple_complex(details) == "SimpleType":
                self.trans_element_simple(name, details, subject)
            elif self.is_simple_complex(details) == "ComplexType":
                self.trans_element_complex(name, details, subject)

        # print(entry)

    def trans_complex(self, element):
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
            if self.is_simple_complex(details) == "SimpleType":
                print(name)
                print("Simple")
                self.trans_element_simple(name, details, subject)
            elif self.is_simple_complex(details) == "ComplexType":
                print(name)
                print("Complex")
                self.trans_element_complex(name, details, subject)
            else:
                print(name)
                print("Test")
            # for child in element.get("properties"):
            #     child_type = child.get("type")
            #     if(self.isSimpleComplex(child) == "SimpleType"):
            #         self.SHACL.add((self.NS[child.get("name")],self.shaclNS["datatype"],self.xsdNS[child_type]))
            #     elif(self.isSimpleComplex(child) == "ComplexType"):
            #         self.SHACL.add((self.NS[child.get("name")],self.shaclNS["nodeKind"],self.shaclNS["BlankNodeOrIRI"]))
            #         self.translate(child

    def translate(self, element):
        """Function to translate JSON Schema to SHACL

        Args:
            element (object): JSON Schema object
        """
        if self.is_simple_complex(element) == "ComplexType":
            self.trans_complex(element)
            # for prop, details in schema.get('properties', {}).items():
            # print(prop)
            # print("-")
            # print(details)
            # print("-------")
            # for child in element.get("properties"):
            #     child_type = child.get("type")
            #     if(self.isSimpleComplex(child) == "SimpleType"):
            #         self.SHACL.add((self.NS[child.get("name")],self.shaclNS["datatype"],self.xsdNS[child_type]))
            #     elif(self.isSimpleComplex(child) == "ComplexType"):
            #         self.SHACL.add((self.NS[child.get("name")],self.shaclNS["nodeKind"],self.shaclNS["BlankNodeOrIRI"]))
            #         self.translate(child)


def main():
    """Main function to exucute
    """
    parser = argparse.ArgumentParser(
        description="Convertir JSON Schema a SHACL")
    parser.add_argument("archivo_json", type=str,
                        help="Ruta al archivo JSON Schema")
    args = parser.parse_args()

    ruta_archivo = args.archivo_json
    schema = leer_json_schema(ruta_archivo)

    json_converter = JsonSchemaToShacl()

    if schema is not None:
        print("¡Archivo leído con éxito! Ahora puedes continuar con la conversión a SHACL.")
        print(schema)

        if schema.get("type"):
            print(schema.get("type"))

        json_converter.translate(schema)

        print(json_converter.shacl.serialize(format="turtle"))


        # print(schema.keys())
        # for key in schema.keys():
        #     element = schema.get(key)
        #     print(element)
        #     print("-------")
if __name__ == "__main__":
    main()
