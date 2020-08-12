import sublime
import sublime_plugin
from subprocess import run, PIPE
from threading import Thread
import time
from datetime import datetime
import os
import sys


def execute_with_stdin(cmd, shell, cwd, text):
    before = time.perf_counter()
    # https://docs.python.org/3/library/subprocess.html#subprocess.run - new in version 3.5
    # therefore, this python file should be in your User package (which defaults to Python 3.8)
    # and you need to be using ST build >= 4050
    p = run(cmd, shell=shell, cwd=cwd, capture_output=True, input=text, encoding='utf-8')
    after = time.perf_counter()
    return (p, after - before)


def get_execution_action(cmd, shell_cmd):
    """ Determine what command to execute and whether or not the result should
        replace the selection or insert after it.
    """

    # Check to see if the command says to execute in place or not
    do_replace = True
    if shell_cmd and shell_cmd[0] == '!':
        shell_cmd = shell_cmd[1:]
        do_replace = False
    elif cmd and cmd[0][0] == '!':
        cmd[0] = cmd[0][1:]
        do_replace = False

    # this shell_cmd/cmd logic was borrowed from Packages/Default/exec.py
    if shell_cmd:
        if sys.platform == "win32":
            # Use shell=True on Windows, so shell_cmd is passed through
            # with the correct escaping
            cmd = shell_cmd
            shell = True
        else:
            cmd = ["/usr/bin/env", "bash", "-c", shell_cmd]
            shell = False
    else:
        shell = False

    return shell, cmd, do_replace


class PipeTextCommand(sublime_plugin.TextCommand):
    """Pipe text from ST - the selections, if any, otherwise the entire buffer contents
       - to the specified shell command.
       Useful for formatting XML or JSON in a quick and easy manner.
       i.e. a workaround for https://github.com/sublimehq/sublime_text/issues/3294
       This command requires Python >= 3.5, and therefore, ST build >= 4050, and for the
       package to have opted in to the Python 3.8 plugin host. (The User package is
       automatically opted-in.)
    """
    def run(self, edit, cmd=None, shell_cmd=None, working_dir=None):
        if not shell_cmd and not cmd:
            raise ValueError("shell_cmd or cmd is required")

        if shell_cmd and not isinstance(shell_cmd, str):
            raise ValueError("shell_cmd must be a string")

        shell, cmd, do_replace = get_execution_action(cmd, shell_cmd)

        # if not all selections are non-empty
        if not all(self.view.sel()) and do_replace:
            # use the entire buffer instead of the selections
            regions = [sublime.Region(0, self.view.size())]
        else:
            # use the user's selections
            regions = self.view.sel()

        if not working_dir and self.view.file_name():
            working_dir = os.path.dirname(self.view.file_name())

        thread = Thread(
            target=self.execute,
            args=(cmd, shell, working_dir, regions, do_replace))
        thread.start()

    def execute(self, cmd, shell, working_dir, regions,do_replace):
        failures = False
        start = time.perf_counter()
        logs = list()
        def log(message):
            nonlocal logs
            log_text = str(datetime.now()) + ' ' + message
            logs.append(log_text)
            print(log_text)

        # TODO: the commands could take a while to execute, and it may be an idea to not block the ui
        # - so maybe just mark the buffer as read only until they complete and do the replacements async
        # maybe even with some phantoms or annotations near the selections to tell the user what is going on

        for region in reversed(regions):
            text = self.view.substr(region)

            p, time_elapsed = execute_with_stdin(cmd, shell, working_dir, text)

            # TODO: also report the selection index?
            log(f'command "{cmd!r}" executed with return code {p.returncode} in {time_elapsed * 1000:.3f}ms')

            if p.returncode == 0:
                self.view.run_command('pipe_text_action', {
                    'region': [region.a, region.b],
                    'data': p.stdout,
                    'do_replace': do_replace
                    })
            else:
                failures = True
                log(p.stderr.rstrip())

        total_elapsed = time.perf_counter() - start
        if failures:
            sublime.error_message('\n'.join(logs)) # TODO: don't include the datetimes here?
        else:
            sublime.status_message(f'text piped and replaced successfully in {total_elapsed * 1000:.3f}ms')


class PipeTextActionCommand(sublime_plugin.TextCommand):
    def run(self, edit, region, data, do_replace):
        region = sublime.Region(region[0], region[1])
        if do_replace:
            self.view.replace(edit, region, data)
        else:
            self.view.insert(edit, region.b, data)


# example for pretty printing XML using xmllint:
# TODO: option for no xml prolog when working with selections? https://stackoverflow.com/q/37118327/4473405
#view.run_command('pipe_text', { 'cmd': ['xmllint', '--format', '-'] })

# example for pretty printing JSON using jq:
#view.run_command('pipe_text', { 'cmd': ['jq', '.'] })

#view.run_command('pipe_text', {"shell_cmd": "sort | uniq"})