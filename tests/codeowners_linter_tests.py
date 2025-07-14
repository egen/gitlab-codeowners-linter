from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from dataclasses import dataclass
from functools import cmp_to_key
from pathlib import Path
from unittest.mock import patch

import gitlab_codeowners_linter  # we need the full import for the mock
from gitlab_codeowners_linter.codeowners_linter import lint_codeowners_file
from gitlab_codeowners_linter.input import get_arguments
from gitlab_codeowners_linter.parser import CodeownerEntry
from gitlab_codeowners_linter.parser import CodeownerSection
from gitlab_codeowners_linter.sorting import sort_paths
from gitlab_codeowners_linter.sorting import sort_section_names


class Test_Functions(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.test_dir = tempfile.mkdtemp()
        self._get_non_existing_paths = gitlab_codeowners_linter.checks._get_non_existing_paths

    def tearDown(self):
        gitlab_codeowners_linter.checks._get_non_existing_paths = self._get_non_existing_paths
        shutil.rmtree(self.test_dir)

    def test_parser(self):
        @dataclass
        class TestCase:
            name: str
            input: list[str]
            expected_codeowners_file: str
            expected_no_autofix: str

        testcases = [
            TestCase(
                name='regular_input',
                input=['--codeowners_file', 'CODEOWNERS'],
                expected_codeowners_file='CODEOWNERS',
                expected_no_autofix='False'),
            TestCase(
                name='trailing_paths_input_ignored',
                input=['.gitlab/CODEOWNERS', '--codeowners_file',
                       'CODEOWNERS', 'path/1', 'path/2'],
                expected_codeowners_file='CODEOWNERS',
                expected_no_autofix='False'),
            TestCase(
                name='trailing_paths_input_and_no_fix',
                input=['.gitlab/CODEOWNERS', 'path/to/CODEOWNERS',
                       'path/1', 'path/2', '--no_autofix', 'path/3'],
                expected_codeowners_file='.gitlab/CODEOWNERS',
                expected_no_autofix='True'),
            TestCase(
                name='positional_paths_wrong_input_and_no_fix',
                input=['.gitlab/wrong/CODEOWNERS', 'path/to/CODEOWNERS',
                       'path/1', 'path/2', '--no_autofix', 'path/3'],
                expected_codeowners_file='None',
                expected_no_autofix='True')
        ]

        for case in testcases:
            codeowners_file, no_autofix = get_arguments(case.input)
            self.assertEqual(str(codeowners_file),
                             case.expected_codeowners_file, 'failed test {} expected {}, actual {}'.format(
                case.name,
                case.expected_codeowners_file,
                codeowners_file,))
            self.assertEqual(str(no_autofix), case.expected_no_autofix, 'failed test {} expected {}, actual {}'.format(
                case.name,
                case.expected_no_autofix,
                no_autofix,))

    def test_sort_sections_function(self):
        @dataclass
        class TestCase:
            name: str
            input: list[str]
            expected: list[str]

        testcases = [
            TestCase(
                name='unsorted',
                input=[
                    '[BUILD]',
                    '[SECURITY]',
                    '[SYSTEM]',
                    '^[And_a_last_section]',
                    '^[SYSTEM]',
                ],
                expected=[
                    '^[And_a_last_section]',
                    '[BUILD]',
                    '[SECURITY]',
                    '^[SYSTEM]',
                    '[SYSTEM]',
                ],
            ),
            TestCase(name='empty_slice', input=[], expected=[]),
            TestCase(
                name='already_sorted',
                input=[
                    '^[And_a_last_section]',
                    '[BUILD]',
                    '[SECURITY]',
                    '^[SYSTEM]',
                    '[SYSTEM]',
                ],
                expected=[
                    '^[And_a_last_section]',
                    '[BUILD]',
                    '[SECURITY]',
                    '^[SYSTEM]',
                    '[SYSTEM]',
                ],
            ),
        ]
        sort_section_key = cmp_to_key(sort_section_names)

        for case in testcases:
            data = []
            actual = data
            for section in case.input:
                data.append(CodeownerSection(section, [], []))
            actual = sorted(data, key=sort_section_key)
            actual_names = [x.codeowner_section for x in actual]
            self.assertListEqual(
                case.expected,
                actual_names,
                'failed test {} expected {}, actual {}'.format(
                    case.name,
                    case.expected,
                    actual_names,
                ),
            )

    def test_sort_path_function(self):
        @dataclass
        class TestCase:
            name: str
            input: list[str]
            expected: list[str]

        testcases = [
            TestCase(
                name='unsorted',
                input=[
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '* test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    'WORKSPACE test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                    '/www/**/*.md test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    '/www/* test@email.com',
                ],
                expected=[
                    '* test@email.com',
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    'WORKSPACE test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/* test@email.com',
                    '/www/**/*.md test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                ],
            ),
            TestCase(name='empty_slice', input=[], expected=[]),
            TestCase(
                name='already_sorted',
                input=[
                    '* test@email.com',
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    'WORKSPACE test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                ],
                expected=[
                    '* test@email.com',
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    'WORKSPACE test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                ],
            ),
        ]
        sort_paths_key = cmp_to_key(sort_paths)

        for case in testcases:
            data = CodeownerSection('Test', [], [])
            actual = data
            for path in case.input:
                data.entries.append(CodeownerEntry(path, ''))
            actual.entries = sorted(data.entries, key=sort_paths_key)
            self.assertListEqual(
                case.expected,
                actual.get_paths(),
                'failed test {} expected {}, actual {}'.format(
                    case.name,
                    case.expected,
                    actual.get_paths(),
                ),
            )

    def test_non_existing_path_autofix(self):

        @dataclass
        class TestCase:
            name: str
            input: Path
            expected_check: list[str]
            expected_fix: Path

        testcases = [
            TestCase(
                name='already_formatted',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/existing_paths_input.txt',
                ),
                expected_check=[
                    'Sections are not sorted',
                    'The sections [SECURITY], [security] are duplicates',
                    'The paths in sections __default_codeowner_section__, [Security], [SYSTEM], [SECURITY] are not sorted',
                    'The sections __default_codeowner_section__ have duplicate paths',
                    'The sections __default_codeowner_section__, [Security], [SYSTEM], [SECURITY], [security] have non-existing paths'],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/existing_paths_autofix.txt',
                ),
            ),
        ]
        for case in testcases:
            actual = os.path.join(
                self.test_dir,
                'actual_input.txt',
            )
            shutil.copyfile(case.input, actual)
            violations = lint_codeowners_file(actual, False)
            self.assertEqual(violations.violation_error_messages, case.expected_check, 'failed autofix feature for test {} expected {}, actual {}'.format(
                case.name,
                case.expected_fix,
                actual,
            ))
            with open(actual) as input, open(case.expected_fix) as expected_output:
                self.assertListEqual(
                    list(input),
                    list(expected_output),
                    'failed autofix feature for test {} expected {}, actual {}'.format(
                        case.name,
                        case.expected_fix,
                        actual,
                    ),
                )


class Test_Autofix(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.test_dir = tempfile.mkdtemp()
        self._get_non_existing_paths = gitlab_codeowners_linter.checks._get_non_existing_paths

    def tearDown(self):
        gitlab_codeowners_linter.checks._get_non_existing_paths = self._get_non_existing_paths
        shutil.rmtree(self.test_dir)

    def test_autofix_feature(self):
        patcher = patch(
            'gitlab_codeowners_linter.checks._get_non_existing_paths')
        mock_thing = patcher.start()
        mock_thing.return_value = [], []

        @dataclass
        class TestCase:
            name: str
            input: Path
            expected_check: list[str]
            expected_fix: Path

        testcases = [
            TestCase(
                name='already_formatted',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/formatted_input.txt',
                ),
                expected_check=[],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/formatted_autofix.txt',
                ),
            ),
            TestCase(
                name='not_formatted',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/unformatted_input.txt',
                ),
                expected_check=[
                    'Sections are not sorted',
                    'There are blank lines in the sections __default_codeowner_section__, [BUILD], [SECURITY]',
                    'The paths in sections __default_codeowner_section__, [BUILD], [SYSTEM], [TEST_SECTION] are not sorted',
                    'The sections __default_codeowner_section__ have duplicate paths',
                ],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/unformatted_autofix.txt',
                ),
            ),
            TestCase(
                name='not_formatted_no_default_section',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/no_default_section_input.txt',
                ),
                expected_check=[
                    'Sections are not sorted',
                    'The sections [SECTION_NAME], [section_name], [Section_Name] are duplicates',
                    'There are blank lines in the sections [Section_name], [BUILD], [SECURITY]',
                    'The paths in sections [Section_name], [BUILD], [SYSTEM], [SECTION_NAME], [TEST_SECTION] are not sorted',
                    'The sections [Section_name], [SECTION_NAME] have duplicate paths',
                ],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/no_default_section_autofix.txt',
                ),
            ),
            TestCase(
                name='optional_sections_not_formatted',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/optional_sections_input.txt',
                ),
                expected_check=[
                    'Sections are not sorted',
                    'The sections [System], [SYSTEM], [SYSTEM] are duplicates',

                ],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/optional_sections_autofix.txt',
                ),
            ),
            TestCase(
                name='empty_file',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/empty_input.txt',
                ),
                expected_check=[],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/empty_autofix.txt',
                ),
            ),
            TestCase(
                name='trailing_whitespace',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/trailing_whitespace_input.txt',
                ),
                expected_check=[
                    'Lines with trailing whitespace: [6, 8]',
                ],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/trailing_whitespace_autofix.txt',
                ),
            ),
        ]
        for case in testcases:
            actual = os.path.join(
                self.test_dir,
                'actual_input.txt',
            )
            shutil.copyfile(case.input, actual)
            violations = lint_codeowners_file(actual, False)
            self.assertEqual(violations.violation_error_messages, case.expected_check, 'failed autofix feature for test {} expected {}, actual {}'.format(
                case.name,
                case.expected_fix,
                actual,
            ),)
            with open(actual) as input, open(case.expected_fix) as expected_output:
                self.assertListEqual(
                    list(input),
                    list(expected_output),
                    'failed autofix feature for test {} expected {}, actual {}'.format(
                        case.name,
                        case.expected_fix,
                        actual,
                    ),
                )


if __name__ == '__main__':
    unittest.main()
