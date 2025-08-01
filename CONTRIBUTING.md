# Contributing to Sollumz

Thank you for considering contributing to Sollumz! We appreciate your time and effort to make this project better.

The following guidelines will help you get started with the contribution process. If you have any doubts or want to discuss the development of Sollumz you can join our [Discord][discord_server].

## Table of Contents

- [Contributing to Sollumz](#contributing-to-sollumz)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [How Can You Contribute?](#how-can-you-contribute)
    - [Reporting Issues](#reporting-issues)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Documentation](#documentation)
    - [Pull Requests](#pull-requests)
  - [Getting Started](#getting-started)
    - [Testing](#testing)
    - [Debugging](#debugging)
  - [Style Guidelines](#style-guidelines)
  - [Commit Guidelines](#commit-guidelines)
  - [License](#license)

## Code of Conduct

Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) to foster a respectful and inclusive community.

## How Can You Contribute?

### Reporting Issues

If you find a bug, please [create an issue][issue_tracker] in our issue tracker. Include as much detail as possible to help us understand and reproduce the problem. You may want to include .blend files, .xml files, asset names, screenshots, etc.

**Note**: The issue tracker should be for bug reports and features requests only. If you are having an issue and you are not sure if it is a bug or not, ask on the help section of our [Discord server][discord_server] first.

### Suggesting Enhancements

We welcome suggestions for new features, improvements, or changes to the project. You can submit your ideas by [creating an issue][issue_tracker] with the "feature request" label.

### Documentation

We use GitBook for our [wiki][wiki]. The source is located in the [`wiki` repository][wiki_repo]. You can edit the Markdown files and submit changes through [pull requests](#pull-requests).

For bigger pieces of work, such as writing a complete tutorial, you can ask on our [Discord][discord_server] for access as editor in GitBook. Then you can use GitBook's interface to edit and submit your changes for review.

### Pull Requests

We encourage you to submit pull requests to contribute directly to the project. Here's how you can do it:

1. Fork the repository and create your branch from `main`.
2. Make your changes, following the [style guidelines](#style-guidelines).
3. Ensure your code passes any existing tests.
4. Write clear and concise commit messages following our [commit guidelines](#commit-guidelines).
5. Submit a pull request, referencing any related issues.

We'll review your pull request, provide feedback, and work with you to get it merged.

## Getting Started

1. Clone this repository:
   ```ps
   > git clone https://github.com/Sollumz/Sollumz.git
   > cd Sollumz
   ```
2. Install Sollumz as a Blender addon. It is recommend to create a symbolic link in the addons directory, so your changes are picked automatically when restarting Blender:
    ```ps
    # Locate your Blender addons directory
    > cd "C:\Users\<user>\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons"
    > New-Item -ItemType SymbolicLink -Name Sollumz -Target "C:\path\to\sollumz\repo\"
    ```
3. Restart Blender and enable Sollumz in the list of addons.


These variables will be referenced in the following sections:
```ps
# Find your Blender executable
> $BLENDER = "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
# Find your Blender Python executable
> $BLENDER_PYTHON = "C:\Program Files\Blender Foundation\Blender 3.6\3.6\python\bin\python.exe"
```

### Testing

Sollumz uses `pytest` for its test suite. The tests are located in the `tests/` directory.

Tests are not required in pull requests due to the complexity of making good test cases with the Blender API, but they are greatly appreciated.

You can execute the tests with the following steps:
1. Install `pytest` in your Blender Python environment:
    ```ps
    > & $BLENDER_PYTHON -m pip install pytest pytest-blender
    ```
2. Run Blender with the test runner script from the repository root directory. Arguments after `--` are passed to `pytest`:
    ```ps
    > & $BLENDER --background --python .\tests\run.py -- -vv -s
    ```

### Debugging

Sollumz includes remote debugging support without additional addons. To enable it, follow these steps:

1. Install `debugpy` in your Blender Python environment:
   ```ps
   > & $BLENDER_PYTHON -m pip install debugpy
   ```
2. Run Blender with the environment variable `SOLLUMZ_DEBUG` set to `true`:
   ```ps
   > $env:SOLLUMZ_DEBUG="true"; & $BLENDER
   ```
3. Attach your preferred debugger to 127.0.0.1:5678.

Supported environtment variables:

|  Name                | Description |
|----------------------|-------------|
| `SOLLUMZ_DEBUG`      | If `true`, start the debugging server; otherwise, do nothing. |
| `SOLLUMZ_DEBUG_HOST` | Host used by the debugging server, default `127.0.0.1`. |
| `SOLLUMZ_DEBUG_PORT` | Port used by the debugging server, default `5678`. |
| `SOLLUMZ_DEBUG_WAIT` | If `true`, blocks execution until a client connects. Useful to debug initialization code. |
 

## Style Guidelines

Sollumz follows PEP 8 with a maximum line length of 120 characters.

Older parts of the codebase might not strictly adhere to PEP 8. When contributing to the project, do not reformat code unrelated to your changes.

## Commit Guidelines

We try to follow [Conventional Commits][conventional_commits] to make it easier to generate changelogs. Write meaningful commit messages to make the project history and release notes more understandable. If the change is significant or complex, please, include a commit description providing more details.

## License

By contributing to this project, you agree that your contributions will be licensed under the [project's license](LICENSE).

[discord_server]: https://discord.sollumz.org/
[issue_tracker]: https://github.com/Sollumz/Sollumz/issues
[wiki]: https://docs.sollumz.org/
[wiki_repo]: https://github.com/Sollumz/wiki
[conventional_commits]: https://www.conventionalcommits.org/en/v1.0.0/
