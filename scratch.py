from pkg_resources import parse_version
import re

canonical_version_re = re.compile(r"""
\b
(?P<version>
    (?P<calver>
       v                    # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
    )
    (?:
        \.                      # "." build nr prefix
        (?P<build_nr>\d{3,})
    )
)(?:\s|$)
""", flags=re.VERBOSE)


full_version_re = re.compile(r"""
\b
(?P<version>
    (?P<calver>
       v                    # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
    )
    (?:
        \.                      # "." build nr prefix
        (?P<build>\d+)
    )
    (?:
        \-                      # "-" tag prefix
        (?P<tag>a|alpha|b|beta|dev|c|rc|pre|preview|post)
        (?P<tag_nr>\d*)
    )?
)(?:\s|$)
""", flags=re.VERBOSE)

versions = [
    "v201711.0001-alpha",
    "v201711.0002-alpha",
    "v201712.0003-beta3",
    "v201712.0004-preview",
    "v201712.0005",
    "v201712.0006",
    "v201712.0007-beta",
    "v201801.0008-beta",
    "v201801.0008-dev",
    "v201801.0009",
    "v201802.0010",
    "v201802.0007",
    "v201904.0050",
    "v201905.0051",
    "v201905.0052",
    "v201712.0027-beta1",
    "v201712.beta-0027",
    "v201712.post-0027",
    "v201712.post-0027",
]

for vstr in versions:
    v = parse_version(vstr)
    print(vstr.ljust(20), repr(v).ljust(30), int(v.is_prerelease))
    v = full_version_re.match(vstr)
    print("\t", v and v.groupdict())
    v = canonical_version_re.match(vstr)
    print("\t", v and v.groupdict())

a = "v201711.beta-0001"
b = "v201711.0002-beta"
c = "v201711.0002"
d = "0.9.2"

va = parse_version(a)
vb = parse_version(b)
vc = parse_version(c)
vd = parse_version(d)

print(a, repr(va))
print(b, repr(vb))
print(c, repr(vc))
print(d, repr(vd), vd < vc)


# https://regex101.com/r/fnj60p/3
pycalver_re = re.compile(r"""
\b
(?P<full_version>
        (?P<calver>
           v                    # "v" version prefix
           (?P<year>\d{4})
           (?P<month>\d{2})
        )
    (?:
        .                       # "." build nr prefix
        (?P<build_nr>\d{4,})
    )
)(?:\s|$)
""", flags=re.VERBOSE)

print(pycalver_re.match("v201712.0027").groupdict())

print(repr(parse_version("v201712.0027")))
print(repr(parse_version("v201712.0027")))
print(repr(parse_version("v201712.0027")))
print(repr(parse_version("v201712") == parse_version("v201712.0")))

print("v201712.0027" > "v201712.0028")
