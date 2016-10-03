 #!/usr/bin/python
from acorn import msg
def examples():
    """Prints examples of using the script to the console using colored output.
    """
    script = "ACORN Automatic Computational Research Notebook"
    explain = ("Research involves repeated testing of hypotheses; for "
               "computational research, these \"experiments\" have a rapid "
               "turnover time so that several hundred could happen in a single "
               "day. ACORN automatically generates research notebooks from "
               "such experimentation within the context of an `ipython` "
               "notebook.\n\nThis script configures the ACORN backend.")
    contents = [(("Create a custom configuration folder for packages that "
                  "ship with ACORN."), 
                 "acrn.py configure packages",
                 "This creates a `~/.acorn` directory with copies of all the "
                 "default package configuration and descriptor files. You can "
                 "edit the configurations by opening the files from that "
                 "folder.")]
    required = ("")
    output = ("")
    details = ("")
    outputfmt = ("")

    msg.example(script, explain, contents, required, output, outputfmt, details)

script_options = {
    "commands": {"nargs": "+",
                 "help": "List of commands and sub-commands to run."},
    }
"""dict: default command-line arguments and their
    :meth:`argparse.ArgumentParser.add_argument` keyword arguments.
"""

def _parser_options():
    """Parses the options and arguments from the command line."""
    #We have two options: get some of the details from the config file,
    import argparse
    from acorn import base
    pdescr = "ACORN setup and custom configuration"
    parser = argparse.ArgumentParser(parents=[base.bparser], description=pdescr)
    for arg, options in script_options.items():
        parser.add_argument(arg, **options)
        
    args = base.exhandler(examples, parser)
    if args is None:
        return

    return args

def _conf_packages(args):
    """Runs custom configuration steps for the packages that ship with support
    in acorn.
    """
    from acorn.config import config_dir
    from os import path
    target = config_dir(True)
    alternate = path.join(path.abspath(path.expanduser("~")), ".acorn")
    if target != alternate:
        msg.err("Could not configure custom ~/.acorn directory.")
        exit(0)

    from acorn.utility import reporoot
    from glob import glob
    from os import chdir, getcwd
    from shutil import copy
    current = getcwd()
    source = path.join(reporoot, "acorn", "config")
    chdir(source)
    count = 0
    
    for json in glob("*.json"):
        copy(json, target)
        count += 1
    for cfg in glob("*.cfg"):
        copy(cfg, target)
        count += 1

    msg.okay("Copied {0:d} package files to {1}.".format(count, target))
    
def _run_configure(subcmd, args):
    """Runs the configuration step for the specified sub-command.
    """
    maps = {
        "packages": _conf_packages
        }
    if subcmd in maps:
        maps[subcmd](args)
    else:
        msg.warn("'configure' sub-command {} is not supported.".format(subcmd))

def run(args):
    """Runs the acorn setup/configuration commands.
    """
    cmd = args["commands"][0]
    if cmd == "configure":
        if len(args["commands"]) < 2:
            msg.err("'configure' command requires a second, sub-command "
                    "parameter. E.g., `acorn.py configure packages`.")
            exit(0)

        subcmd = args["commands"][1]
        _run_configure(subcmd, args)

if __name__ == '__main__': # pragma: no cover
    run(_parser_options())
