# Endstone Matchmaking

Generic matchmaking plugin for **Endstone** servers.

This plugin provides a simple queue and lobby system for a mini-game server.
Players can join a queue, be assigned to a lobby, leave the queue or lobby using an item, and automatically start a game when a sufficient number of players are available.

## Features

- `/exampleq01` command to join the queue (executable by an entity)
- `/leavelobby` command to leave the queue or current lobby (currently executed by the player via an item)
- Automatic lobby assignment
- Countdown before game start
- Leave-lobby item support
- Hub teleport when leaving or reconnecting
- Potential bridge to an external mini-game plugin to notify it that a game is in progress

## Requirements

- Python 3.10 or higher
- An Endstone server

## Minigame integration

This plugin is designed to connect to another plugin; otherwise, it will not be able to determine whether a game is in progress.

You simply need to replace the command name and the lobby name, correctly configure the HUD and lobby coordinates, and then repeat the process for each mini-game.

## In Development

This plugin is still under development; bugs may be discovered. Please report them to us.
