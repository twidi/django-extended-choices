# -*- coding: utf-8 -*-
from django.test import TestCase
from django import forms

from extended_choices.choices import Choices
from extended_choices.fields import NamedExtendedChoiceFormField

MY_CHOICES = Choices(
   ('ONE', 1, u'One for the money'),
   ('TWO', 2, u'Two for the show'),
   ('THREE', 3, u'Three to get ready'),
)

class FieldsTests(TestCase):
    """
    Testing the fields
    """
    def test_named_extended_choice_form_field(self):
        """
        Should return accept only string, and should return the integer value.
        """
        field = NamedExtendedChoiceFormField(choices=MY_CHOICES)
        # Should work with lowercase
        self.assertEqual(field.clean("one"), 1)
        # Should word with uppercase
        self.assertEqual(field.clean("ONE"), 1)
        # Should not validate with wrong name
        self.assertRaises(forms.ValidationError, field.clean, "FOUR")
        # Should not validate with integer
        self.assertRaises(forms.ValidationError, field.clean, 1)



