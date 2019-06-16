import util
import faceit_tasker
import faceit_commands



def register(client):
    util.start_task_thread(faceit_tasker.elo_notifier_task(client))
    return {
        'faceit': faceit_commands.cmd_faceit_commands,
    }

