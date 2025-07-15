from __future__ import annotations

from functools import cmp_to_key

from gitlab_codeowners_linter.constants import DEFAULT_SECTION
from gitlab_codeowners_linter.sorting import sort_paths
from gitlab_codeowners_linter.sorting import sort_section_names


def fix(codeowners_data, violations, file_path):

    # Fix sections first

    # Are custom section names sorted?
    if violations.section_names_sorted:
        sort_sections_names_key = cmp_to_key(sort_section_names)
        sorted_sections_names = sorted(
            codeowners_data[1:],
            key=sort_sections_names_key,
        )
        codeowners_data_updated = []
        codeowners_data_updated.append(codeowners_data[0])
        codeowners_data_updated.extend(sorted_sections_names)
        codeowners_data = codeowners_data_updated

    # Are there duplicated sections?

    if violations.duplicated_sections != []:
        # If multiple sections have the same name, they are combined.
        # Also, section headings are not case-sensitive.
        # For example the entries defined under the sections Documentation
        # and DOCUMENTATION are combined, using the case of the first section
        i = 0
        while i < len(codeowners_data)-1:
            current_section = codeowners_data[i].codeowner_section.lower()
            if current_section.startswith('^'):
                current_section = current_section[1:]
            next_section = codeowners_data[i+1].codeowner_section.lower()
            if next_section.startswith('^'):
                next_section = next_section[1:]
            if current_section == next_section:
                codeowners_data[i].comments = codeowners_data[i].comments + \
                    codeowners_data[i+1].comments
                codeowners_data[i].entries = codeowners_data[i].entries + \
                    codeowners_data[i+1].entries
                codeowners_data.pop(i+1)
            else:
                i += 1

    # Then fix section's content

    codeowners_data_updated = []

    for section in codeowners_data:
        codeowners_data_updated.append(section)
        if violations.sections_with_blank_lines != []:
            if not section.codeowner_section in violations.sections_with_blank_lines:
                pass
            else:
                codeowners_data_updated[-1] = _fix_blank_lines(
                    codeowners_data_updated[-1])
        if violations.unsorted_paths_in_sections != [] or violations.duplicated_sections != []:
            if not section.codeowner_section in violations.unsorted_paths_in_sections and violations.duplicated_sections == []:
                pass
            else:
                codeowners_data_updated[-1] = _fix_unsorted_paths(
                    codeowners_data_updated[-1])
        if violations.sections_with_duplicate_paths != [] or violations.duplicated_sections != []:
            if not section.codeowner_section in violations.sections_with_duplicate_paths and violations.duplicated_sections == []:
                pass
            else:
                codeowners_data_updated[-1] = _fix_duplicated_paths(
                    codeowners_data_updated[-1])
        if violations.sections_with_non_existing_paths != []:
            if not section.codeowner_section in violations.sections_with_non_existing_paths:
                pass
            else:
                codeowners_data_updated[-1] = _fix_nonexisting_paths(
                    codeowners_data_updated[-1], violations.non_existing_paths[section.codeowner_section.lower()])
    codeowners_data = codeowners_data_updated

    _update_codeowners_file(codeowners_data, file_path)


def _fix_blank_lines(section):
    entries_updated = []
    for entry in section.entries:
        if not len(entry.path.strip()) == 0:
            entries_updated.append(entry)
    section_updated = section
    section_updated.entries = entries_updated
    return section_updated


def _fix_unsorted_paths(section):
    entries_updated = []

    sort_paths_key = cmp_to_key(sort_paths)
    entries_updated = sorted(
        section.entries, key=sort_paths_key)
    section_updated = section
    section_updated.entries = entries_updated

    return section_updated


def _fix_duplicated_paths(section):
    entries_updated = []

    for entry in section.entries:
        if entries_updated == []:
            entries_updated.append(entry)
            continue
        if entry.path == entries_updated[-1].path:
            # we have a duplicate
            entries_updated[-1].comments.extend(entry.comments)
            new_owners = entries_updated[-1].owners + \
                entry.owners
            entries_updated[-1].owners = sorted(
                list(set(new_owners)))
            continue
        entries_updated.append(entry)
    section_updated = section
    section_updated.entries = entries_updated
    return section_updated


def _fix_nonexisting_paths(section, non_existing_paths_in_section):
    entries_updated = []
    for entry in section.entries:
        if entry.path in non_existing_paths_in_section:
            continue
        entries_updated.append(entry)
    section_updated = section
    section_updated.entries = entries_updated
    return section_updated


def _update_codeowners_file(codeowners_data, file_path):
    with open(file_path, 'w') as f:
        for section in codeowners_data:
            # if the default section is empty let's skip it
            if section.codeowner_section != DEFAULT_SECTION:
                f.write('\n')
            if section.comments:
                for comment_line in section.comments:
                    f.write(f'{comment_line.rstrip()}\n')
            if section.codeowner_section != DEFAULT_SECTION:
                f.write(f'{section.codeowner_section.rstrip()}')
            if section.entries:
                f.write('\n')
                for entry in section.entries:
                    if entry.comments:
                        for comment_line in entry.comments:
                            f.write(f'{comment_line.rstrip()}\n')
                    owners = ' '.join(str(x) for x in entry.owners)
                    line_to_write = f'{entry.path} {owners}'
                    f.write(f'{line_to_write.rstrip()}\n')
