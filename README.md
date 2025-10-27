# human errors

humans do make some errors, so we should show it to them, so that it can be fixed

## usage:

### json/orjson

```py
from human_errors import json_dump
import orjson

try:
  with open("config.json", "r") as file:
    config = orjson.loads(file.read())
except orjson.JSONDecodeError as exc:
  json_dump(exc, "config.json")
```

Output (error):
```
    --> C:\Users\<user>\absolute\path\to\config.json:19:5
  17 │       "path": "$DESKTOP"
  18 │     }
╭╴19 │     {
│    │     ↑
│ 20 │       "name": "Pictures",
│ 21 │       "path": "$PICTURES"
╰────❯ unexpected character
```

### tomllib (>=3.14) or toml
if you want to use tomllib, python >= 3.14 must be used so that the message and line + column numbers can be extracted.
```py
from human_errors import toml_dump
import toml
try:
  with open("pyproject.toml", "r") as file:
    config = toml.loads(file.read())
except toml.TomlDecodeError as exc:
  toml_dump(exc, "pyproject.toml")
```

Output (error):
```
    --> C:\Users\<user>\path\to\pyproject.toml:9:26
   7 │     { name = "<name>", email = "<email>" }
   8 │ ]
╭╴ 9 │ requires-python = ">=3.12
│    │                          ↑
│ 10 │ dependencies = [
│ 11 │     "rich>=14.2.0",
╰────❯ Unbalanced quotes
```

### Base Renderer (Custom Errors)

For custom error handling or any file-based errors not covered by the built-in renderers:

```py
from human_errors.base_renderer import dump

def validate_config(file_path: str):
    with open(file_path, "r") as f:
        for line_num, line in enumerate(f, start=1):
            if "TODO" in line:
                col = line.index("TODO") + 1
                dump(
                    doc_path=file_path,
                    cause="TODO found in production config",
                    line_number=line_num,
                    column_number=col,
                    context=3,
                    extra=[
                        "Production configs should not contain TODO items",
                        "Please replace with actual values or remove this entry"
                    ]
                )
                exit(1)
```

Output (error):
```
     --> C:\Users\<user>\absolute\path\to\config.py:15:9
  12 │ DATABASE_HOST = "localhost"
  13 │ DATABASE_PORT = 5432
  14 │
╭╴15 │ API_KEY = "TODO: add production key"
│    │            ↑
│ 16 │
│ 17 │ CACHE_ENABLED = True
│ 18 │ CACHE_TTL = 3600
╰─────❯ TODO found in production config
    ╭───────────────────────────────────────────────────────────╮
    │ Production configs should not contain TODO items          │
    ├───────────────────────────────────────────────────────────┤
    │ Please replace with actual values or remove this entry    │
    ╰───────────────────────────────────────────────────────────╯
```

more soon i guess

## contributing

any extra data format must be in an extra, and also available in the `all` group

any contributions must pre-lint with `ruff` and `ty`

```sh
uv run ruff check --unsafe-fixes --fix
uv run ty check
```

adding support for pytest is also fine

<div align="center">
  <h1>（￣︶￣）↗ give a star</h1>
</div>
