# gitlab-codeowners-linter
Keep your [Gitlab's CODEOWNERS file](https://docs.gitlab.com/ee/user/project/code_owners.html) up to date with this linter.

## Features
gitlab-codeowners-linter makes sure that the CODEOWNERS file is formatted respecting the following rules:
  - every section must be sorted alphabetically
  - within a section, paths must be ordered alphabetically
  - paths in a section must be unique
  - there must be no empty lines between paths
  - paths must exist
  - there must not be duplicated sections
  - there must not be trailing whitespace

The linter can run in check or autofix mode.

## Usage
Install the library with
```bash
git clone git@github.com:Qarik-Group/gitlab-codeowners-linter.git
cd gitlab-codeowners-linter
pip install .
```

You need to pass the path to the CODEOWNERS file to the linter. It can be done via positional argument or with the `--codeowners_file` with the path to the CODEOWNERS file.
The linter by default will run in autofix mode. If you just want to check your file without modifying it use `--no_autofix`.

### Usage with pre-commit

You can use this linter with `pre-commit` by adding the following hook in your `.pre-commit-config.yaml` file.

```yaml
repos:
- repo:  https://github.com/Qarik-Group/gitlab-codeowners-linter
  rev: v1.0.3
  hooks:
  - id:  gitlab-codeowners-linter
    args: ['--codeowners_file=path/to/your/CODEOWNERS/file']
```
Note: with `pre-commit` the usage of `--codeowners_file` is optional, it only speeds up the linter