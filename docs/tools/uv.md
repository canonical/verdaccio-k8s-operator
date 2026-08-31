### Install Pydantic using pip or uv

Source: https://github.com/pydantic/pydantic/blob/main/docs/install.md

Standard installation for Python 3.10+ environments.

```bash
pip install pydantic
```

```bash
uv add pydantic
```

--------------------------------

### Install Logfire SDK and authenticate via CLI

Source: https://github.com/pydantic/pydantic/blob/main/docs/errors/troubleshooting.md

Install the Logfire package and authenticate your environment with your Logfire account.

```bash
pip install logfire
logfire auth
```

--------------------------------

### Install Pydantic from GitHub repository

Source: https://github.com/pydantic/pydantic/blob/main/docs/install.md

Install the latest development version directly from the main branch.

```bash
pip install 'git+https://github.com/pydantic/pydantic@main'
# or with `email` and `timezone` extras:
pip install 'git+https://github.com/pydantic/pydantic@main#egg=pydantic[email,timezone]'
```

```bash
uv add 'git+https://github.com/pydantic/pydantic@main'
# or with `email` and `timezone` extras:
uv add 'git+https://github.com/pydantic/pydantic@main#egg=pydantic[email,timezone]'
```

--------------------------------

### Build and serve documentation

Source: https://github.com/pydantic/pydantic/blob/main/CONTRIBUTING.md

Build the documentation to verify that your changes to docstrings or guides render correctly.

```bash
# Build documentation
make docs
# If you have changed the documentation, make sure it builds successfully.
# You can also use `uv run mkdocs serve` to serve the documentation at localhost:8000
```

--------------------------------

### Install datamodel-code-generator using pip

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/datamodel_code_generator.md

Installs the datamodel-code-generator CLI utility and library via pip.

```bash
pip install datamodel-code-generator
```

--------------------------------

### Clone and install pydantic-core repository in Bash

Source: https://github.com/pydantic/pydantic/blob/main/pydantic-core/README.md

Clones the repository and installs development dependencies and pre-commit hooks via uv and make.

```bash
# Clone the repository (or from your fork)
git clone git@github.com:pydantic/pydantic-core.git
cd pydantic-core

# Install all dependencies using uv, setup pre-commit hooks, and build the development version
make install
```

--------------------------------

### Install Pydantic V2 Migration Tool

Source: https://github.com/pydantic/pydantic/blob/main/docs/migration.md

Install the `bump-pydantic` tool to assist with automated code migration from Pydantic V1 to V2.

```bash
pip install bump-pydantic
```

--------------------------------

### Clone and set up the Pydantic repository

Source: https://github.com/pydantic/pydantic/blob/main/CONTRIBUTING.md

Use these commands to clone the repo and install all necessary development tools including uv and pre-commit.

```bash
# Clone your fork and cd into the repo directory
git clone git@github.com:<your username>/pydantic.git
cd pydantic

# Install UV and pre-commit
# We use uv here, for other options see:
# https://docs.astral.sh/uv/getting-started/installation/
# https://pre-commit.com/#install
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install pre-commit

# Install pydantic, dependencies, test dependencies and doc dependencies
make install
```

--------------------------------

### Install Pydantic via Conda

Source: https://github.com/pydantic/pydantic/blob/main/docs/install.md

Installation using the conda-forge channel.

```bash
conda install pydantic -c conda-forge
```

--------------------------------

### Install Pydantic V2

Source: https://github.com/pydantic/pydantic/blob/main/docs/migration.md

Use this command to install the latest production release of Pydantic V2 from PyPI.

```bash
pip install -U pydantic
```

--------------------------------

### Install Pydantic via pip

Source: https://github.com/pydantic/pydantic/blob/main/docs/index.md

Use this command to install the Pydantic library into your Python environment.

```bash
pip install pydantic
```

--------------------------------

### Install Pydantic with optional dependencies

Source: https://github.com/pydantic/pydantic/blob/main/docs/install.md

Includes extras like email validation and timezone support.

```bash
# with the `email` extra:
pip install 'pydantic[email]'
# or with `email` and `timezone` extras:
pip install 'pydantic[email,timezone]'
```

