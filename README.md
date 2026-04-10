# django-field-permissions
A Django package for implementing field-level permissions in your projects.

if a user doesnt use django forms but wants to implement field permission checks in the view, how would that work with middleware and attaching field perms to the request?

if a user is editing an object with several fields, how will that work with field permissions


## Packaging

Here's a step-by-step guide for packaging django-field-permissions and publishing it to PyPI.

1. Project structure
Your package directory should look like this:


django-field-permissions/          # repo root
├── field_permissions/             # the Django app (importable package)
│   ├── __init__.py
│   ├── models.py
│   ├── middleware.py
│   ├── admin.py
│   ├── apps.py
│   ├── management/
│   │   └── commands/
│   │       └── sync_field_permissions.py
│   └── templatetags/
│       └── field_permission_filters.py
├── pyproject.toml                 # package metadata + build config
├── README.md
├── LICENSE
└── MANIFEST.in                    # optional, for including non-Python files
The key thing: the installable app is the field_permissions/ directory. Everything else at the repo root is packaging scaffolding.

2. Create pyproject.toml
This is the modern replacement for setup.py and setup.cfg. Use it exclusively — don't create a setup.py unless you have a specific reason.

Required sections:

[build-system] — tells pip which build backend to use. hatchling and setuptools are the two most common. hatchling has simpler defaults.

[project] — package metadata:

name — the PyPI name (django-field-permissions). This is what people pip install.
version — start at 0.1.0. Follow semver.
description — one-liner.
readme — points to README.md.
license — e.g. MIT, BSD-3-Clause.
requires-python — minimum Python version (e.g. >=3.10).
dependencies — runtime dependencies. For you, just Django>=4.2 (or whatever minimum you want to support).
authors — your name and email.
classifiers — PyPI category tags. Include the Django framework classifier, Python version classifiers, and license classifier.
[project.urls] — links to repo, docs, etc.

3. Choose a build backend
Pick one:

hatchling — minimal config, good defaults, auto-discovers packages. Add hatch as a dev dependency.
setuptools — more established, requires slightly more config (e.g. [tool.setuptools.packages.find]).
Either works. Hatchling is less boilerplate for a single-app package like this.

4. Add a LICENSE file
PyPI requires a license. Pick one (MIT and BSD-3-Clause are standard for Django packages), create the file at the repo root.

5. Write your README.md
This renders as the PyPI project page. Include:

What the package does (one paragraph)
Installation (pip install django-field-permissions)
Quick setup (add to INSTALLED_APPS, MIDDLEWARE, run manage.py sync_field_permissions)
Basic usage (template filter example, view helper example)
Settings reference (FIELD_PERMISSIONS_CACHE_TIMEOUT, FIELD_PERMISSIONS_ALLOWED_MODELS)
6. Version management
Two options:

Manual — hardcode version = "0.1.0" in pyproject.toml and update it before each release.
Dynamic — use __version__ in field_permissions/__init__.py and configure the build backend to read it. Hatchling supports this with dynamic = ["version"] and [tool.hatch.version].
Start with manual. Switch to dynamic later if you want.

7. Create a PyPI account
Go to pypi.org and register.
Go to Account Settings > API tokens.
Create a token scoped to "Entire account" for the first upload. After the first upload, create a project-scoped token and delete the account-wide one.
8. Install build and publish tools

pip install build twine
build — creates the distributable files (sdist + wheel).
twine — uploads them to PyPI.
9. Build the package
From the repo root:


python -m build
This creates a dist/ directory with two files:

django_field_permissions-0.1.0.tar.gz — source distribution
django_field_permissions-0.1.0-py3-none-any.whl — wheel (pre-built)
10. Test with TestPyPI first
Don't publish to real PyPI on your first try. Use TestPyPI:

Create a separate account at test.pypi.org.
Upload:

twine upload --repository testpypi dist/*
Test install in a fresh venv:

pip install --index-url https://test.pypi.org/simple/ django-field-permissions
Verify: open a Python shell, import field_permissions, check it works.
11. Publish to PyPI
Once TestPyPI looks good:


twine upload dist/*
Enter your API token when prompted (username is __token__, password is the token string).

12. Verify the release

pip install django-field-permissions
Check the PyPI page at pypi.org/project/django-field-permissions/ — make sure the README renders, metadata looks right, and the install works.

13. Subsequent releases
For each new version:

Update the version number in pyproject.toml (or __init__.py if dynamic).
Commit and tag: git tag v0.2.0.
Clean old builds: delete the dist/ directory.
Rebuild: python -m build.
Upload: twine upload dist/*.
Things to do before your first publish
Pick a license and add the file.
Add a .gitignore entry for dist/, *.egg-info/, and build/.
Test the package installs cleanly in a blank Django project — add to INSTALLED_APPS, add middleware, run the management command, confirm the template filter loads.
Decide your minimum Django version and test against it. Django 4.2 LTS is a reasonable floor.
Name check — search PyPI for django-field-permissions to make sure the name isn't taken. If it is, you'll need a different PyPI package name (the internal app name field_permissions can stay the same).