# PipeText

A package for Sublime Text that allows you to execute arbitrary shell commands,
shipping the selected text or the whole buffer to the command's `stdin` and
replacing or inserting the result of the command in the buffer.

This is still in active development at the moment. Stay tuned!

This package is a modified version of [pipe_text.py](https://github.com/STealthy-and-haSTy/SublimeScraps/blob/master/plugins/pipe_text.py),
enhanced with some extra functionality and some additional resource file glue.


# Installing

This package requires Sublime Text 4050 or greater because it takes advantage of
features added in Python version 3.5.

To install, clone this repository into your `Packages` folder.

# Usage

The package implements a `pipe_text` command:

```python
self.view.run_command('pipe_text', {
    "cmd": None,        # the cmd to execute
    "shell_cmd": None,  # A script to execute in a shell
    "working_dir": None # The working directory
    })
```

`pipe_text` gathers the contents of all selections (or if not all selections are
non-empty, the contents of the entire buffer), executes the command you provide
and replaces the selected text with the result of the command.

If a `working_dir` is not provided, the path of the currently open file is used,
if any.

The first character of `shell_cmd` or the first character in the first argument
to `cmd` can optionally be a `!` character; in this case the command operates as
above, but the result of the command is inserted into the buffer instead of
replacing the input text.

In addition to the above, there is also a `pipe_text_wrapper` command:

```python
self.view.run_command('pipe_text_wrapper', {
    "working_dir": None # The working directory
    })
```

This command will open the input panel and prompt you interactively for the
command to execute. The input panel maintains a command history of previously
used commands, allowing you to easily re-use previous commands.

Currently, the command history is not persisted between sessions.


# Future features

- Use an input handler to enter a command via the command palette.
- Allow the user to cancel a running command if it takes too long
- Include a spinner in the status bar while external commands are running
- Optionally execute all commands first and perform insertions all at once
- Persist the command history between sessions