```bash
# with the `email` extra:
uv add 'pydantic[email]'
# or with `email` and `timezone` extras:
uv add 'pydantic[email,timezone]'
```

--------------------------------

### Install Pydantic V1

Source: https://github.com/pydantic/pydantic/blob/main/docs/migration.md

Install a specific version of Pydantic V1 if you need to continue using its features without migrating to V2.

```bash
pip install "pydantic==1.*"
```

--------------------------------

### Example Person Record in JSON

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Sample JSON file structure representing a single person's data.

```json
{
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
}
```

--------------------------------

### Example List of Person Records in JSON

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Sample JSON array containing multiple person objects.

```json
[
    {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
    },
    {
        "name": "Jane Doe",
        "age": 25,
        "email": "jane@example.com"
    }
]
```

--------------------------------

### Sample CSV data format

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Example structure of a standard CSV file with headers.

```csv
name,age,email
John Doe,30,john@example.com
Jane Doe,25,jane@example.com
```

--------------------------------

### Example Pydantic Model and Usage

Source: https://github.com/pydantic/pydantic/blob/main/tests/mypy/README.md

An example of a Pydantic BaseModel and its usage, demonstrating a potential Mypy error.

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int


model = Model(a=1, b=2)
```

--------------------------------

### Testing and Updating Documentation Examples with Pytest

Source: https://github.com/pydantic/pydantic/blob/main/CONTRIBUTING.md

Use the --update-examples flag with pytest to verify documentation code blocks and automatically refresh their formatting and output.

```bash
# Run tests and update code examples
pytest tests/test_docs.py --update-examples
```

--------------------------------

### Sample JSON Lines data format

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Example structure of a .jsonl file containing newline-delimited JSON objects.

```json
{"name": "John Doe", "age": 30, "email": "john@example.com"}
{"name": "Jane Doe", "age": 25, "email": "jane@example.com"}
```

--------------------------------

### Generating JSON schema from a TypeAdapter

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example demonstrating how to generate JSON schema for an arbitrary type using TypeAdapter.

```python
from pydantic import TypeAdapter

adapter = TypeAdapter(list[int])
print(adapter.json_schema())
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

--------------------------------

### Asserting TypeAdapter type

Source: https://github.com/pydantic/pydantic/blob/main/tests/typechecking/README.md

Example demonstrating how to use `assert_type` from `typing_extensions` to verify the type of a `TypeAdapter` instance.

```python
from typing_extensions import assert_type

from pydantic import TypeAdapter

ta1 = TypeAdapter(int)
assert_type(ta1, TypeAdapter[int])
```

--------------------------------

### View missing pydantic_core error message

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/aws_lambda.md

Common error message indicating incorrect or missing native binary installation for pydantic_core.

```text
no module named `pydantic_core._pydantic_core`
```

--------------------------------

### Define models for exclusion and inclusion examples in Pydantic

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/serialization.md

Defines base models and sample instance data to demonstrate serialization filtering options.

```python
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr


class Transaction(BaseModel):
    id: str
    private_id: str = Field(exclude=True)
    user: User
    value: int


t = Transaction(
    id='1234567890',
    private_id='123',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)
```

--------------------------------

### Check target Python platform extension suffix in Python

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/aws_lambda.md

Use sysconfig to verify the expected native extension suffix matches the installed binary extension.

```python
import sysconfig
print(sysconfig.get_config_var("EXT_SUFFIX"))
#> '.cpython-312-x86_64-linux-gnu.so'
```

--------------------------------

### Config in class arguments (using model_config)

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/visual_studio_code.md

Example of setting model configurations using an internal 'model_config' dictionary within the model class.

```python
from pydantic import BaseModel


class Knight(BaseModel):
    model_config = dict(frozen=True)
    title: str
    age: int
    color: str = 'blue'
```

--------------------------------

### Generating JSON Schema for Union Types with TypeAdapter

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

This example demonstrates how to generate a JSON Schema for a union of Pydantic models using `TypeAdapter`.

