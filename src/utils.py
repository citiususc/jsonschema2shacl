def check_type(element: dict) -> str:
    """A function to determine whether the type of element is SimpleType or ComplexType"""
    element_type = element.get("type")
    if element_type == "object":
        return "ComplexType"
    elif element_type == "array":
        return "ArrayType"
    elif element.get("$ref"):
        return "RefType"
    elif (element.get("allOf") is not None) or (element.get("anyOf") is not None) or (element.get("oneOf") is not None) or (element.get("not") is not None):
        return "LogicalType"
    else:
        return "SimpleType"


def check_if_object_has_properties_or_restrictions(element: dict) -> bool:
    if element.get('properties') or element.get('additionalProperties') or element.get('required') or element.get(
        'unevaluatedProperties') or element.get('patternProperties') or element.get(
            'propertyNames') or element.get('dependentRequired'):
        return True
    return False
