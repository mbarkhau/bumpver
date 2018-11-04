# Stub files for mypy

Before using stubs, check if the library you want to use
itself uses mypy. If it does, the better approach is to
add it to `requirements/vendor.txt`. This way mypy will
find the actual source instead of just stub files.
