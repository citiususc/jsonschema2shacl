def build_in_types(json_type):
    type_map = {
        "string": "string",
        "number": "decimal",
        "integer": "integer",
        "boolean": "boolean",
        "null": "nil"
    }
    return type_map.get(json_type, None)


def format_types(format_type):
    format_type_map = {
        "date-time": "dateTime",
        "date": "date",
        "time": "time",
        "duration": "duration"
    }
    return format_type_map.get(format_type, None)