```python
import json

from pydantic import BaseModel, TypeAdapter


class Cat(BaseModel):
    name: str
    color: str


class Dog(BaseModel):
    name: str
    breed: str

ta = TypeAdapter(Cat | Dog)
ta_schema = ta.json_schema()
print(json.dumps(ta_schema, indent=2))
"""
{
  "$defs": {
    "Cat": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "color": {
          "title": "Color",
          "type": "string"
        }
      },
      "required": [
        "name",
        "color"
      ],
      "title": "Cat",
      "type": "object"
    },
    "Dog": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "breed": {
          "title": "Breed",
          "type": "string"
        }
      },
      "required": [
        "name",
        "breed"
      ],
      "title": "Dog",
      "type": "object"
    }
  },
  "anyOf": [
    {
      "$ref": "#/$defs/Cat"
    },
    {
      "$ref": "#/$defs/Dog"
    }
  ]
}
"""
```

--------------------------------

### Define input JSON Schema for code generation

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/datamodel_code_generator.md

Example JSON Schema containing object properties, required fields, and nested definitions to be converted into Pydantic models.

```json
{
  "$id": "person.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Person",
  "type": "object",
  "properties": {
    "first_name": {
      "type": "string",
      "description": "The person's first name."
    },
    "last_name": {
      "type": "string",
      "description": "The person's last name."
    },
    "age": {
      "description": "Age in years.",
      "type": "integer",
      "minimum": 0
    },
    "pets": {
      "type": "array",
      "items": [
        {
          "$ref": "#/definitions/Pet"
        }
      ]
    },
    "comment": {
      "type": "null"
    }
  },
  "required": [
      "first_name",
      "last_name"
  ],
  "definitions": {
    "Pet": {
      "properties": {
        "name": {
          "type": "string"
        },
        "age": {
          "type": "integer"
        }
      }
    }
  }
}
```

--------------------------------

### Annotated Metadata for String Restriction

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example of using `Annotated` metadata with a `RestrictCharacters` class to validate that a string only contains characters from a specified alphabet. This example calls the handler to get the inner schema.

```python
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationError


@dataclass
class RestrictCharacters:
    alphabet: Sequence[str]

    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if not self.alphabet:
            raise ValueError('Alphabet may not be empty')
        schema = handler(
            source
        )  # get the CoreSchema from the type / inner constraints
        if schema['type'] != 'str':
            raise TypeError('RestrictCharacters can only be applied to strings')
        return core_schema.no_info_after_validator_function(
            self.validate,
            schema,
        )

    def validate(self, value: str) -> str:
        if any(c not in self.alphabet for c in value):
            raise ValueError(
                f'{value!r} is not restricted to {self.alphabet!r}'
            )
        return value


class MyModel(BaseModel):
    value: Annotated[str, RestrictCharacters('ABC')]


print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='CBA'))
#> value='CBA'

try:
    MyModel(value='XYZ')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      Value error, 'XYZ' is not restricted to 'ABC' [type=value_error, input_value='XYZ', input_type=str]
    """
```

--------------------------------

### Define sample YAML configuration file

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Sample YAML file containing user configuration data.

```yaml
name: John Doe
age: 30
email: john@example.com
```

--------------------------------

### Local development make commands

Source: https://github.com/pydantic/pydantic/blob/main/docs/contributing.md

Standard commands for formatting, testing, and documentation generation during local development.

```bash
make format
```

```bash
make
```

```bash
make docs
```

--------------------------------

### Run full development cycle with Make in Bash

Source: https://github.com/pydantic/pydantic/blob/main/pydantic-core/README.md

Executes the default Make target to format, build, lint, and test the project.

```bash
make
```

--------------------------------

### Create a Dynamic Model with create_model in Python

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/models.md

Demonstrates basic dynamic model creation by specifying field names as types or (type, default) tuples.

```python
from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model('DynamicFoobarModel', foo=str, bar=(int, 123))

# Equivalent to:


class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
```

--------------------------------

### Install Flake8 Pydantic plugin

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/linting.md

Command to install the flake8-pydantic plugin using pip.

```bash
pip install flake8-pydantic
```

--------------------------------

### Run common development tasks with Make in Bash

Source: https://github.com/pydantic/pydantic/blob/main/pydantic-core/README.md

Lists commonly used Make targets for building development or production binaries, linting, formatting, and running test suites.

