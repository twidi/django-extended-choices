#!/usr/bin/env python

from __future__ import unicode_literals

import sys
if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

from django import forms

from .choices import Choices
from .fields import NamedExtendedChoiceFormField

MY_CHOICES = Choices(
    ('ONE', 1, 'One for the money'),
    ('TWO', 2, 'Two for the show'),
    ('THREE', 3, 'Three to get ready'),
)
MY_CHOICES.add_subset("ODD", ("ONE", "THREE"))


class FieldsTests(unittest.TestCase):
    """
    Testing the fields
    """
    def test_named_extended_choice_form_field(self):
        """
        Should accept only string, and should return the integer value.
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


class ChoicesTests(unittest.TestCase):
    """
    Testing the choices
    """
    def test_attributes_and_keys(self):
        self.assertEqual(MY_CHOICES.ONE, MY_CHOICES['ONE'])
        with self.assertRaises(AttributeError):
            MY_CHOICES.FORTY_TWO
        with self.assertRaises(KeyError):
            MY_CHOICES['FORTY_TWO']

        # should work for all attributes
        self.assertEqual(MY_CHOICES.CHOICES, MY_CHOICES['CHOICES'])

    def test_simple_choice(self):
        self.assertEqual(MY_CHOICES.CHOICES,(
            (1, "One for the money"),
            (2, "Two for the show"),
            (3, "Three to get ready"),
        ))
        self.assertEqual(MY_CHOICES.CHOICES_DICT, {
            1: 'One for the money',
            2: 'Two for the show',
            3: 'Three to get ready'
        })
        self.assertEqual(MY_CHOICES.REVERTED_CHOICES_DICT,{
            'One for the money': 1,
            'Three to get ready': 3,
            'Two for the show': 2
        })
        self.assertEqual(MY_CHOICES.CHOICES_CONST_DICT,{
            'ONE': 1,
            'TWO': 2,
            'THREE': 3
        })
        self.assertEqual(MY_CHOICES.REVERTED_CHOICES_CONST_DICT, {
            1: 'ONE',
            2: 'TWO',
            3: 'THREE'
        })

    def test__contains__(self):
        self.assertTrue(MY_CHOICES.ONE in MY_CHOICES)

    def test__iter__(self):
        self.assertEqual([k for k, v in MY_CHOICES], [1, 2, 3])

    def test_subset(self):
        self.assertEqual(MY_CHOICES.ODD,(
            (1, 'One for the money'),
            (3, 'Three to get ready')
        ))
        self.assertEqual(MY_CHOICES.ODD_CONST_DICT,{'ONE': 1, 'THREE': 3})

    def test_unique_values(self):
        self.assertRaises(ValueError, Choices, ('TWO', 4, 'Deux'), ('FOUR', 4, 'Quatre'))

    def test_unique_constants(self):
        self.assertRaises(ValueError, Choices, ('TWO', 2, 'Deux'), ('TWO', 4, 'Quatre'))

    def test_retrocompatibility(self):
        OTHER_CHOICES = Choices(
            ('TWO', 2, 'Deux'),
            ('FOUR', 4, 'Quatre'),
            name="EVEN"
        )
        OTHER_CHOICES.add_choices("ODD",
            ('ONE', 1, 'Un'),
            ('THREE', 3, 'Trois'),
        )
        self.assertEqual(OTHER_CHOICES.CHOICES, (
            (2, 'Deux'),
            (4, 'Quatre'),
            (1, 'Un'),
            (3, 'Trois')
        ))
        self.assertEqual(OTHER_CHOICES.ODD, ((1, 'Un'), (3, 'Trois')))
        self.assertEqual(OTHER_CHOICES.EVEN, ((2, 'Deux'), (4, 'Quatre')))

    def test_dict_class(self):
        if sys.version_info >= (2, 7):
            from collections import OrderedDict
        else:
            from django.utils.datastructures import SortedDict as OrderedDict

        OTHER_CHOICES = Choices(
            ('ONE', 1, 'One for the money'),
            ('TWO', 2, 'Two for the show'),
            ('THREE', 3, 'Three to get ready'),
            dict_class = OrderedDict
        )
        OTHER_CHOICES.add_subset("ODD", ("ONE", "THREE"))

        for attr in (
                # normal choice
                'CHOICES_DICT',
                'REVERTED_CHOICES_DICT',
                'CHOICES_CONST_DICT',
                'REVERTED_CHOICES_CONST_DICT',
                # subset
                'ODD_DICT',
                'REVERTED_ODD_DICT',
                'ODD_CONST_DICT',
                'REVERTED_ODD_CONST_DICT',
            ):
            self.assertFalse(isinstance(getattr(MY_CHOICES, attr), OrderedDict))
            self.assertTrue(isinstance(getattr(OTHER_CHOICES, attr), OrderedDict))


if __name__ == "__main__":
    unittest.main()