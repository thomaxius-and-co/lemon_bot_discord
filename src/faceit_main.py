import faceit_tasker
import faceit_commands


def register(client):
    return {
        'faceit': faceit_commands.cmd_faceit_commands,
    }

