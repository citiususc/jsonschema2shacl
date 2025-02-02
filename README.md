# JSONSchema2SHACL
The repository contains the source code for extracting and generating SHACL shapes from JSONSchema

## Installation:
```
pip install jsonschema2shacl
```

## Execution from CLI
To execute from command line run the following:

```bash
python3 -m jsonschema2shacl path_to_input_jsonschema.json
```

## Execution as a library

If you want to include the module in your implementation:
```python
import jsonschema2shacl
json_converter = JsonSchemaToShacl()
json_converter.translate(schema)
```

## Authors
- [David Chaves Fraga](mailto:david.chaves@usc.es)
- Óscar Suárez Montes
