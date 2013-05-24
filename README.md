# Sublime Text 2 plugin: TypeScript Compiler

TypeScript compiler integrated into Sublime Text 2. You can compile fragment or whole .ts file into a new plain JavaScript. 

Developed for JavaScript prototyping in mind.

## Usage

You can select a fragment of TypeScript source code (it must be language consistent) or, without any selection, take the whole file. Next, call the compiler shortcut:

* Windows: CTRL+ALT+Y
* OSX: CMD+ALT+Y
* Linux: CTRL+ALT+Y

A new file will be created in JavaScript plain format.

## Installation

Install this repository via [Package Control](http://wbond.net/sublime_packages/package_control)

## Configuration

The package uses [Node.js](http://nodejs.org/) and [TypeScript Compiler](http://www.typescriptlang.org/). They must be installed before running the compiler.

Default configuration, you can find in the Sublime preference menu (Preferences/Package Settings/TypeScript Compiler), is the following:

* `node_path: "/usr/local/bin/node"`
* `typescript_path:"/usr/local/share/npm/bin/tsc"`

You can change it in according to your operating system.

Typical exemple for windows users:
```json
{
    "node_path"       : "C:\\Program Files\\nodejs\\node.exe",
    "typescript_path" : "C:\\Users\\User_Name\\AppData\\Roaming\\npm\\node_modules\\typescript\\bin\\tsc"
}
```
