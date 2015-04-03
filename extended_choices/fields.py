from __future__ import unicode_literals

from past.builtins import basestring

from django import forms

from . import Choices

class NamedExtendedChoiceFormField(forms.Field):
    """
    Special fields, where the values are the constants names instead of the
    integer (could be useful for example for an API).
    Should not be very userful in normal HTML form life, but we need one because
    we use forms to do REST parameters validation.
    """
    def __init__(self, choices, *args, **kwargs):
        """
        Choices must be instance of ``extended_choices.Choice``.
        """
        super(NamedExtendedChoiceFormField, self).__init__(*args, **kwargs)
        if not isinstance(choices, Choices):
            raise ValueError("choices must be an instance of extended_choices.Choices")
        self.choices = choices

    def to_python(self, value):
        """
        Convert the named value to the internal integer.
        """
        # is_required is checked in validate
        if value is None: return None
        if not isinstance(value, basestring):
            raise forms.ValidationError("Invalid value format.")
        try:
            final = getattr(self.choices, value.upper())
        except AttributeError:
            raise forms.ValidationError("Invalid value.")
        return final



