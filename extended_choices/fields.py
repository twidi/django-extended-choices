# -*- coding: utf-8 -*-

from django import forms
from django.db import models
from django.db.models import ImageField
from django.utils.encoding import smart_unicode
from django.template.defaultfilters import filesizeformat

from django.utils.translation import ugettext_lazy as _
from extended_choices import Choices

class NamedExtendedChoiceFormField(forms.Field):
    """
    Special fields, where the values are the constants names instead of the 
    integer (could be usefull for example for an API).
    Should not be very userfull in normal HTML form life, but we need one because
    we use forms to do REST parameters validation. 
    """
    def __init__(self, choices=(), required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        """
        Choices must be instance of ``extended_choices.Choice``.
        """
        super(NamedExtendedChoiceFormField, self).__init__(required=required, 
               widget=widget, label=label, initial=initial, help_text=help_text,
               *args, **kwargs)
        if not isinstance(choices, Choices):
            raise ValueError("choices must be an instance of extended_choices.Choices")
        self.choices = choices
    
    def to_python(self, value):
        """
        Convert the named value to the internal integer.
        """
        # is_required is checked in validate
        if value is None: return None
        if not isinstance(value, (str, unicode)):
            raise forms.ValidationError("Invalid value format.")
        try:
            final = getattr(self.choices, value.upper())
        except AttributeError:
            raise forms.ValidationError("Invalid value.")
        return final
    
    

