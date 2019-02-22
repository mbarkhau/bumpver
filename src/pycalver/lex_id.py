# This file is part of the pycalver project
# https://gitlab.com/mbarkhau/pycalver
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

"""A scheme for lexically ordered numerical ids.

Throughout the sequence this expression remains true, whether you
are dealing with integers or strings:

    older_id < newer_id

The left most character/digit is only used to maintain lexical
order, so that the position in the sequence is maintained in the
remaining digits.

    sequence_pos = int(idval[1:], 10)

lexical  sequence_pos
0                   0
11                  1
12                  2
...
19                  9
220                20
221                21
...
298                98
299                99
3300              300
3301              301
...
3998              998
3999              999
44000            4000
44001            4001
...
899999998    99999998
899999999    99999999
9900000000  900000000
9900000001  900000001
...
9999999998  999999998
9999999999  999999999       # maximum value

You can add leading zeros to delay the expansion and/or increase
the maximum possible value.

lexical       sequence_pos
0001                     1
0002                     2
0003                     3
...
0999                   999
11000                 1000
11001                 1001
11002                 1002
...
19998                 9998
19999                 9999
220000               20000
220001               20001
...
899999999998   99999999998
899999999999   99999999999
9900000000000 900000000000
9900000000001 900000000001
...
9999999999998 999999999998
9999999999999 999999999999      # maximum value

This scheme is useful when you just want an ordered sequence of
numbers, but the numbers don't have any particular meaning or
arithmetical relation. The only relation they have to each other
is that numbers generated later in the sequence are greater than
ones generated earlier.
"""


MINIMUM_ID = "0"


def next_id(prev_id: str) -> str:
    """Generate next lexical id.

    Increments by one and adds padding if required.

    >>> next_id("0098")
    '0099'
    >>> next_id("0099")
    '0100'
    >>> next_id("0999")
    '11000'
    >>> next_id("11000")
    '11001'
    """

    num_digits = len(prev_id)

    if prev_id.count("9") == num_digits:
        raise OverflowError("max lexical version reached: " + prev_id)

    _prev_id_val       = int(prev_id, 10)
    _maybe_next_id_val = int(_prev_id_val) + 1
    _maybe_next_id_str = f"{_maybe_next_id_val:0{num_digits}}"

    _is_padding_ok = prev_id[0] == _maybe_next_id_str[0]
    _next_id_str: str

    if _is_padding_ok:
        _next_id_str = _maybe_next_id_str
    else:
        _next_id_str = str(_maybe_next_id_val * 11)
    return _next_id_str


def ord_val(lex_id: str) -> int:
    """Parse the ordinal value of a lexical id.

    The ordinal value is the position in the sequence,
    from repeated calls to next_id.

    >>> ord_val("0098")
    98
    >>> ord_val("0099")
    99
    >>> ord_val("0100")
    100
    >>> ord_val("11000")
    1000
    >>> ord_val("11001")
    1001
    """
    if len(lex_id) == 1:
        return int(lex_id, 10)
    else:
        return int(lex_id[1:], 10)


def _main() -> None:
    _curr_id = "01"
    print(f"{'lexical':<13} {'numerical':>12}")

    while True:
        print(f"{_curr_id:<13} {ord_val(_curr_id):>12}")
        _next_id = next_id(_curr_id)

        if _next_id.count("9") == len(_next_id):
            # all nines, we're done
            print(f"{_next_id:<13} {ord_val(_next_id):>12}")
            break

        if _next_id[0] != _curr_id[0] and len(_curr_id) > 1:
            print(f"{_next_id:<13} {ord_val(_next_id):>12}")
            _next_id = next_id(_next_id)
            print(f"{_next_id:<13} {ord_val(_next_id):>12}")
            _next_id = next_id(_next_id)

            print("...")

            # skip ahead
            _next_id = _next_id[:1] + "9" * (len(_next_id) - 2) + "8"

        _curr_id = _next_id


if __name__ == '__main__':
    _main()
