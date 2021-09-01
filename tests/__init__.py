# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    from trytond.modules.welding_certification.tests.test_welding_certification import suite  # noqa: E501
except ImportError:
    from .test_welding_certification import suite

__all__ = ['suite']
