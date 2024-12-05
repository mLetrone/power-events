# Contributing

Thank you for wanting to contribute to this project!

Don't hesitate to give feedback to improve it!

## Installation

First of all, let's set up your environment.

### Clone repository

If you haven't already cloned the [power-events repository](https://github.com/mLetrone/power-events/), do it before
continuing.

```shell
git clone https://github.com/mLetrone/power-events.git
```

### Install UV

UV is used as package manager inside the project, so you need to install it.
Please refer to the [official installation page](https://docs.astral.sh/uv/getting-started/installation/).

### Virtual environment

Virtual environment is a key feature in Python project development.
It allows to isolate the packages you install for each project, avoiding dependency conflict.

No need to worry, this step is quite simple.
Thanks to [uv](https://docs.astral.sh/uv/) you have nothing to do, it will create a virtual environment if not exists
when you install dependencies.

_So nothing to do here_ :smile:!

### Install dependencies

To install the required packages:

```shell
uv sync --all-groups
```

It will install all the dependencies to work on Power-events!

### Pre-commit

Some pre-checks are performed using githook before commit or push.
To enable it:

```shell
pre-commit install
```

At commit: check format and linting of your code, if one fails the commit is cancelled.

At push: check tests and types.

## Development guidelines

Writing code is, of course important for a project.
But because before writing code, we read the existing.
We should not forget to produce clean code to be easily readable and understandable.
As reference, we can take note from _Clean Code_, by Robert C. Martin.

And do not forget the _Zen of Python_ by Tim Peters

```text
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
```

You can get all the principals with this little easter egg:

```shell
python -c "import this"
```

### Lint

To ensure the format and the respect of rules, some tools are used:

- [ruff](https://docs.astral.sh/ruff/): A fast formatter and linter.
- [mypy](https://mypy.readthedocs.io/en/stable/getting_started.html): Static type checker.

There is a script that you can run that will format and clean all your code:

#### Linux

```shell
bash ./script/format.sh
```

#### Windows

```powershell
./script/format.ps1
```

For mypy:

```shell
mypy
```

### Tests

Whatever the modification, whether it's a feature or a fix, it must be tested :mag:!

A well-tested project is not about avoiding all bugs, but of limiting their severity and number.
And also, be confident that new modification does not imply any regression.

Now that said, to test the codebase and produce coverage:

```shell
pytest
```

It shows you whether the tests are passing or not, an interactive coverage is also generated.
You can open `./test-report/coverage/index.html` in your browser,
to explore interactively the regions of code that are covered by the tests
and notice if there is any region missing.

### Documentation

First, make sure to have set up your environment correctly as described above.

During your local development, you can build and serve your changes with site, that does live reloading.

```shell
mkdocs serve
```

It will serve the documentation on [http://127.0.0.1:8000/](`http://127.0.0.1:8000/`).
This way can see your changes in live.

### Git

#### Branch

Branch name should follow this naming convention:

**\<scope>/<short-name>**

List of scopes:

- **feature**
- **fix**
- **docs**
- etc. (scopes are not limited by these, it only has to be meaningful)

This way we can grasp the gist of your work in this branch in a blink.

#### Commit

We base our commit messages on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
and [gitmoji](https://gitmoji.dev/).

> Gitmoji is here as experiment to add some colors in old conventional commit, there are optional.


Summary :

```text
<type>(<scope>): <subject>
```

The scope is optional, you can find a simpler form:

```text
<type>: <subject>
```

In order to be concise, type and scope should not be longer than 10
characters. Limit the first line to 70 characters or less.

##### Types

- **build:** Changes that affects the build system or external dependencies,
  such as adding a dependency, or modifying the build system.
- **bump:** version change, new release.
- **ci:** Changes in CI.
- **chore:** Changes which does not modify the code sources nor the tests.
- **docs:** Addition or modification of documentation/comment.
- **feat:** Adding or modifying a feature.
- **fix:** Bug fix.
- **perf:** Code change that improves performance.
- **refactor:** Code change that doesn't fix a bug or add a feature.
- **revert:** Rollback changes from a previous commit.
- **style:** Changes that does not affect the sense/meaning of the
  code (space, formatting, semicolon, newline, etc...).
- **test:** Addition of missing tests or correction of existing tests.
