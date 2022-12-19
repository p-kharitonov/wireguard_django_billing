"""
Custom Signals sent on WireGuard interface status changes.
"""

from django.dispatch import Signal

interface_created = Signal()
"""Signal sent to emulate WireGuard's PostUp configuration option

Provides instance argument (sender instance).
"""

interface_deleted = Signal()
"""Signal sent to emulate WireGuard's PostDown configuration option

Provides instance argument (sender instance).
"""

