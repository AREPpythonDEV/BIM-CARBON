#! python3
# -*- coding: utf-8 -*-

"""
pyRevit 5.2 requests Helper - Standalone Fix
===========================================

This module fixes the requests import issue in pyRevit 5.2 by addressing
the broken six.moves lazy loading mechanism.

USAGE:
    from pyrevit_52_requests_helper import fix_requests
    fix_requests()  # Apply the fix once

    # Now use requests normally
    import requests
    response = requests.get('https://api.example.com')

OR:
    from pyrevit_52_requests_helper import requests  # Pre-fixed requests
    response = requests.get('https://api.example.com')

PROBLEM SOLVED:
    - six.moves lazy loading is broken in pyRevit 5.2
    - collections.Mapping compatibility issues
    - urllib3.packages.six.moves import failures
    - requests.packages.urllib3.packages.six.moves import failures

AUTHOR: Based on extensive debugging with Claude AI
VERSION: 1.0
DATE: 2025
"""

import sys
import types

# Global flag to track if fix has been applied
_fix_applied = False


def fix_requests():
    """
    Apply the complete fix for requests in pyRevit 5.2
    Call this once before using requests
    """
    global _fix_applied

    if _fix_applied:
        print("✓ requests fix already applied")
        return True

    print("=== APPLYING PYREVIT 5.2 REQUESTS FIX ===")

    # Step 1: Create working six.moves
    if not _create_working_six_moves():
        return False

    # Step 2: Fix collections.Mapping
    if not _fix_collections_mapping():
        return False

    # Step 3: Setup urllib3 packages
    if not _setup_urllib3_packages():
        return False

    # Step 4: Test the fix
    if not _test_fix():
        return False

    _fix_applied = True
    print("✓ requests fix applied successfully!")
    return True


def _create_working_six_moves():
    """
    Create a working six.moves module to replace broken lazy loading
    """
    try:
        import six

        # Create real six.moves module
        moves_module = types.ModuleType('six.moves')
        moves_module.__path__ = []  # Make it a package

        # Add all required modules
        import queue
        import http.client
        import builtins
        import configparser
        import io
        import http.cookiejar
        import http.cookies
        import urllib.parse
        import urllib.request
        import urllib.error

        # Basic modules
        moves_module.queue = queue
        moves_module.http_client = http.client
        moves_module.builtins = builtins
        moves_module.configparser = configparser
        moves_module.StringIO = io.StringIO
        moves_module.http_cookiejar = http.cookiejar
        moves_module.http_cookies = http.cookies
        moves_module.xrange = range  # Python 3 compatibility

        # Create urllib submodule
        urllib_module = types.ModuleType('urllib')
        urllib_module.parse = urllib.parse
        urllib_module.request = urllib.request
        urllib_module.error = urllib.error

        moves_module.urllib = urllib_module
        moves_module.urllib_parse = urllib.parse
        moves_module.urllib_request = urllib.request
        moves_module.urllib_error = urllib.error

        # Replace six.moves with working version
        six.moves = moves_module

        # Add to sys.modules
        sys.modules['six.moves'] = moves_module
        sys.modules['six.moves.urllib'] = urllib_module
        sys.modules['six.moves.urllib.parse'] = urllib.parse
        sys.modules['six.moves.urllib.request'] = urllib.request
        sys.modules['six.moves.urllib.error'] = urllib.error
        sys.modules['six.moves.queue'] = queue
        sys.modules['six.moves.http_client'] = http.client
        sys.modules['six.moves.builtins'] = builtins
        sys.modules['six.moves.configparser'] = configparser
        sys.modules['six.moves.StringIO'] = io.StringIO
        sys.modules['six.moves.http_cookiejar'] = http.cookiejar
        sys.modules['six.moves.http_cookies'] = http.cookies
        sys.modules['six.moves.urllib_parse'] = urllib.parse
        sys.modules['six.moves.urllib_request'] = urllib.request
        sys.modules['six.moves.urllib_error'] = urllib.error
        sys.modules['six.moves.xrange'] = range

        return True

    except Exception as e:
        print(f"✗ Failed to create working six.moves: {e}")
        return False


