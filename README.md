# Endstone Matchmaking

Generic matchmaking plugin for **Endstone** servers.

This plugin provides a simple queue and lobby system for a minigame server.  
Players can join a queue, be assigned to a lobby, leave the queue or lobby, and automatically start a game when enough players are available.

## Features

- `/exampleq01` command to join the queue
- `/leavelobby` command to leave the queue or current lobby
- Automatic lobby assignment
- Countdown before game start
- Leave-lobby item support
- Hub teleport when leaving or reconnecting
- External minigame plugin bridge through `Example`

## Requirements

- Python 3.10 or higher
- An Endstone server
- A minigame plugin named `Example` if you want automatic game start integration

## How it works

This plugin manages matchmaking for a generic minigame setup.

When a player uses `/exampleq01`, they are added to the matchmaking queue.  
If a lobby is available, they are moved into `ExampleLobby01`.  
When the minimum player count is reached, a countdown starts.  
When the countdown ends, the plugin checks whether a game is already running and then triggers the minigame plugin.

## Minigame integration

This plugin is designed to connect to another plugin called `Example`.

It expects the external plugin to expose:

- `example_manager`
- `example_manager.is_running`
- `example_manager.start_example()`

Example minimal structure for the linked minigame plugin:

```python
from endstone.plugin import Plugin


class ExampleManager:
    def __init__(self):
        self.is_running = False

    def start_example(self):
        self.is_running = True
        # Start the minigame here


class ExamplePlugin(Plugin):
    api_version = "0.10"

    def on_enable(self):
        self.example_manager = ExampleManager()
```

If your minigame plugin uses different names, you must update the matchmaking plugin accordingly.

## Commands

| Command | Description |
|---|---|
| `/exampleq01` | Join the Example queue |
| `/leavelobby` | Leave the current queue or lobby |

## Permissions

| Permission | Default | Description |
|---|---|---|
| `matchmaking.command.exampleq01` | `true` | Allows joining Example queue 01 |
| `matchmaking.command.leavelobby` | `true` | Allows leaving the current lobby |

## Default configuration

The public version of this plugin uses generic values:

- Queue tag: `exampleq01`
- Lobby name: `ExampleLobby01`
- Hub coordinates: `0, 0, 0`
- Lobby coordinates: `0, 0, 0`

You should update these values before using the plugin in production.

## Installation

### Development install

If you are developing the plugin locally, install it in editable mode:

```bash
pip install -e .
```

This allows you to update the code without reinstalling the package every time. The official Endstone Python example also recommends editable installation during development. [web:14]

### Build the plugin

To package the plugin as a wheel:

```bash
pip install pipx
pipx run build --wheel
```

This generates a `.whl` file in the `dist/` folder. Endstone’s install and publish tutorials use this build flow. [web:105][web:34]

### Install on the server

Copy the generated `.whl` file from `dist/` into your Endstone server `plugins` folder, then restart the server. Endstone’s install guide describes this wheel-based installation flow. [web:105]

## Project structure

Example structure:

```text
endstone-matchmaking/
├── LICENSE
├── README.md
├── pyproject.toml
└── src/
    └── enstone_matchmaking/
        ├── __init__.py
        └── ...
```

The official Endstone example plugin uses the same overall structure: source package under `src/`, plus `README.md`, `LICENSE`, and `pyproject.toml`. [web:14][web:24]

## pyproject.toml notes

Your `pyproject.toml` defines:

- project metadata
- package name
- version
- Python requirement
- Endstone entry point
- package discovery/build settings

The Endstone example plugin also defines metadata like `readme`, `license`, and authors in `pyproject.toml`. [web:24]

## Author

Original author: **TonNom**

You should also keep your name in:

- the `LICENSE` file
- the `pyproject.toml` `authors` field
- the top of the main Python source file

Example header:

```python
# Copyright (c) 2026 TonNom
# Author: TonNom
# Licensed under the terms described in LICENSE
```

## License

This plugin should be distributed with a `LICENSE` file at the root of the project.

If you are using a custom license, make sure it clearly explains:

- who the original author is
- whether modification is allowed
- whether redistribution is allowed
- whether commercial resale is forbidden

## Notes

- The plugin currently uses `get_plugin("Example")` to find the linked minigame plugin.
- If your linked plugin has a different name, update the code.
- If `example_manager` or `start_example()` does not exist, automatic game launch will not work.
- If your package folder is actually named `endstone_matchmaking` instead of `enstone_matchmaking`, you must also update the entry point in `pyproject.toml`.

## Publishing

When your plugin is ready, you can build it and publish it as a Python package. Endstone’s publishing tutorial uses `pipx run build` and `twine upload` for distribution to package indexes such as PyPI. [web:34]

## Documentation

Useful links:

- [Endstone Documentation](https://endstone.dev/latest/) [web:106]
- [Create your first plugin](https://endstone.dev/latest/tutorials/create-your-first-plugin/) [web:17]
- [Install your plugin](https://endstone.dev/v0.5.2/tutorials/install-your-plugin/) [web:105]
- [Publish your plugin](https://endstone.dev/latest/tutorials/publish-your-plugin/) [web:34]
