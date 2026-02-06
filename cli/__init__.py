import bpy
from . import (
    command_perf_ie,
)


cli_commands = []


if bpy.app.version >= (4, 2, 0):

    def register():
        for cmd_id, cmd_exec in (command_perf_ie.CMD,):
            cli_commands.append(bpy.utils.register_cli_command(cmd_id, cmd_exec))

    def unregister():
        for cmd in cli_commands:
            bpy.utils.unregister_cli_command(cmd)
        cli_commands.clear()
