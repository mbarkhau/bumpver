import datetime as dt
import pycalver.version


def test_calver():
    import random

    first_version_str = "v201808.0001-dev"
    padding = len(first_version_str) + 3
    version_str = first_version_str

    def _current_calver() -> str:
        _current_calver.delta += dt.timedelta(days=int(random.random() * 5))

        return (dt.datetime.utcnow() + _current_calver.delta).strftime("v%Y%m")

    _current_calver.delta = dt.timedelta(days=1)

    global current_calver
    current_calver = _current_calver

    for i in range(1050):
        version_str = incr_version(version_str, tag=random.choice([
            None, "alpha", "beta", "rc"
        ]))
        print(f"{version_str:<{padding}}", end=" ")
        if (i + 1) % 8 == 0:
            print()

    print()
