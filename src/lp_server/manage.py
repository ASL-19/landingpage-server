#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    assert 'BUILD_ENV' in os.environ, 'BUILD_ENV not set in environment'
    build_env = os.environ['BUILD_ENV']
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lp_server.settings.' + build_env)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