```bash
make build-dev    # to build the package during development
make build-prod   # to perform an optimised build for benchmarking
make test         # to run the tests
make testcov      # to run the tests and generate a coverage report
make lint         # to run the linter
make format       # to format python and rust code
make all          # to run to run build-dev + format + lint + test
```

--------------------------------

### Invalid Person Record Example in JSON

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Example JSON payload containing missing and invalid fields that trigger validation errors.

```json
{
    "age": -30,
    "email": "not-an-email-address"
}
```

--------------------------------

### Example of `WithJsonSchema` usage

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

This example demonstrates how to use `WithJsonSchema` to override the JSON Schema for a custom type, `MyInt`, and how it affects the generated schema for a Pydantic model.

```python
import json
from typing import Annotated

from pydantic import BaseModel, WithJsonSchema

MyInt = Annotated[
    int,
    WithJsonSchema({'type': 'integer', 'examples': [1, 0, -1]}),
]


class Model(BaseModel):
    a: MyInt


print(json.dumps(Model.model_json_schema(), indent=2))
```

```json
{
  "properties": {
    "a": {
      "examples": [
        1,
        0,
        -1
      ],
      "title": "A",
      "type": "integer"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
```

--------------------------------

### Field-Level JSON Schema Customization

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example of customizing JSON schema properties for fields using `Field()` parameters like `description`, `examples`, `title`, and `json_schema_extra`.

```python
import json
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, SecretStr


class User(BaseModel):
    age: int = Field(description='Age of the user')
    email: Annotated[EmailStr, Field(examples=['marcelo@mail.com'])]
    name: str = Field(title='Username')
    password: SecretStr = Field(
        json_schema_extra={
            'title': 'Password',
            'description': 'Password of the user',
            'examples': ['123456'],
        }
    )


print(json.dumps(User.model_json_schema(), indent=2))
"""
{
  "properties": {
    "age": {
      "description": "Age of the user",
      "title": "Age",
      "type": "integer"
    },
    "email": {
      "examples": [
        "marcelo@mail.com"
      ],
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "name": {
      "title": "Username",
      "type": "string"
    },
    "password": {
      "description": "Password of the user",
      "examples": [
        "123456"
      ],
      "format": "password",
      "title": "Password",
      "type": "string",
      "writeOnly": true
    }
  },
  "required": [
    "age",
    "email",
    "name",
    "password"
  ],
  "title": "User",
  "type": "object"
}
"""
```

--------------------------------

### Define sample TOML configuration file

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/files.md

Sample TOML file representing person configuration data.

```toml
name = "John Doe"
age = 30
email = "john@example.com"
```

--------------------------------

### Example Pydantic Model with Mypy Error Output

Source: https://github.com/pydantic/pydantic/blob/main/tests/mypy/README.md

The same Pydantic BaseModel example, showing how the Mypy output with an error message would be appended.

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int


model = Model(a=1, b=2)
# MYPY: error: Unexpected keyword argument "b" for "Model"  [call-arg]
```

--------------------------------

### Google-style Docstring Examples in Python

Source: https://github.com/pydantic/pydantic/blob/main/docs/contributing.md

Use these patterns for documenting classes and functions according to Google-style and PEP 257 guidelines. Types are inferred from signatures, so only descriptions are needed in the docstring.

```python
class Foo:
    """A class docstring.

    Attributes:
        bar: A description of bar. Defaults to "bar".
    """

    bar: str = 'bar'
```

```python
def bar(self, baz: int) -> str:
    """A function docstring.

    Args:
        baz: A description of `baz`.

    Returns:
        A description of the return value.
    """

    return 'bar'
```

--------------------------------

### Run formatting, linting, and tests

Source: https://github.com/pydantic/pydantic/blob/main/CONTRIBUTING.md

Run these commands to ensure your code adheres to formatting standards and passes all tests before submission.

```bash
# Run automated code formatting and linting
make format
# Pydantic uses ruff, an awesome Python linter written in Rust
# https://github.com/astral-sh/ruff

# Run tests and linting
make
# There are a few sub-commands in Makefile like `test`, `testcov` and `lint`
# which you might want to use, but generally just `make` should be all you need.
# You can run `make help` to see more options.
```

--------------------------------

### Implementing __get_pydantic_json_schema__

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example demonstrating how to modify or override the generated JSON schema by implementing the `__get_pydantic_json_schema__` class method, adding an 'examples' array and setting a custom 'title'.

```python
import json
from typing import Any

