# Copyright (c) 2026 ObiDev-Studios
# Author: ObiDev-Studios
# Licensed under the terms described in LICENSE.txt

from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.event import (
    event_handler,
    PlayerJoinEvent,
    PlayerQuitEvent,
    PlayerInteractEvent,
)
from endstone.level import Location


class Matchmaking(Plugin):
    api_version = "0.10"

    commands = {
        "exampleq01": {
            "description": "Join Example queue 01.",
            "usages": ["/exampleq01"],
            "permissions": ["matchmaking.command.exampleq01"],
        },
        "leavelobby": {
            "description": "Leave your current lobby.",
            "usages": ["/leavelobby"],
            "permissions": ["matchmaking.command.leavelobby"],
        },
    }

    permissions = {
        "matchmaking.command.exampleq01": {
            "description": "Allows joining Example queue 01.",
            "default": True,
        },
        "matchmaking.command.leavelobby": {
            "description": "Allows leaving the current lobby.",
            "default": True,
        },
    }

    QUEUE_TAG = "exampleq01"
    LEAVE_LOBBY_ITEM = "matchmaking:leave_lobby"
    LEAVE_LOBBY_SLOT = 8

    MAX_PLAYERS = 8
    MIN_PLAYERS = 2
    COUNTDOWN_SECONDS = 30

    HUB = (0, 0, 0)
    EXAMPLE_START_LOBBY = "ExampleLobby01"

    def on_enable(self):
        self.queue_players = set()
        self.pending_hub_tp = set()
        self.lobbies = {
            self.EXAMPLE_START_LOBBY: {
                "coords": (0, 0, 0),
                "players": set(),
                "state": "WAITING",
                "countdown": None,
            },
        }

        self.server.scheduler.run_task(
            self,
            self.monitor_example_lobby,
            delay=200,
            period=200,
        )

        self.dispatch_console_command("gamerule showtags false")

        self.register_events(self)
        self.logger.info("§a[Matchmaking] Plugin enabled.")

    def on_disable(self):
        self.logger.info("§c[Matchmaking] Plugin disabled.")

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not hasattr(sender, "name"):
            sender.send_message("§cThis command can only be used by a player.")
            return True

        player = sender

        if command.name == "exampleq01":
            if self.is_player_in_any_lobby(player.name):
                self.send_actionbar(player.name, "§cYou are already in a lobby.")
                return True

            if player.name in self.queue_players:
                self.send_actionbar(player.name, "§eYou are already in queue.")
                return True

            self.add_tag(player.name, self.QUEUE_TAG)
            self.queue_players.add(player.name)
            self.send_actionbar(player.name, "§aSearching for a lobby...")
            self.try_assign_player_to_lobby(player.name)
            return True

        if command.name == "leavelobby":
            return self.handle_leave_request(player.name)

        return False

    def handle_leave_request(self, player_name: str) -> bool:
        if player_name in self.queue_players:
            self.remove_tag(player_name, self.QUEUE_TAG)
            self.queue_players.discard(player_name)
            self.remove_leave_lobby_item(player_name)
            x, y, z = self.HUB
            self.teleport_player(player_name, x, y, z)
            self.log_lobby_leave(player_name, None, "left queue")
            self.send_actionbar(player_name, "§7You left the queue.")
            return True

        lobby_name = self.get_player_lobby(player_name)
        if lobby_name is None:
            self.send_actionbar(player_name, "§cYou are not in a lobby.")
            return True

        self.leave_lobby(player_name, lobby_name, "manual leave")
        return True

    def get_online_player(self, player_name: str):
        return self.server.get_player(player_name)

    def send_actionbar(self, player_name: str, message: str):
        player = self.get_online_player(player_name)
        if player is not None:
            player.send_tip(message)

    def send_start_title(self, player_name: str):
        player = self.get_online_player(player_name)
        if player is not None:
            player.send_title("§aStarting...", "", 0, 20, 10)

    def play_countdown_sound(self, player_name: str):
        player = self.get_online_player(player_name)
        if player is not None:
            player.play_sound(player.location, "random.orb", 1.0, 1.2)

    def log_lobby_join(self, player_name: str, lobby_name: str):
        self.logger.info(f"§a[Matchmaking] {player_name} joined {lobby_name}")

    def log_lobby_leave(self, player_name: str, lobby_name: str | None, reason: str):
        if lobby_name is None:
            self.logger.info(f"§6[Matchmaking] {player_name} left matchmaking ({reason})")
        else:
            self.logger.info(f"§6[Matchmaking] {player_name} left {lobby_name} ({reason})")

    def log_lobby_start(self, lobby_name: str, player_count: int):
        self.logger.info(f"§9[Matchmaking] {lobby_name} is starting with {player_count} players")

    def get_example_plugin(self):
        # Used to detect whether a match is currently running.
        # Link this to your minigame plugin.
        return self.server.plugin_manager.get_plugin("Example")

    def has_active_example_game(self) -> bool:
        # This section is used to know if a game is already in progress.
        # You need to connect it to the plugin that manages your minigame.
        example_plugin = self.get_example_plugin()

        if example_plugin is None:
            return False

        if not hasattr(example_plugin, "example_manager"):
            return False

        manager = example_plugin.example_manager
        if manager is None:
            return False

        return bool(manager.is_running)

    def has_tag(self, player_name: str, tag: str) -> bool:
        player = self.get_online_player(player_name)
        if player is None:
            return False
        return tag in player.scoreboard_tags

    def add_tag(self, player_name: str, tag: str):
        player = self.get_online_player(player_name)
        if player is None:
            return

        if tag in player.scoreboard_tags:
            return

        player.add_scoreboard_tag(tag)

    def remove_tag(self, player_name: str, tag: str):
        player = self.get_online_player(player_name)
        if player is None:
            return

        if tag not in player.scoreboard_tags:
            return

        player.remove_scoreboard_tag(tag)

    def teleport_player(self, player_name: str, x: int, y: int, z: int):
        player = self.get_online_player(player_name)
        if player is None:
            return

        current = player.location
        destination = Location(
            current.dimension,
            float(x),
            float(y),
            float(z),
            float(current.pitch),
            float(current.yaw),
        )
        player.teleport(destination)

    def dispatch_console_command(self, command_line: str) -> bool:
        return self.server.dispatch_command(self.server.command_sender, command_line)

    def quote_target(self, player_name: str) -> str:
        return f'"{player_name}"'

    def give_leave_lobby_item(self, player_name: str):
        target = self.quote_target(player_name)
        command = (
            f'replaceitem entity {target} slot.hotbar {self.LEAVE_LOBBY_SLOT} '
            f'{self.LEAVE_LOBBY_ITEM} 1 0 '
            f'{{"minecraft:item_lock":{{"mode":"lock_in_slot"}}}}'
        )
        self.dispatch_console_command(command)

    def remove_leave_lobby_item(self, player_name: str):
        target = self.quote_target(player_name)
        command = f"replaceitem entity {target} slot.hotbar {self.LEAVE_LOBBY_SLOT} air"
        self.dispatch_console_command(command)

    def get_held_item_type(self, player_name: str):
        player = self.get_online_player(player_name)
        if player is None:
            return None

        held_slot = player.inventory.held_item_slot
        held_item = player.inventory.get_item(held_slot)

        if held_item is None:
            return None

        return getattr(held_item, "type", None)

    def monitor_example_lobby(self):
        lobby_name = self.EXAMPLE_START_LOBBY
        lobby = self.lobbies.get(lobby_name)

        if lobby is None:
            return

        if self.has_active_example_game():
            lobby["state"] = "IN_GAME"
            lobby["countdown"] = None
            return

        if lobby["state"] == "IN_GAME":
            lobby["state"] = "WAITING"
            lobby["countdown"] = None
            self.broadcast_lobby_actionbar(lobby_name, "§aThe lobby is available again.")
            self.check_lobby_start(lobby_name)

    def delayed_start_example(self):
        if self.has_active_example_game():
            return

        example_plugin = self.get_example_plugin()
        if example_plugin is None:
            self.logger.warning("[Matchmaking] Plugin 'Example' not found.")
            self.logger.warning("[Matchmaking] This plugin must be linked to your minigame plugin.")
            return

        if not hasattr(example_plugin, "example_manager"):
            self.logger.warning("[Matchmaking] example_manager not found on plugin 'Example'.")
            self.logger.warning("[Matchmaking] This part is used to know if a game is already running.")
            return

        manager = example_plugin.example_manager
        if manager is None:
            self.logger.warning("[Matchmaking] example_manager is None on plugin 'Example'.")
            return

        manager.start_example()

        for player_name in list(self.lobbies[self.EXAMPLE_START_LOBBY]["players"]):
            self.remove_leave_lobby_item(player_name)

        self.lobbies[self.EXAMPLE_START_LOBBY]["players"].clear()

    def try_assign_player_to_lobby(self, player_name: str):
        available_lobbies = []

        for lobby_name, lobby_data in self.lobbies.items():
            if len(lobby_data["players"]) < self.MAX_PLAYERS:
                available_lobbies.append((lobby_name, len(lobby_data["players"])))

        if not available_lobbies:
            self.send_actionbar(player_name, "§eWaiting for an available lobby...")
            return

        available_lobbies.sort(key=lambda entry: entry[1], reverse=True)
        selected_lobby = available_lobbies[0][0]
        self.move_player_to_lobby(player_name, selected_lobby)

    def move_player_to_lobby(self, player_name: str, lobby_name: str):
        lobby = self.lobbies[lobby_name]

        self.remove_tag(player_name, self.QUEUE_TAG)
        self.queue_players.discard(player_name)

        self.add_tag(player_name, lobby_name)
        lobby["players"].add(player_name)
        self.give_leave_lobby_item(player_name)
        self.log_lobby_join(player_name, lobby_name)

        x, y, z = lobby["coords"]
        self.teleport_player(player_name, x, y, z)

        if lobby_name == self.EXAMPLE_START_LOBBY and self.has_active_example_game():
            lobby["state"] = "IN_GAME"
            lobby["countdown"] = None
            self.send_actionbar(player_name, "§eGame already in progress, please wait...")
            return

        self.send_actionbar(player_name, f"§bJoined {lobby_name}")
        self.check_lobby_start(lobby_name)

    def check_lobby_start(self, lobby_name: str):
        lobby = self.lobbies[lobby_name]

        if lobby_name == self.EXAMPLE_START_LOBBY and self.has_active_example_game():
            lobby["state"] = "IN_GAME"
            lobby["countdown"] = None
            return

        if lobby["state"] == "IN_GAME":
            lobby["state"] = "WAITING"

        if lobby["state"] != "WAITING":
            return

        if len(lobby["players"]) >= self.MIN_PLAYERS:
            lobby["state"] = "STARTING"
            lobby["countdown"] = self.COUNTDOWN_SECONDS
            self.run_lobby_countdown(lobby_name)

    def run_lobby_countdown(self, lobby_name: str):
        lobby = self.lobbies[lobby_name]

        if lobby["state"] != "STARTING":
            return

        if len(lobby["players"]) < self.MIN_PLAYERS:
            lobby["state"] = "WAITING"
            lobby["countdown"] = None
            self.broadcast_lobby_actionbar(lobby_name, "§cStart cancelled.")
            return

        if lobby_name == self.EXAMPLE_START_LOBBY and self.has_active_example_game():
            lobby["state"] = "IN_GAME"
            lobby["countdown"] = None
            self.broadcast_lobby_actionbar(lobby_name, "§eA game is already in progress...")
            return

        seconds = lobby["countdown"]
        if seconds is None:
            return

        if seconds > 0:
            self.broadcast_lobby_actionbar(lobby_name, f"§eStarting in {seconds}")

            if seconds <= 5:
                self.broadcast_lobby_sound(lobby_name)

            lobby["countdown"] -= 1
            self.server.scheduler.run_task(
                self,
                lambda: self.run_lobby_countdown(lobby_name),
                delay=20,
            )
            return

        lobby["state"] = "IN_GAME"
        lobby["countdown"] = None
        self.log_lobby_start(lobby_name, len(lobby["players"]))

        for player_name in list(lobby["players"]):
            self.send_start_title(player_name)

        if lobby_name == self.EXAMPLE_START_LOBBY:
            self.server.scheduler.run_task(
                self,
                self.delayed_start_example,
                delay=40,
            )

    def broadcast_lobby_actionbar(self, lobby_name: str, message: str):
        lobby = self.lobbies[lobby_name]
        for player_name in list(lobby["players"]):
            if self.get_online_player(player_name) is not None:
                self.send_actionbar(player_name, message)

    def broadcast_lobby_sound(self, lobby_name: str):
        lobby = self.lobbies[lobby_name]
        for player_name in list(lobby["players"]):
            if self.get_online_player(player_name) is not None:
                self.play_countdown_sound(player_name)

    def is_player_in_any_lobby(self, player_name: str) -> bool:
        for lobby_data in self.lobbies.values():
            if player_name in lobby_data["players"]:
                return True
        return False

    def get_player_lobby(self, player_name: str):
        for lobby_name, lobby_data in self.lobbies.items():
            if player_name in lobby_data["players"]:
                return lobby_name
        return None

    def leave_lobby(self, player_name: str, lobby_name: str, reason: str = "manual leave"):
        lobby = self.lobbies.get(lobby_name)
        if lobby is None:
            return

        lobby["players"].discard(player_name)
        self.remove_tag(player_name, lobby_name)
        self.remove_leave_lobby_item(player_name)
        self.log_lobby_leave(player_name, lobby_name, reason)

        if lobby["state"] == "STARTING" and len(lobby["players"]) < self.MIN_PLAYERS:
            lobby["state"] = "WAITING"
            lobby["countdown"] = None
            self.broadcast_lobby_actionbar(
                lobby_name,
                "§cA player left, start cancelled."
            )

        if lobby["state"] == "IN_GAME" and len(lobby["players"]) == 0:
            lobby["state"] = "WAITING"
            lobby["countdown"] = None

        x, y, z = self.HUB
        self.teleport_player(player_name, x, y, z)
        self.send_actionbar(player_name, "§7Returned to hub.")

    def remove_player_from_system(self, player_name: str):
        self.queue_players.discard(player_name)
        self.remove_tag(player_name, self.QUEUE_TAG)
        self.remove_leave_lobby_item(player_name)

        lobby_name = self.get_player_lobby(player_name)
        if lobby_name is None:
            return

        lobby = self.lobbies[lobby_name]
        lobby["players"].discard(player_name)
        self.remove_tag(player_name, lobby_name)
        self.log_lobby_leave(player_name, lobby_name, "disconnect")

        if lobby["state"] == "STARTING" and len(lobby["players"]) < self.MIN_PLAYERS:
            lobby["state"] = "WAITING"
            lobby["countdown"] = None
            self.broadcast_lobby_actionbar(
                lobby_name,
                "§cA player left, start cancelled."
            )

        if lobby["state"] == "IN_GAME" and len(lobby["players"]) == 0:
            lobby["state"] = "WAITING"
            lobby["countdown"] = None

    def clear_known_tags(self, player_name: str):
        self.remove_tag(player_name, self.QUEUE_TAG)
        for lobby_name in self.lobbies.keys():
            self.remove_tag(player_name, lobby_name)

    @event_handler
    def on_player_interact(self, event: PlayerInteractEvent):
        player = event.player
        item_type = self.get_held_item_type(player.name)

        if item_type != self.LEAVE_LOBBY_ITEM:
            return

        self.handle_leave_request(player.name)

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        player_name = event.player.name
        was_in_queue = player_name in self.queue_players
        was_in_lobby = self.get_player_lobby(player_name) is not None

        if was_in_queue or was_in_lobby:
            self.pending_hub_tp.add(player_name)

        self.remove_player_from_system(player_name)

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        player_name = event.player.name

        if player_name in self.pending_hub_tp:
            self.clear_known_tags(player_name)
            x, y, z = self.HUB
            self.teleport_player(player_name, x, y, z)
            self.send_actionbar(player_name, "§7Returned to hub.")
            self.pending_hub_tp.discard(player_name)
            return

        if self.is_player_in_any_lobby(player_name):
            self.give_leave_lobby_item(player_name)
        else:
            self.remove_leave_lobby_item(player_name)

# Copyright (c) 2026 ObiDev-Studios
# Author: ObiDev-Studios
# Licensed under the terms described in LICENSE.txt           