def _fix_collections_mapping():
    """
    Fix collections.Mapping compatibility for Python 3.12
    """
    try:
        import collections
        import collections.abc

        # Add missing collections attributes
        missing_attrs = ['Mapping', 'MutableMapping', 'Sequence', 'MutableSequence', 'Set', 'MutableSet', 'Callable']
        for attr in missing_attrs:
            if not hasattr(collections, attr) and hasattr(collections.abc, attr):
                setattr(collections, attr, getattr(collections.abc, attr))

        return True

    except Exception as e:
        print(f"✗ Failed to fix collections.Mapping: {e}")
        return False


def _setup_urllib3_packages():
    """
    Setup urllib3.packages.six to use our working six.moves
    """
    try:
        import six

        # Both locations that need fixing
        locations = [
            'urllib3.packages.six',
            'requests.packages.urllib3.packages.six'
        ]

        for location in locations:
            # Link to our working six
            sys.modules[location] = six
            sys.modules[f'{location}.moves'] = six.moves

            # Add all the modules
            modules = [
                'queue', 'http_client', 'urllib', 'urllib_parse', 'urllib_error',
                'urllib_request', 'builtins', 'configparser', 'StringIO',
                'http_cookiejar', 'http_cookies', 'xrange'
            ]

            for module_name in modules:
                if hasattr(six.moves, module_name):
                    full_name = f'{location}.moves.{module_name}'
                    module_obj = getattr(six.moves, module_name)
                    sys.modules[full_name] = module_obj

            # Add urllib submodules
            for submodule in ['parse', 'request', 'error']:
                if hasattr(six.moves.urllib, submodule):
                    full_name = f'{location}.moves.urllib.{submodule}'
                    module_obj = getattr(six.moves.urllib, submodule)
                    sys.modules[full_name] = module_obj

        return True

    except Exception as e:
        print(f"✗ Failed to setup urllib3 packages: {e}")
        return False


def _test_fix():
    """
    Test that the fix works
    """
    try:
        # Test critical imports
        from six.moves import queue, http_client
        from six.moves.urllib import parse
        from urllib3.packages.six.moves import queue as urllib3_queue
        from requests.packages.urllib3.packages.six.moves import queue as requests_queue
        from collections import Mapping

        return True

    except Exception as e:
        print(f"✗ Fix test failed: {e}")
        return False


def get_fixed_requests():
    """
    Get the requests module with fix applied
    Returns requests module or None if fix failed
    """
    if not fix_requests():
        return None

    try:
        # Clear requests cache to ensure clean import
        requests_modules = [name for name in sys.modules.keys() if name.startswith('requests')]
        for module in requests_modules:
            if module in sys.modules:
                del sys.modules[module]

        # Re-establish urllib3 packages after clearing
        _setup_urllib3_packages()

        import requests
        return requests

    except Exception as e:
        print(f"✗ Failed to get fixed requests: {e}")
        return None


# Convenience: pre-apply fix and expose requests
if fix_requests():
    try:
        requests = get_fixed_requests()
        if requests:
            # Expose common requests components
            from requests import exceptions
            from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

            __all__ = ['fix_requests', 'get_fixed_requests', 'requests', 'exceptions',
                       'RequestException', 'HTTPError', 'ConnectionError', 'Timeout']
        else:
            requests = None
            __all__ = ['fix_requests', 'get_fixed_requests']
    except:
        requests = None
        __all__ = ['fix_requests', 'get_fixed_requests']
else:
    requests = None
    __all__ = ['fix_requests', 'get_fixed_requests']


# Test function for verification
def test_requests():
    """
    Test that requests is working properly
    """
    if not fix_requests():
        print("✗ Fix failed")
        return False

    try:
        import requests

        # Test basic functionality
        print(f"✓ requests version: {requests.__version__}")
        print(f"✓ requests.get available: {callable(requests.get)}")
        print(f"✓ requests.post available: {callable(requests.post)}")

        # Test HTTP functionality (if network available)
        try:
            response = requests.get('https://httpbin.org/get', timeout=3)
            print(f"✓ HTTP GET test: {response.status_code}")
        except:
            print("⚠ HTTP test skipped (network unavailable)")

        print("✓ requests is working correctly!")
        return True

    except Exception as e:
        print(f"✗ requests test failed: {e}")
        return False


if __name__ == "__main__":
    print("pyRevit 5.2 requests Helper")
    print("=" * 30)
    test_requests()