from pydantic_core import core_schema as cs

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter
from pydantic.json_schema import JsonSchemaValue


class Person:
    name: str
    age: int

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> cs.CoreSchema:
        return cs.typed_dict_schema(
            {
                'name': cs.typed_dict_field(cs.str_schema()),
                'age': cs.typed_dict_field(cs.int_schema()),
            },
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema['examples'] = [
            {
                'name': 'John Doe',
                'age': 25,
            }
        ]
        json_schema['title'] = 'Person'
        return json_schema


print(json.dumps(TypeAdapter(Person).json_schema(), indent=2))
```

```json
{
  "examples": [
    {
      "age": 25,
      "name": "John Doe"
    }
  ],
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
```

--------------------------------

### Define Incomplete JSON Input

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/experimental.md

Example of an incomplete JSON string input.

```json
'{"a": "hello", "b": "wor'
```

--------------------------------

### Define TypedDict Model

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/experimental.md

Example model structure for partial validation testing.

```python
from typing import TypedDict


class Model(TypedDict):
    a: str
    b: str
```

--------------------------------

### Implement UserIn and UserOut Pattern

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/experimental.md

Illustrates an alternative approach using plain Python classes and functions for data transformation, which may be more readable than complex pipeline definitions.

```python
from __future__ import annotations

from pydantic import BaseModel


class UserIn(BaseModel):
    favorite_number: int | str


class UserOut(BaseModel):
    favorite_number: int


def my_api(user: UserIn) -> UserOut:
    favorite_number = user.favorite_number
    if isinstance(favorite_number, str):
        favorite_number = int(user.favorite_number.strip())

    return UserOut(favorite_number=favorite_number)


assert my_api(UserIn(favorite_number=' 1 ')).favorite_number == 1
```

--------------------------------

### Config in class arguments (using keyword arguments)

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/visual_studio_code.md

Example of setting model configurations by passing keyword arguments directly when defining the model class.

```python
from pydantic import BaseModel


class Knight(BaseModel, frozen=True):
    title: str
    age: int
    color: str = 'blue'
```

--------------------------------

### Documenting Python Functions with Google-style Docstrings

Source: https://github.com/pydantic/pydantic/blob/main/CONTRIBUTING.md

Document function arguments and return values in the docstring. Use the 'Args' section for parameters and 'Returns' for the return value description.

```python
def bar(self, baz: int) -> str:
    """A function docstring.

    Args:
        baz: A description of `baz`.

    Returns:
        A description of the return value.
    """

    return 'bar'
```

--------------------------------

### Accessing Experimental Features

Source: https://github.com/pydantic/pydantic/blob/main/docs/version-policy.md

Example of importing an experimental feature from the `pydantic.experimental` module.

```python
from pydantic.experimental import feature_name
```

--------------------------------

### Define Pydantic model with boolean field

Source: https://github.com/pydantic/pydantic/blob/main/docs/internals/architecture.md

Example of a Pydantic model using a strict boolean field.

```python
from pydantic import BaseModel, Field


class Model(BaseModel):
    foo: bool = Field(strict=True)
```

--------------------------------

### Define a basic model with configuration in Python

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/models.md

Defines required and optional fields along with custom model configuration using ConfigDict. Fields with default values do not require input during model instantiation.

```python
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: int
    name: str = 'Jane Doe'

    model_config = ConfigDict(str_max_length=10)  # (1)!
```

--------------------------------

### Profile benchmark tests with flamegraph in Bash

Source: https://github.com/pydantic/pydantic/blob/main/pydantic-core/README.md

Runs a micro-benchmark using flamegraph and pytest to generate an interactive SVG flame graph. Requires building with profiling symbols enabled via make build-profiling.

```bash
flamegraph -- pytest tests/benchmarks/test_micro_benchmarks.py -k test_list_of_ints_core_py --benchmark-enable
```

--------------------------------

### Merging `json_schema_extra`

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example illustrating how Pydantic merges `json_schema_extra` dictionaries from annotated types, providing an additive approach.

```python
import json
from typing import Annotated, TypeAlias

from pydantic import Field, TypeAdapter

ExternalType: TypeAlias = Annotated[
    int, Field(json_schema_extra={'key1': 'value1'})
]

ta = TypeAdapter(
    Annotated[ExternalType, Field(json_schema_extra={'key2': 'value2'})]
)
print(json.dumps(ta.json_schema(), indent=2))
"""
{
  "key1": "value1",
  "key2": "value2",
  "type": "integer"
}
"""
```

--------------------------------

### Perform Model Validation and Serialization

Source: https://github.com/pydantic/pydantic/blob/main/docs/internals/architecture.md

Demonstrates using model_validate to populate a model instance and model_dump to serialize it back to a dictionary.

```python
from pydantic import BaseModel


class Model(BaseModel):
    foo: int


model = Model.model_validate({'foo': 1})  # (1)!
dumped = model.model_dump()  # (2)!
```

--------------------------------

### Inspect installed pydantic-core package files in Python

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/aws_lambda.md

Execute before failing imports to verify both the compiled shared library and type stubs are present.

```python
from importlib.metadata import files
print([file for file in files('pydantic-core') if file.name.startswith('_pydantic_core')])
"""
[PackagePath('pydantic_core/_pydantic_core.pyi'), PackagePath('pydantic_core/_pydantic_core.cpython-312-x86_64-linux-gnu.so')]
"""
```

--------------------------------

### Basic Forward Annotation Usage

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/forward_annotations.md

Demonstrates using `from __future__ import annotations` for forward references in Pydantic models.

```python
from __future__ import annotations

from pydantic import BaseModel

MyInt = int


class Model(BaseModel):
    a: MyInt
    # Without the future import, equivalent to:
    # a: 'MyInt'


print(Model(a='1'))
#> a=1
```

--------------------------------

### Customizing Core Schema with Annotated

Source: https://github.com/pydantic/pydantic/blob/main/docs/internals/architecture.md

Example of using __get_pydantic_core_schema__ to modify schema properties like strictness and constraints within an Annotated type.

```python
from typing import Annotated, Any

from pydantic_core import CoreSchema

from pydantic import GetCoreSchemaHandler, TypeAdapter


class MyStrict:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        schema = handler(source)  # (1)!
        schema['strict'] = True
        return schema


class MyGt:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        schema = handler(source)  # (2)!
        schema['gt'] = 1
        return schema


ta = TypeAdapter(Annotated[int, MyStrict(), MyGt()])
```

--------------------------------

### Example Model with Annotated Field

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/dynamic_models.md

A sample Pydantic model demonstrating the use of `Annotated` with `Field` for type-specific constraints and metadata.

```python
class Model(BaseModel):
    f: Annotated[int, Field(gt=1), WithJsonSchema({'extra': 'data'}), Field(title='F')] = 1
```

--------------------------------

### Instantiate a model with input data in Python

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/models.md

Instantiates the model while performing validation and type coercion. Raises a ValidationError if the provided data is invalid.

```python
user = User(id='123')
```

--------------------------------

### Correctly Specify Field Names in Pydantic Decorators

Source: https://github.com/pydantic/pydantic/blob/main/docs/errors/usage_errors.md

Fields should be provided as separate string arguments to `@field_validator` for correct usage, as shown in this example.

```python
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str
    b: str

    @field_validator('a', 'b')
    @classmethod
    def check_fields(cls, v):
        return v
```

--------------------------------

### Stdlib Type Configuration Propagation and Override

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/config.md

Demonstrates how configuration propagates to nested standard library types (dataclasses) unless the nested type explicitly sets its own configuration using `@with_config`.

```python
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, with_config


@dataclass
class UserWithoutConfig:
    name: str


@dataclass
@with_config(str_to_lower=False)
class UserWithConfig:
    name: str


class Parent(BaseModel):
    user_1: UserWithoutConfig
    user_2: UserWithConfig

    model_config = ConfigDict(str_to_lower=True)


print(Parent(user_1={'name': 'JOHN'}, user_2={'name': 'JOHN'}))
#> user_1=UserWithoutConfig(name='john') user_2=UserWithConfig(name='JOHN')
```

--------------------------------

### Customizing GenerateJsonSchema

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example of subclassing `GenerateJsonSchema` to customize the generated JSON schema, such as adding a custom title and schema dialect.

```python
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema


class MyGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode='validation'):
        json_schema = super().generate(schema, mode=mode)
        json_schema['title'] = 'Customize title'
        json_schema['$schema'] = self.schema_dialect
        return json_schema


class MyModel(BaseModel):
    x: int


print(MyModel.model_json_schema(schema_generator=MyGenerateJsonSchema))
```

```json
{
    "properties": {"x": {"title": "X", "type": "integer"}},
    "required": ["x"],
    "title": "Customize title",
    "type": "object",
    "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

--------------------------------

### Illustrate Required, Optional, and Nullable Fields in Pydantic V2

Source: https://github.com/pydantic/pydantic/blob/main/docs/migration.md

This example demonstrates the new behavior for required, optional, and nullable fields in Pydantic V2, including how `Optional[T]` fields are required by default if no default value is provided.

```python
from typing import Optional

from pydantic import BaseModel, ValidationError


class Foo(BaseModel):
    f1: str  # required, cannot be None
    f2: Optional[str]  # required, can be None - same as str | None
    f3: Optional[str] = None  # not required, can be None
    f4: str = 'Foobar'  # not required, but cannot be None


try:
    Foo(f1=None, f2=None, f4='b')
except ValidationError as e:
    print(e)
```

--------------------------------

### Named type aliases

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/types.md

Example of defining a named type alias using `Annotated` and `Len` for type hints.

```python
from typing import Annotated, TypeVar

from annotated_types import Len

type ShortList[T] = Annotated[list[T], Len(max_length=4)]
```

--------------------------------

### Demonstration of make_fields_optional factory function

Source: https://github.com/pydantic/pydantic/blob/main/docs/examples/dynamic_models.md

Shows how to use the `make_fields_optional` function to create a new model where all fields are optional and default to `None`.

```python
from pydantic import BaseModel, Field


class Model(BaseModel):
    a: Annotated[int, Field(gt=1)]


ModelOptional = make_fields_optional(Model)

m = ModelOptional()
print(m.a)
#> None
```

--------------------------------

### Using model_title_generator

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/json_schema.md

Example demonstrating the use of the `model_title_generator` config option to generate the title for the model itself, based on the model class.

```python
import json

from pydantic import BaseModel, ConfigDict


def make_title(model: type) -> str:
    return f'Title-{model.__name__}'


class Person(BaseModel):
    model_config = ConfigDict(model_title_generator=make_title)
    name: str
    age: int


print(json.dumps(Person.model_json_schema(), indent=2))
```

```json
{
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Title-Person",
  "type": "object"
}
```

--------------------------------

### Manually rebuild a TypeAdapter schema

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/type_adapter.md

Use defer_build=True to delay schema creation and call rebuild() once the necessary types are defined.

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter('MyInt', config=ConfigDict(defer_build=True))

# some time later, the forward reference is defined
MyInt = int

ta.rebuild()
assert ta.validate_python(1) == 1
```

--------------------------------

### Adding a default with Field

Source: https://github.com/pydantic/pydantic/blob/main/docs/integrations/visual_studio_code.md

Demonstrates how Pylance/pyright requires 'default' to be a keyword argument to 'Field' for proper inference of optional fields, highlighting a limitation with positional arguments.

```python
from pydantic import BaseModel, Field


class Knight(BaseModel):
    title: str = Field(default='Sir Lancelot')  # this is okay
    age: int = Field(
        23
    )  # this works fine at runtime but will case an error for pyright

lance = Knight()  # error: Argument missing for parameter "age"
```

--------------------------------

### Defining a Positive Integer Type

Source: https://github.com/pydantic/pydantic/blob/main/docs/concepts/types.md

Example of creating a reusable `PositiveInt` type using `Annotated` and `pydantic.Field` for validation.

```python
from typing import Annotated

from pydantic import Field, TypeAdapter, ValidationError

PositiveInt = Annotated[int, Field(gt=0)]  # (1)!

ta = TypeAdapter(PositiveInt)

print(ta.validate_python(1))
#> 1

try:
    ta.validate_python(-1)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for constrained-int
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```