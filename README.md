# Template for a python project managed with Poetry

## Goal
Template project for a python application:
- dependencies managed by peotry
- delivered as a container

## IDE

`Visual Studio Code` is the recommended IDE for this project. It was chosen for the `Remote - Containers` extension that guarantees the same development environment for every developer. The project is configured so that everything works out of the box.

## Architecture

### File system organization

- `bin`: binaries for the project
- `src`: the source code of the application, and nothing more.
- `tools`: anything else that's required to make the project work but is not a part of the application. This may include source code, shell scripts, configuration files, etc.
- `tools/tooling` is used to explicitely link the various configuration files to the software that requires it.
- `tests`: holds tests that can be run with `pytest`.

### Quality Assurance

#### Formatting

- python: [isort](https://github.com/PyCQA/isort) and [black](https://github.com/psf/black).

#### Linting

- python: [pylint](https://www.pylint.org/).
- shell scripts: [shellcheck](https://github.com/koalaman/shellcheck).

#### Testing

- python: [pytest](https://github.com/pytest-dev/pytest/), with [pytest-cov](https://github.com/pytest-dev/pytest-cov) to handle coverage and [pytest-xdist](https://github.com/ohmu/pytest-xdist) to handle parallelization.

#### Type checking

- python: [mypy](https://github.com/python/mypy)

### Makefile

The project uses a `Makefile` as a way to provide quick access to common commands. It should not be used to write complex scripts. It was chosen over `poetry` scripts because `make` is shorter to type than `poetry run`, despite the shortfall of `make` it is everywhere and many developers are used to `make target` commands, and finally the `Makefile` syntax should be awful enough that you would want to write a `shell` or `python` script if you wanted to do something complicated and call that from the `Makefile`.
