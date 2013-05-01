# -*- coding: utf-8 -*-
# Author: Guido D'Albore
# Version: 0.1.1
# Official Repository: https://github.com/setumiami/sublime-typescript-compiler
# CommandThread class is based on Git sublime package (https://github.com/kemayo/sublime-text-2-git)

import sublime, sublime_plugin
import os
import subprocess 
import threading
import functools
import tempfile
import re

DEBUG = True

# Used in case the configuration is not found in 'sublime.settings'
DEFAULT_NODE_PATH       = '/usr/local/bin/node'
DEFAULT_TYPESCRIPT_PATH = '/usr/local/bin/tsc'

class TypescriptCommand(sublime_plugin.TextCommand): 
    def run(self, edit):
        self.config          = sublime.load_settings("TypeScript Compiler.sublime-settings")
        self.node_path       = DEFAULT_NODE_PATH
        self.typescript_path = DEFAULT_TYPESCRIPT_PATH

        if(self.config):
            if(self.config.get("node_path")):
                self.node_path = self.config.get("node_path")
            if(self.config.get("typescript_path")):
                self.typescript_path = self.config.get("typescript_path")

        if(DEBUG):
            print("* TypeScript Compiler running...")
            print("  - Node.js path: %s" % self.node_path)
            print("  - TypeScript complier path: %s" % self.typescript_path)

        source = self.get_content();
        
        self.compile(str(source))
        
    def get_content(self):            
        view = self.view
        regions = view.sel()

        if len(regions) > 1 or not regions[0].empty():
                return view.substr(regions[0]);
        else: 
                view_content = sublime.Region(0, view.size())
                return view.substr(view_content)

    def compile(self, source):
        if(self.view.file_name() != None):
            self.sourcefilename = self.view.file_name()
            self.destinationfilename = os.path.splitext(self.sourcefilename)[0]
            self.destinationfilename += ".js"
        else:
            # File doesn't exist on disk, it will be created in temp directory

            # Create TypeScript source file
            f = tempfile.NamedTemporaryFile(prefix = 'tsc_', suffix = '.ts', delete = False)
            self.sourcefile = f
            self.sourcefile.write(source)
            self.sourcefile.close()
            self.sourcefilename = self.sourcefile.name;


            # Create JavaScript destination file
            f = tempfile.NamedTemporaryFile(prefix = 'tsc_', suffix = '.js', delete = False)
            self.destinationfile = f
            #self.destinationfile.write(source)
            self.destinationfile.close()
            self.destinationfilename = self.destinationfile.name

        self.workingdir = os.path.split(self.sourcefilename)[0]

        if(DEBUG):
            print "  - Source TypeScript file: %s" % self.sourcefilename
            print "  - Destination plain JavaScript file: %s" % self.destinationfilename
            print "  - Working directory: %s" % self.workingdir

        commandline = [ self.node_path,
                        self.typescript_path,
                        '--out',
                        self.destinationfilename,
                        self.sourcefilename];

        command = CommandThread(commandline, self.onDone, self.workingdir)
        command.start()

    def onDone(self, result):
        if(DEBUG):
            print("  - Result: %s" % result)
            print("--TypeScript Compiler finished--")

        showerror = False

        if(re.search(".*TypeError.*", result, re.MULTILINE)): 
            showerror = True
            result = "*** Your TypeScript contains errors ***\n\n" + result

        if(re.search(".*Cannot find module.*", result, re.MULTILINE) or (not os.path.isfile(self.destinationfilename))): 
            showerror = True
            result = "*** Your TypeScript compiler is not properly configured. ***\n*** Check your Preferences (menu 'Preferences/Package Settings/TypeScript Compiler') and retry. ***\n\n" + result

        if(showerror):
            w = self.view.window()
            w.new_file()
            w.active_view().set_read_only(False)
            edit = w.active_view().begin_edit()
            w.active_view().insert(edit, w.active_view().size(), result)
            w.active_view().end_edit(edit)
            w.active_view().set_read_only(True)
        else:
            sublime.active_window().open_file(self.destinationfilename)
            sublime.active_window().active_view().set_syntax_file("Packages/JavaScript/JavaScript.tmLanguage")            

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
                main_thread(sublime.error_message, "Node.js or TypeScript Complier (tsc) binary could not be found in PATH\n\nPATH is: %s" % os.environ['PATH'])
            else:
                raise e
