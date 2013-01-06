# -*- coding: utf-8 -*-
# Author: Guido D'Albore
# Official Repository: https://github.com/setumiami/sublime-text-2-typescript
# CommandThread class is based on Git sublime package (https://github.com/kemayo/sublime-text-2-git)

import sublime, sublime_plugin
import os
import subprocess 
import threading
import functools
import tempfile

class TypescriptCommand(sublime_plugin.TextCommand): 
    def run(self, edit):
        print("TypeScript Compiler running...")
        print("Working dir: %s" % self.get_working_dir())

        source = self.get_content();
        print("%s" % source);
        
        self.compile(str(source))
        
        print("TypeScript Compiler finished.")

    def get_content(self):
        view = self.view
        regions = view.sel()

        if len(regions) > 1 or not regions[0].empty():
                return view.substr(regions[0]);
        else: 
                view_content = sublime.Region(0, view.size())
                return view.substr(view_content)

    def compile(self, source):
        print source
        # Create TypeScript source file
        f = tempfile.NamedTemporaryFile(prefix = 'tsc_', suffix = '.ts', delete = False)
        self.sourcefile = f
        self.sourcefile.write(source)
        self.sourcefile.close()
        print "Source TypeScript file: %s" % self.sourcefile.name

        # Create JavaScript destination file
        f = tempfile.NamedTemporaryFile(prefix = 'tsc_', suffix = '.js', delete = False)
        self.destinationfile = f
        self.destinationfile.write(source)
        self.destinationfile.close()
        print "Source TypeScript file: %s" % self.destinationfile.name

        commandline = [ '/usr/local/bin/node', 
                        '/usr/local/share/npm/bin/tsc',
                        '--out',
                        self.destinationfile.name,
                        self.sourcefile.name];

        command = CommandThread(commandline, self.onDone, self.get_working_dir())
        command.start()

    def get_working_dir(self):
        file_name = None

        view = self.view

        if view and view.file_name() and len(view.file_name()) > 0:
            file_name = view.file_name()

        if file_name:
            return os.path.realpath(os.path.dirname(file_name))
        else:
            try:  # handle case with no open folder
                return self.window.folders()[0]
            except IndexError:
                return ''

    def onDone(self, result):
        sublime.active_window().open_file(self.destinationfile.name)
        sublime.active_window().active_view().set_syntax_file("Packages/JavaScript/JavaScript.tmLanguage")
        print("onDone called...")
        print(result)

def main_thread(callback, *args, **kwargs):
    # sublime.set_timeout gets used to send things onto the main thread
    # most sublime.[something] calls need to be on the main thread
    sublime.set_timeout(functools.partial(callback, *args, **kwargs), 0)

def _make_text_safeish(text, fallback_encoding, method='decode'):
    # The unicode decode here is because sublime converts to unicode inside
    # insert in such a way that unknown characters will cause errors, which is
    # distinctly non-ideal... and there's no way to tell what's coming out of
    # git in output. So...
    try:
        unitext = getattr(text, method)('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        unitext = getattr(text, method)(fallback_encoding)
    return unitext

# CommandThread comes from Git sublime package
# Thanks to @kemaio on https://github.com/kemayo/sublime-text-2-git
class CommandThread(threading.Thread):
    def __init__(self, command, on_done, working_dir="", fallback_encoding="", **kwargs):
        threading.Thread.__init__(self)
        self.command = command
        self.on_done = on_done
        self.working_dir = working_dir
        if "stdin" in kwargs:
            self.stdin = kwargs["stdin"]
        else:
            self.stdin = None
        if "stdout" in kwargs:
            self.stdout = kwargs["stdout"]
        else:
            self.stdout = subprocess.PIPE
        self.fallback_encoding = fallback_encoding
        self.kwargs = kwargs

    def run(self):
        try:

            # Ignore directories that no longer exist
            if os.path.isdir(self.working_dir):

                # Per http://bugs.python.org/issue8557 shell=True is required to
                # get $PATH on Windows. Yay portable code.
                shell = os.name == 'nt'
                if self.working_dir != "":
                    os.chdir(self.working_dir)

                proc = subprocess.Popen(self.command,
                    stdout=self.stdout, stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    shell=shell, universal_newlines=True)
                output = proc.communicate(self.stdin)[0]
                if not output:
                    output = ''
                # if sublime's python gets bumped to 2.7 we can just do:
                # output = subprocess.check_output(self.command)
                main_thread(self.on_done,
                    _make_text_safeish(output, self.fallback_encoding), **self.kwargs)

        except subprocess.CalledProcessError, e:
            main_thread(self.on_done, e.returncode)
        except OSError, e:
            if e.errno == 2:
                main_thread(sublime.error_message, "Git binary could not be found in PATH\n\nConsider using the git_command setting for the Git plugin\n\nPATH is: %s" % os.environ['PATH'])
            else:
                raise e
