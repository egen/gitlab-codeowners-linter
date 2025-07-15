# Gitlab CODEOWNERS linter
# What we want to check:
# The CODEOWNERS file must be formatted respecting the following rules:
#   - every section must be sorted alphabetically
#   - within a section, paths must be ordered alphabetically
#   - there must be no empty lines between paths
#   - paths in a section must be unique
#   - paths must exist
#   - there must be no duplicated sections
#   - there must not be trailing whitespace
#
from __future__ import annotations

import logging
import sys

from gitlab_codeowners_linter.autofix import fix
from gitlab_codeowners_linter.checks import check
from gitlab_codeowners_linter.input import get_arguments
from gitlab_codeowners_linter.parser import parse_codeowners

# TODO: manage logging level via args
logging.basicConfig(level=logging.ERROR)


class OwnersList:
    def __init__(self, file_path, no_autofix):
        """
        file_path: path of the CODEOWNERS file
        """
        self.file_path = file_path
        self.codeowners_data = parse_codeowners(self.file_path)
        self.autofix = not no_autofix

    def lint(self):
        violations = check(self.codeowners_data, self.file_path)
        if self.autofix:
            fix(self.codeowners_data, violations, self.file_path)
        return violations


def lint_codeowners_file(codeowners_file, no_autofix):
    codeowners = OwnersList(codeowners_file, no_autofix)
    return codeowners.lint()


def main():
    codeowners_file, no_autofix = get_arguments(sys.argv[1:])
    if codeowners_file == None:
        logging.debug(
            'You did not provide a valid CODEOWNERS path, you can use a positional argument or the flag --codeowners_file. Please refer to the README for more info')
        sys.exit(0)
    violations = lint_codeowners_file(
        codeowners_file, no_autofix)
    if violations.violation_error_messages:
        logging.error(
            'There are the following linting violations: %s', violations.violation_error_messages)
        sys.exit(1)


if __name__ == '__main__':
    main()
