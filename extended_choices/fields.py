"""Provides a form field for django to use constants instead of values as available values.

Notes
-----

The documentation format in this file is `numpydoc`_.

.. _numpydoc: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

"""

from __future__ import unicode_literals

import six

from django import forms

from . import Choices


class NamedExtendedChoiceFormField(forms.Field):
    """Field to use with choices where values are constant names instead of choice values.

    Should not be very useful in normal HTML form, but if API validation is done via a form, it
    will to have more readable constants in the API that values
    """
    def __init__(self, choices, *args, **kwargs):
        """Override to ensure that the ``choices`` argument is a ``Choices`` object."""

        super(NamedExtendedChoiceFormField, self).__init__(*args, **kwargs)

        if not isinstance(choices, Choices):
            raise ValueError("`choices` must be an instance of `extended_choices.Choices`.")

        self.choices = choices

    def to_python(self, value):
        """Convert the constant to the real choice value."""

        # ``is_required`` is already checked in ``validate``.
        if value is None:
            return None

        # Validate the type.
        if not isinstance(value, six.string_types):
            raise forms.ValidationError(
                "Invalid value type (should be a string).",
                code='invalid-choice-type',
            )

        # Get the constant from the choices object, raising if it doesn't exist.
        try:
            final = getattr(self.choices, value)
        except AttributeError:
            available = '[%s]' % ', '.join(self.choices.constants)
            raise forms.ValidationError(
                "Invalid value (not in available choices. Available ones are: %s" % available,
                code='non-existing-choice',
            )

        return final
