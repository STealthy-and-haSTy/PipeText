import sublime
import sublime_plugin


### ---------------------------------------------------------------------------


class PipeCommandHistory():
    LIST_LIMIT = 50

    def __init__(self):
        self.storage = []

    def push(self, text, temp=False):
        self.del_duplicates(text)
        self.storage.insert(0, text)

        if len(self.storage) > self.LIST_LIMIT:
            del self.storage[self.LIST_LIMIT:]

    def del_duplicates(self, text):
        self.storage = [s for s in self.storage if s != text]

    def get(self):
        return self.storage

    def empty(self):
        return len(self.storage) == 0

_pipe_cmd_history = PipeCommandHistory()


### ---------------------------------------------------------------------------


class PipeTextWrapperCommand(sublime_plugin.WindowCommand):
    def run(self, working_dir=None):
        last_cmd = '' if _pipe_cmd_history.empty() else _pipe_cmd_history.get()[0]
        panel = self.window.show_input_panel('shell_cmd', last_cmd,
                                             lambda shell_cmd: self.execute(shell_cmd, working_dir),
                                             None, None)
        panel.settings().set('_pipe_cmd_input', True)
        panel.settings().set('_pipe_cmd_idx', 0)
        panel.run_command('select_all')

    def execute(self, shell_cmd, working_dir):
        _pipe_cmd_history.push(shell_cmd)
        self.window.run_command('pipe_text', {
            'shell_cmd': shell_cmd,
            'working_dir': working_dir
        })


### ---------------------------------------------------------------------------


class PipeTextHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit, prev=False):
        history = _pipe_cmd_history.get()

        cur_idx = self.view.settings().get("_pipe_cmd_idx", 0)
        cur_idx = (cur_idx + (-1 if prev else 1)) % len(history)
        self.view.settings().set("_pipe_cmd_idx", cur_idx)

        self.view.replace(edit, sublime.Region(0, len(self.view)), history[cur_idx])
        self.view.run_command('select_all')

    def is_enabled(self, prev=False):
        return len(_pipe_cmd_history.get()) > 1


### ---------------------------------------------------------------------------


class PipeTextEventListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == 'pipe_text_input':
            lhs = view.settings().get('_pipe_cmd_input', False)
            rhs = bool(operand)
            return lhs == rhs if operator == sublime.OP_EQUAL else lhs != rhs

        return None


### ---------------------------------------------------------------------------
