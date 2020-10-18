import io
import sys
import shlex
import random
import difflib
import datetime as dt
import subprocess as sp
import pkg_resources

import rich
import rich.box
import rich.table

from bumpcalver import v2version


def update(content, marker, value):
    begin_marker = f"<!-- BEGIN {marker} -->"
    end_marker   = f"<!-- END {marker} -->"

    prefix, rest   = content.split(begin_marker)
    _     , suffix = rest.split(end_marker)
    return prefix + begin_marker + value + end_marker + suffix


def _color_line(line):
    if line.startswith("+++") or line.startswith("---"):
        return line
    elif line.startswith("+"):
        return "\u001b[32m" + line + "\u001b[0m"
    elif line.startswith("-"):
        return "\u001b[31m" + line + "\u001b[0m"
    elif line.startswith("@"):
        return "\u001b[36m" + line + "\u001b[0m"
    else:
        return line


def print_diff(old_content, new_content):
    diff_lines = difflib.unified_diff(
        a=old_content.splitlines(),
        b=new_content.splitlines(),
        lineterm="",
    )

    for line in diff_lines:
        print(_color_line(line))


def update_md_code_output(content, command):
    output_data = sp.check_output(shlex.split(command))
    output      = output_data.decode("utf-8")

    replacement = "\n\n```\n" + "$ " + command + "\n" + output + "```\n\n"
    return update(content, command, replacement)


def weeknum_example():
    base_date = dt.date(2020, 12, 26)

    rows = []
    for i in range(10):
        d   = base_date + dt.timedelta(days=i)
        row = d.strftime("%Y-%m-%d (%a):  %Y %W %U  %G %V")
        rows.append(row)

    content = "\n".join(["                   YYYY WW UU  GGGG VV"] + rows)
    return "\n\n```\n" + content + "\n```\n\n"


def pattern_examples():
    patterns = [
        ("MAJOR.MINOR.PATCH[PYTAGNUM]"  , ""),
        ("MAJOR.MINOR[.PATCH[PYTAGNUM]]", ""),
        ("YYYY.BUILD[PYTAGNUM]"         , ""),
        ("YYYY.BUILD[-TAG]"             , ""),
        ("YYYY.INC0[PYTAGNUM]"          , ""),
        ("YYYY0M.PATCH[-TAG]"           , "¹"),
        ("YYYY0M.BUILD[-TAG]"           , ""),
        ("YYYY.0M"                      , ""),
        ("YYYY.MM"                      , ""),
        ("YYYY.WW"                      , ""),
        ("YYYY.MM.PATCH[PYTAGNUM]"      , ""),
        ("YYYY.0M.PATCH[PYTAGNUM]"      , "¹"),
        ("YYYY.MM.INC0"                 , ""),
        ("YYYY.MM.DD"                   , ""),
        ("YYYY.0M.0D"                   , ""),
        ("YY.0M.PATCH"                  , "²"),
    ]

    rand         = random.Random(0)
    field_values = [
        {
            'year_y': rand.randrange(2020, 2023),
            'month' : rand.randrange(   1,   12),
            'dom'   : rand.randrange(   1,   28),
            'major' : rand.randrange(   0,    1),
            'minor' : rand.randrange(   0,   20),
            'patch' : rand.randrange(   0,   20),
            'inc0'  : rand.randrange(   0,   20),
            'bid'   : rand.randrange(1000, 1500),
            'tag'   : rand.choice(["final", "beta"]),
        }
        for _ in range(100)
    ]

    rows = []
    for raw_pattern, lexico_caveat in patterns:
        sort_keys = ['year_y']
        if "0M" in raw_pattern or "MM" in raw_pattern:
            sort_keys.append('month')
        if "0D" in raw_pattern or "DD" in raw_pattern:
            sort_keys.append('dom')
        if "PATCH" in raw_pattern:
            sort_keys.append('patch')
        if "INC0" in raw_pattern:
            sort_keys.append('inc0')
        if "BUILD" in raw_pattern:
            sort_keys.append('bid')
        if "PYTAG" in raw_pattern:
            sort_keys.append('tag')

        field_values.sort(key=lambda fv: tuple(fv[k] for k in sort_keys))
        field_values[-1]['year_y'] = 2101

        example_versions = []
        notag_versions   = []
        pep440_versions  = []

        for fvals in field_values:
            vinfo           = v2version.parse_field_values_to_vinfo(fvals)
            example_version = v2version.format_version(vinfo, raw_pattern)
            example_versions.append(example_version)

            pep440_version = str(pkg_resources.parse_version(example_version))
            pep440_versions.append(pep440_version)

            notag_fvals = fvals.copy()
            notag_fvals['tag'] = 'final'

            notag_vinfo   = v2version.parse_field_values_to_vinfo(notag_fvals)
            notag_version = v2version.format_version(notag_vinfo, raw_pattern)
            notag_versions.append(notag_version)

        sample = rand.sample(sorted(example_versions, key=len, reverse=True)[:-1], 2)
        sample.sort(key=pkg_resources.parse_version)

        is_pep440 = pep440_versions == example_versions
        is_lexico = sorted(notag_versions) == notag_versions

        pattern_col  = f"`{raw_pattern}`"
        pep440_col   = "yes" if is_pep440 else "no"
        lexico_col   = ("yes" if is_lexico else "no") + lexico_caveat
        sample_str   = " ".join([v.ljust(16) for v in sample]).strip()
        examples_col = "`" + sample_str + "`"

        # row          = (pattern_col, examples_col, pep440_col)
        # sort_key     = (is_pep440  , -len(raw_pattern))

        row      = (pattern_col, examples_col, pep440_col, lexico_col)
        sort_key = (is_pep440  , is_lexico   , -len(raw_pattern))

        rows.append((sort_key, row))

    # rows.sort(reverse=True)

    patterns_table = rich.table.Table(show_header=True, box=rich.box.ASCII)
    patterns_table.add_column("pattern")
    patterns_table.add_column("examples")
    patterns_table.add_column("PEP440")
    patterns_table.add_column("lexico.")

    for _, row in rows:
        patterns_table.add_row(*row)

    buf = io.StringIO()
    rich.print(patterns_table, file=buf)
    table_str = buf.getvalue()
    table_str = "\n".join(table_str.splitlines()[1:-1])
    table_str = table_str.replace("-+-", "-|-")
    return "\n\n" + table_str + "\n\n"


old_content = io.open("README.md").read()

new_content = old_content
new_content = update_md_code_output(new_content, "bumpver --help")
new_content = update_md_code_output(new_content, "bumpver update --help")
new_content = update(new_content, "pattern_examples", pattern_examples())
new_content = update(new_content, "weeknum_example" , weeknum_example())


if old_content == new_content:
    print("Nothing changed")
elif "--dry" in sys.argv:
    print_diff(old_content, new_content)
else:
    with io.open("README.md", mode="w") as fobj:
        fobj.write(new_content)
