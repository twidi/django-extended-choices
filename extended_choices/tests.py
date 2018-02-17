#!/usr/bin/env python

"""Tests for the ``extended_choices`` module.

Notes
-----

The documentation format in this file is numpydoc_.

.. _numpydoc: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

"""

from __future__ import unicode_literals

from copy import copy, deepcopy

try:
    import cPickle as pickle
except ImportError:
    import pickle

from collections import OrderedDict
import unittest

import django


# Minimal django conf to test a real field.
from django.conf import settings
settings.configure(DATABASE_ENGINE='sqlite3')

from django.core.exceptions import ValidationError
from django.utils.functional import Promise
from django.utils.translation import ugettext_lazy

from .choices import Choices, OrderedChoices, AutoDisplayChoices, AutoChoices
from .fields import NamedExtendedChoiceFormField
from .helpers import ChoiceAttributeMixin, ChoiceEntry


class BaseTestCase(unittest.TestCase):
    """Base test case that define a test ``Choices`` instance with a subset."""

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.MY_CHOICES = None
        self.init_choices()

    def init_choices(self):

        self.MY_CHOICES = Choices(
            ('ONE', 1, 'One for the money', {'one': 'money'}),
            ('TWO', 2, 'Two for the show'),
            ('THREE', 3, 'Three to get ready'),
        )
        self.MY_CHOICES.add_subset("ODD", ("ONE", "THREE"))


class FieldsTestCase(BaseTestCase):
    """Tests of the ``NamedExtendedChoiceFormField`` field."""

    def test_enforce_passing_a_choices(self):
        """Test that the field class only accepts a ``Choices`` object for its ``choices`` arg."""

        # Test with default choices tuple.
        with self.assertRaises(ValueError):
            NamedExtendedChoiceFormField(choices=(
                ('ONE', 1, 'One for the money'),
                ('TWO', 2, 'Two for the show'),
                ('THREE', 3, 'Three to get ready'),
            ))

        # Test with something else unrelated.
        with self.assertRaises(ValueError):
            NamedExtendedChoiceFormField(choices=1)

        # Test with a ``Choices`` object.
        field = NamedExtendedChoiceFormField(choices=self.MY_CHOICES)
        self.assertEqual(field.choices, self.MY_CHOICES)

    def test_named_extended_choice_form_field_validation(self):
        """Test that it only validation when it receives an existing constant name."""

        field = NamedExtendedChoiceFormField(choices=self.MY_CHOICES)

        # Should respect the constant case.
        self.assertEqual(field.clean('ONE'), 1)
        self.assertEqual(field.clean('TWO'), 2)

        with self.assertRaises(ValidationError) as raise_context:
            field.clean('one')
        self.assertEqual(raise_context.exception.code, 'non-existing-choice')

        # Should not validate with non-existing constant.
        with self.assertRaises(ValidationError) as raise_context:
            field.clean('FOUR')
        self.assertEqual(raise_context.exception.code, 'non-existing-choice')

        # Should fail early if not a string.
        with self.assertRaises(ValidationError) as raise_context:
            field.clean(1)
        self.assertEqual(raise_context.exception.code, 'invalid-choice-type')


class ChoicesTestCase(BaseTestCase):
    """Test the ``Choices`` class."""

    def test_should_behave_as_expected_by_django(self):
        """Test that it can be used by django, ie a list of tuple (value, display name)."""

        expected = (
            (1, 'One for the money'),
            (2, 'Two for the show'),
            (3, 'Three to get ready'),
        )

        # Test access to the whole expected tuple
        self.assertEqual(self.MY_CHOICES, expected)
        self.assertEqual(self.MY_CHOICES.choices, expected)

        # Test access to each tuple
        self.assertEqual(self.MY_CHOICES[0], expected[0])
        self.assertEqual(self.MY_CHOICES[2], expected[2])

    def test_should_be_accepted_by_django(self):
        """Test that a django field really accept a ``Choices`` instance."""

        from django.db.models import IntegerField
        field = IntegerField(choices=self.MY_CHOICES, default=self.MY_CHOICES.ONE)

        self.assertEqual(field.choices, self.MY_CHOICES)

        # No errors in ``_check_choices_``, Django 1.7+
        if django.VERSION >= (1, 7):
            self.assertEqual(field._check_choices(), [])

        # Test validation
        field.validate(1, None)

        with self.assertRaises(ValidationError) as raise_context:
            field.validate(4, None)

        # Check exception code, only in Django 1.6+
        if django.VERSION >= (1, 6):
            self.assertEqual(raise_context.exception.code, 'invalid_choice')

    def test_constants_attributes_should_return_values(self):
        """Test that each constant is an attribute returning the value."""

        self.assertEqual(self.MY_CHOICES.ONE, 1)
        self.assertEqual(self.MY_CHOICES.THREE, 3)

        with self.assertRaises(AttributeError):
            self.MY_CHOICES.FOUR

    def test_attributes_should_be_accessed_by_keys(self):
        """Test that each constant is accessible by key."""

        self.assertIs(self.MY_CHOICES['ONE'], self.MY_CHOICES.ONE)
        self.assertIs(self.MY_CHOICES['THREE'], self.MY_CHOICES.THREE)

        with self.assertRaises(KeyError):
            self.MY_CHOICES['FOUR']

    def test_entries(self):
        """Test that ``entries`` holds ``ChoiceEntry`` instances with correct attributes."""

        self.assertIsInstance(self.MY_CHOICES.entries[0], ChoiceEntry)
        self.assertEqual(self.MY_CHOICES.entries[0], ('ONE', 1, 'One for the money'))
        self.assertEqual(self.MY_CHOICES.entries[0].constant, 'ONE')
        self.assertEqual(self.MY_CHOICES.entries[0].value, 1)
        self.assertEqual(self.MY_CHOICES.entries[0].display, 'One for the money')

        self.assertIsInstance(self.MY_CHOICES.entries[2], ChoiceEntry)
        self.assertEqual(self.MY_CHOICES.entries[2], ('THREE', 3, 'Three to get ready'))
        self.assertEqual(self.MY_CHOICES.entries[2].constant, 'THREE')
        self.assertEqual(self.MY_CHOICES.entries[2].value, 3)
        self.assertEqual(self.MY_CHOICES.entries[2].display, 'Three to get ready')

    def test_dicts(self):
        """Test that ``constants``, ``values`` and ``displays`` dicts behave as expected."""
        self.assertIsInstance(self.MY_CHOICES.constants, dict)
        self.assertIsInstance(self.MY_CHOICES.values, dict)
        self.assertIsInstance(self.MY_CHOICES.displays, dict)

        self.assertDictEqual(self.MY_CHOICES.constants, {
            'ONE': ('ONE', 1, 'One for the money'),
            'TWO': ('TWO', 2, 'Two for the show'),
            'THREE': ('THREE', 3, 'Three to get ready'),
        })
        self.assertDictEqual(self.MY_CHOICES.values, {
            1: ('ONE', 1, 'One for the money'),
            2: ('TWO', 2, 'Two for the show'),
            3: ('THREE', 3, 'Three to get ready'),
        })
        self.assertDictEqual(self.MY_CHOICES.displays, {
            'One for the money': ('ONE', 1, 'One for the money'),
            'Two for the show': ('TWO', 2, 'Two for the show'),
            'Three to get ready': ('THREE', 3, 'Three to get ready'),
        })

    def test_adding_choices(self):
        """Test that we can add choices to an existing ``Choices`` instance."""
        self.MY_CHOICES.add_choices(
            ('FOUR', 4, 'And four to go'),
            ('FIVE', 5, '... but Five is not in the song'),
        )

        # Test django expected tuples
        expected = (
            (1, 'One for the money'),
            (2, 'Two for the show'),
            (3, 'Three to get ready'),
            (4, 'And four to go'),
            (5, '... but Five is not in the song'),
        )

        self.assertEqual(self.MY_CHOICES, expected)
        self.assertEqual(self.MY_CHOICES.choices, expected)

        # Test entries

        self.assertIsInstance(self.MY_CHOICES.entries[3], ChoiceEntry)
        self.assertEqual(self.MY_CHOICES.entries[3].constant, 'FOUR')
        self.assertEqual(self.MY_CHOICES.entries[3].value, 4)
        self.assertEqual(self.MY_CHOICES.entries[3].display, 'And four to go')

        self.assertIsInstance(self.MY_CHOICES.entries[4], ChoiceEntry)
        self.assertEqual(self.MY_CHOICES.entries[4].constant, 'FIVE')
        self.assertEqual(self.MY_CHOICES.entries[4].value, 5)
        self.assertEqual(self.MY_CHOICES.entries[4].display, '... but Five is not in the song')

        # Test dicts
        self.assertEqual(len(self.MY_CHOICES.constants), 5)
        self.assertEqual(len(self.MY_CHOICES.values), 5)
        self.assertEqual(len(self.MY_CHOICES.displays), 5)

        self.assertEqual(self.MY_CHOICES.constants['FOUR'],
                         ('FOUR', 4, 'And four to go'))
        self.assertEqual(self.MY_CHOICES.constants['FIVE'],
                         ('FIVE', 5, '... but Five is not in the song'))
        self.assertEqual(self.MY_CHOICES.values[4],
                         ('FOUR', 4, 'And four to go'))
        self.assertEqual(self.MY_CHOICES.values[5],
                         ('FIVE', 5, '... but Five is not in the song'))
        self.assertEqual(self.MY_CHOICES.displays['And four to go'],
                         ('FOUR', 4, 'And four to go'))
        self.assertEqual(self.MY_CHOICES.displays['... but Five is not in the song'],
                         ('FIVE', 5, '... but Five is not in the song'))

    def test_adding_choice_to_create_subset(self):
        """Test that we can create a subset while adding choices.

        This test test both ways of setting a name for a subset to create when adding choices,
        resetting ``MY_CHOICES`` between both tests, and calling ``test_subset`` in both cases.

        """

        def test_subset():
            # Quick check of the whole ``Choices`` (see ``test_adding_choices`` for full test)
            self.assertEqual(len(self.MY_CHOICES), 5)
            self.assertEqual(len(self.MY_CHOICES.entries), 5)
            self.assertEqual(len(self.MY_CHOICES.constants), 5)

            # Check that we have a subset
            self.assertIsInstance(self.MY_CHOICES.EXTENDED, Choices)

            # And that it contains the added choices (see ``test_creating_subset`` for full test)
            self.assertEqual(self.MY_CHOICES.EXTENDED, (
                (4, 'And four to go'),
                (5, '... but Five is not in the song'),
            ))

        # First test by setting the subset as first argument
        self.MY_CHOICES.add_choices(
            'EXTENDED',
            ('FOUR', 4, 'And four to go'),
            ('FIVE', 5, '... but Five is not in the song'),
        )

        test_subset()

        # Reset to remove added choices and subset
        self.init_choices()

        # Then test by setting the subset as named argument
        self.MY_CHOICES.add_choices(
            ('FOUR', 4, 'And four to go'),
            ('FIVE', 5, '... but Five is not in the song'),
            name='EXTENDED'
        )

        test_subset()

        # Using both first argument and a named argument should fail
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                'EXTENDED',
                ('FOUR', 4, 'And four to go'),
                ('FIVE', 5, '... but Five is not in the song'),
                name='EXTENDED'
            )

    def test_extracting_subset(self):
        """Test that we can extract a subset of choices."""

        subset = self.MY_CHOICES.extract_subset('ONE', 'TWO')

        self.assertIsInstance(subset, Choices)

        # Test django expected tuples
        expected = (
            (1, 'One for the money'),
            (2, 'Two for the show'),
        )

        self.assertEqual(subset, expected)
        self.assertEqual(subset.choices, expected)

        # Test entries
        self.assertEqual(len(subset.entries), 2)
        self.assertIsInstance(subset.entries[0], ChoiceEntry)
        self.assertEqual(subset.entries[0].constant, 'ONE')
        self.assertEqual(subset.entries[0].value, 1)
        self.assertEqual(subset.entries[0].display, 'One for the money')

        self.assertIsInstance(subset.entries[1], ChoiceEntry)
        self.assertEqual(subset.entries[1].constant, 'TWO')
        self.assertEqual(subset.entries[1].value, 2)
        self.assertEqual(subset.entries[1].display, 'Two for the show')

        # Test dicts
        self.assertEqual(len(subset.constants), 2)
        self.assertEqual(len(subset.values), 2)
        self.assertEqual(len(subset.displays), 2)

        self.assertIs(subset.constants['ONE'],
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(subset.constants['TWO'],
                      self.MY_CHOICES.constants['TWO'])
        self.assertIs(subset.values[1],
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(subset.values[2],
                      self.MY_CHOICES.constants['TWO'])
        self.assertIs(subset.displays['One for the money'],
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(subset.displays['Two for the show'],
                      self.MY_CHOICES.constants['TWO'])

        # Test ``in``
        self.assertIn(1, subset)
        self.assertNotIn(4, subset)

    def test_creating_subset(self):
        """Test that we can add subset of choices."""

        self.assertIsInstance(self.MY_CHOICES.ODD, Choices)

        # Test django expected tuples
        expected = (
            (1, 'One for the money'),
            (3, 'Three to get ready'),
        )

        self.assertEqual(self.MY_CHOICES.ODD, expected)
        self.assertEqual(self.MY_CHOICES.ODD.choices, expected)

        # Test entries
        self.assertEqual(len(self.MY_CHOICES.ODD.entries), 2)
        self.assertIsInstance(self.MY_CHOICES.ODD.entries[0], ChoiceEntry)
        self.assertEqual(self.MY_CHOICES.ODD.entries[0].constant, 'ONE')
        self.assertEqual(self.MY_CHOICES.ODD.entries[0].value, 1)
        self.assertEqual(self.MY_CHOICES.ODD.entries[0].display, 'One for the money')

        self.assertIsInstance(self.MY_CHOICES.ODD.entries[1], ChoiceEntry)
        self.assertEqual(self.MY_CHOICES.ODD.entries[1].constant, 'THREE')
        self.assertEqual(self.MY_CHOICES.ODD.entries[1].value, 3)
        self.assertEqual(self.MY_CHOICES.ODD.entries[1].display, 'Three to get ready')

        # Test dicts
        self.assertEqual(len(self.MY_CHOICES.ODD.constants), 2)
        self.assertEqual(len(self.MY_CHOICES.ODD.values), 2)
        self.assertEqual(len(self.MY_CHOICES.ODD.displays), 2)

        self.assertIs(self.MY_CHOICES.ODD.constants['ONE'],
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(self.MY_CHOICES.ODD.constants['THREE'],
                      self.MY_CHOICES.constants['THREE'])
        self.assertIs(self.MY_CHOICES.ODD.values[1],
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(self.MY_CHOICES.ODD.values[3],
                      self.MY_CHOICES.constants['THREE'])
        self.assertIs(self.MY_CHOICES.ODD.displays['One for the money'],
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(self.MY_CHOICES.ODD.displays['Three to get ready'],
                      self.MY_CHOICES.constants['THREE'])

        # Test ``in``
        self.assertIn(1, self.MY_CHOICES.ODD)
        self.assertNotIn(4, self.MY_CHOICES.ODD)

    def test_should_not_be_able_to_add_choices_to_a_subset(self):
        """Test that an exception is raised when trying to add new choices to a subset."""

        # Using a subset created by ``add_subset``.
        with self.assertRaises(RuntimeError):
            self.MY_CHOICES.ODD.add_choices(
                ('FOO', 10, 'foo'),
                ('BAR', 20, 'bar'),
            )

        # Using a subset created by ``add_choices``.
        self.MY_CHOICES.add_choices(
            ('FOUR', 4, 'And four to go'),
            ('FIVE', 5, '... but Five is not in the song'),
            name='EXTENDED'
        )
        with self.assertRaises(RuntimeError):
            self.MY_CHOICES.EXTENDED.add_choices(
                ('FOO', 10, 'foo'),
                ('BAR', 20, 'bar'),
            )

    def test_validating_added_choices(self):
        """Test that added choices can be added."""

        # Cannot add an existing constant.
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                ('ONE', 11, 'Another ONE'),
                ('FOUR', 4, 'And four to go'),
            )

        # Cannot add an existing value.
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                ('ONEBIS', 1, 'Another 1'),
                ('FOUR', 4, 'And four to go'),
            )

        # Cannot add two choices with the same name.
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                ('FOUR', 4, 'And four to go'),
                ('FOUR', 44, 'And four to go, bis'),
            )

        # Cannot add two choices with the same value.
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                ('FOUR', 4, 'And four to go'),
                ('FOURBIS', 4, 'And four to go, bis'),
            )

        # Cannot use existing attributes.
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                ('FOUR', 4, 'And four to go'),
                ('choices', 123, 'Existing attribute'),
            )

        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_choices(
                ('FOUR', 4, 'And four to go'),
                ('add_choices', 123, 'Existing attribute'),
            )

    def test_validating_subset(self):
        """Test that new subset is valid."""

        # Using a name that is already an attribute
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_subset("choices", ("ONE", "THREE"))

        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_subset("add_choices", ("ONE", "THREE"))

        # Using an undefined constant
        with self.assertRaises(ValueError):
            self.MY_CHOICES.add_subset("EVEN", ("TWO", "FOUR"))

    def test_for_methods(self):
        """Test the ``for_constant``, ``for_value`` and ``for_display`` methods."""

        self.assertIs(self.MY_CHOICES.for_constant('ONE'),
                      self.MY_CHOICES.constants['ONE'])
        self.assertIs(self.MY_CHOICES.for_value(2),
                      self.MY_CHOICES.values[2])
        self.assertIs(self.MY_CHOICES.for_display('Three to get ready'),
                      self.MY_CHOICES.displays['Three to get ready'])

        with self.assertRaises(KeyError):
            self.MY_CHOICES.for_constant('FOUR')

        with self.assertRaises(KeyError):
            self.MY_CHOICES.for_value(4)

        with self.assertRaises(KeyError):
            self.MY_CHOICES.for_display('And four to go')

    def test_has_methods(self):
        """Test the ``has_constant``, ``has_value`` and ``has_display`` methods."""

        self.assertTrue(self.MY_CHOICES.has_constant('ONE'))
        self.assertTrue(self.MY_CHOICES.has_value(2))
        self.assertTrue(self.MY_CHOICES.has_display('Three to get ready'))

        self.assertFalse(self.MY_CHOICES.has_constant('FOUR'))
        self.assertFalse(self.MY_CHOICES.has_value(4))
        self.assertFalse(self.MY_CHOICES.has_display('And four to go'))

    def test__contains__(self):
        """Test the ``__contains__`` method."""

        self.assertIn(self.MY_CHOICES.ONE, self.MY_CHOICES)
        self.assertTrue(self.MY_CHOICES.__contains__(self.MY_CHOICES.ONE))
        self.assertIn(1, self.MY_CHOICES)
        self.assertTrue(self.MY_CHOICES.__contains__(1))
        self.assertIn(3, self.MY_CHOICES)
        self.assertTrue(self.MY_CHOICES.__contains__(3))
        self.assertNotIn(4, self.MY_CHOICES)
        self.assertFalse(self.MY_CHOICES.__contains__(4))

    def test__getitem__(self):
        """Test the ``__getitem__`` method."""

        # Access to constants.
        self.assertEqual(self.MY_CHOICES['ONE'], 1)
        self.assertEqual(self.MY_CHOICES.__getitem__('ONE'), 1)

        self.assertEqual(self.MY_CHOICES['THREE'], 3)
        self.assertEqual(self.MY_CHOICES.__getitem__('THREE'), 3)

        with self.assertRaises(KeyError):
            self.MY_CHOICES['FOUR']
        with self.assertRaises(KeyError):
            self.MY_CHOICES.__getitem__('FOUR')

        one = (1, 'One for the money')
        three = (3, 'Three to get ready')

        # Access to default list entries
        self.assertEqual(self.MY_CHOICES[0], one)
        self.assertEqual(self.MY_CHOICES.__getitem__(0), one)

        self.assertEqual(self.MY_CHOICES[2], three)
        self.assertEqual(self.MY_CHOICES.__getitem__(2), three)

        with self.assertRaises(IndexError):
            self.MY_CHOICES[3]
        with self.assertRaises(IndexError):
            self.MY_CHOICES.__getitem__(3)

    def test_it_should_work_with_django_promises(self):
        """Test that it works with django promises, like ``ugettext_lazy``."""

        # Init django, only needed starting from django 1.7
        if django.VERSION >= (1, 7):
            django.setup()

        choices = Choices(
            ('ONE', 1, ugettext_lazy('one')),
            ('TWO', 2, ugettext_lazy('two')),
        )

        # Key in ``displays`` dict should be promises
        self.assertIsInstance(list(choices.displays.keys())[0], Promise)

        # And that they can be retrieved
        self.assertTrue(choices.has_display(ugettext_lazy('one')))
        self.assertEqual(choices.displays[ugettext_lazy('two')].value, 2)

        return

    def test_pickle_choice_attribute(self):
        """Test that a choice attribute could be pickled and unpickled."""

        value = self.MY_CHOICES.ONE

        pickled_value = pickle.dumps(value)
        unpickled_value = pickle.loads(pickled_value)

        self.assertEqual(unpickled_value, value)
        self.assertEqual(unpickled_value.choice_entry, value.choice_entry)
        self.assertEqual(unpickled_value.constant, 'ONE')
        self.assertEqual(unpickled_value.display, 'One for the money')
        self.assertEqual(unpickled_value.value, 1)
        self.assertEqual(unpickled_value.one, 'money')
        self.assertEqual(unpickled_value.display.one, 'money')

    def test_pickle_choice_entry(self):
        """Test that a choice entry could be pickled and unpickled."""

        entry = self.MY_CHOICES.ONE.choice_entry

        pickled_entry = pickle.dumps(entry)
        unpickled_entry = pickle.loads(pickled_entry)

        self.assertEqual(unpickled_entry, entry)
        self.assertEqual(unpickled_entry.constant, 'ONE')
        self.assertEqual(unpickled_entry.display, 'One for the money')
        self.assertEqual(unpickled_entry.value, 1)
        self.assertEqual(unpickled_entry.one, 'money')
        self.assertEqual(unpickled_entry.display.one, 'money')

    def test_pickle_choice(self):
        """Test that a choices object could be pickled and unpickled."""

        # Simple choice
        pickled_choices = pickle.dumps(self.MY_CHOICES)
        unpickled_choices = pickle.loads(pickled_choices)

        self.assertEqual(unpickled_choices, self.MY_CHOICES)
        self.assertEqual(unpickled_choices.ONE.one, 'money')
        self.assertEqual(unpickled_choices.ONE.display.one, 'money')

        # With a name, extra arguments and subsets
        OTHER_CHOICES = Choices(
            'ALL',
            ('ONE', 1, 'One for the money'),
            ('TWO', 2, 'Two for the show'),
            ('THREE', 3, 'Three to get ready'),
            dict_class=OrderedDict,
            mutable=False
        )
        OTHER_CHOICES.add_subset("ODD", ("ONE", "THREE"))
        OTHER_CHOICES.add_subset("EVEN", ("TWO", ))

        pickled_choices = pickle.dumps(OTHER_CHOICES)
        unpickled_choices = pickle.loads(pickled_choices)

        self.assertEqual(unpickled_choices, OTHER_CHOICES)
        self.assertEqual(unpickled_choices.dict_class, OrderedDict)
        self.assertFalse(unpickled_choices._mutable)
        self.assertEqual(unpickled_choices.subsets, OTHER_CHOICES.subsets)
        self.assertEqual(unpickled_choices.ALL, OTHER_CHOICES.ALL)
        self.assertEqual(unpickled_choices.ODD, OTHER_CHOICES.ODD)
        self.assertEqual(unpickled_choices.EVEN, OTHER_CHOICES.EVEN)

    def test_django_ugettext_lazy(self):
        """Test that a choices object using ugettext_lazy could be pickled and copied."""

        lazy_choices = Choices(
            ('ONE', 1, ugettext_lazy('One for the money')),
            ('TWO', 2, ugettext_lazy('Two for the show')),
            ('THREE', 3, ugettext_lazy('Three to get ready')),
        )

        # try to pickel it, it should not raise
        pickled_choices = pickle.dumps(lazy_choices)
        unpickled_choices = pickle.loads(pickled_choices)

        self.assertEqual(unpickled_choices, lazy_choices)

        # try to copy it, it should not raise
        copied_choices = copy(lazy_choices)
        self.assertEqual(copied_choices, lazy_choices)

        # try to deep-copy it, it should not raise
        deep_copied_choices = deepcopy(lazy_choices)
        self.assertEqual(deep_copied_choices, lazy_choices)

    def test_bool(self):
        """Test that having 0 or "" return `False` in a boolean context"""

        bool_choices = Choices(
            ('', 0, ''),
            ('FOO', 1, 'bar'),
        )

        first = bool_choices.for_value(0)
        second = bool_choices.for_value(1)

        self.assertFalse(first.constant)
        self.assertFalse(first.value)
        self.assertFalse(first.display)

        self.assertTrue(second.constant)
        self.assertTrue(second.value)
        self.assertTrue(second.display)

    def test_dict_class(self):
        """Test that the dict_class argument is taken into account"""

        dict_choices = Choices(
            ('FOO', 1, 'foo'),
            ('BAR', 2, 'bar')
        )

        self.assertIs(dict_choices.dict_class, dict)
        self.assertIsInstance(dict_choices.constants, dict)
        self.assertIsInstance(dict_choices.values, dict)
        self.assertIsInstance(dict_choices.displays, dict)

        ordered_dict_choices = Choices(
            ('FOO', 1, 'foo'),
            ('BAR', 2, 'bar'),
            dict_class=OrderedDict
        )

        self.assertIs(ordered_dict_choices.dict_class, OrderedDict)
        self.assertIsInstance(ordered_dict_choices.constants, OrderedDict)
        self.assertIsInstance(ordered_dict_choices.values, OrderedDict)
        self.assertIsInstance(ordered_dict_choices.displays, OrderedDict)

        ordered_choices = OrderedChoices(
            ('FOO', 1, 'foo'),
            ('BAR', 2, 'bar'),
        )

        self.assertIs(ordered_choices.dict_class, OrderedDict)
        self.assertIsInstance(ordered_choices.constants, OrderedDict)
        self.assertIsInstance(ordered_choices.values, OrderedDict)
        self.assertIsInstance(ordered_choices.displays, OrderedDict)

    def test_passing_choice_entry(self):
        MY_CHOICES = Choices(
            ChoiceEntry(('A', 'aa', 'aaa', {'foo': 'bar'})),
            ('B', 'bb', 'bbb'),
        )
        self.assertEqual(MY_CHOICES.A.value, 'aa')
        self.assertEqual(MY_CHOICES.A.display, 'aaa')
        self.assertEqual(MY_CHOICES.B.value, 'bb')
        self.assertEqual(MY_CHOICES.B.display, 'bbb')

    def test_accessing_attributes(self):
        MY_CHOICES = Choices(
            ('FOO', 1, 'foo', {'foo': 'foo1', 'bar': 'bar1'}),
            ('BAR', 2, 'bar', {'foo': 'foo2', 'bar': 'bar2'}),
        )
        self.assertEqual(MY_CHOICES.FOO.choice_entry.foo, 'foo1')
        self.assertEqual(MY_CHOICES.FOO.foo, 'foo1')
        self.assertEqual(MY_CHOICES.FOO.constant.foo, 'foo1')
        self.assertEqual(MY_CHOICES.FOO.value.foo, 'foo1')
        self.assertEqual(MY_CHOICES.FOO.display.foo, 'foo1')
        self.assertEqual(MY_CHOICES.FOO.choice_entry.bar, 'bar1')
        self.assertEqual(MY_CHOICES.BAR.choice_entry.foo, 'foo2')
        self.assertEqual(MY_CHOICES.BAR.foo, 'foo2')
        self.assertEqual(MY_CHOICES.BAR.choice_entry.bar, 'bar2')
        self.assertEqual(MY_CHOICES.BAR.bar, 'bar2')

    def test_invalid_attributes(self):
        for invalid_key in {'constant', 'value', 'display'}:
            with self.assertRaises(AssertionError):
                Choices(('FOO', '1', 'foo', {invalid_key: 'xxx'}))


class ChoiceAttributeMixinTestCase(BaseTestCase):
    """Test the ``ChoiceAttributeMixin`` class."""

    choice_entry = ChoiceEntry(('FOO', 1, 'foo'))

    def test_it_should_respect_the_type(self):
        """A class based on ``ChoiceAttributeMixin`` should inherit from the other class too."""

        class StrChoiceAttribute(ChoiceAttributeMixin, str):
            pass

        str_attr = StrChoiceAttribute('f', self.choice_entry)
        self.assertEqual(str_attr, 'f')
        self.assertIsInstance(str_attr, str)

        class IntChoiceAttribute(ChoiceAttributeMixin, int):
            pass

        int_attr = IntChoiceAttribute(1, self.choice_entry)
        self.assertEqual(int_attr, 1)
        self.assertIsInstance(int_attr, int)

        class FloatChoiceAttribute(ChoiceAttributeMixin, float):
            pass

        float_attr = FloatChoiceAttribute(1.5, self.choice_entry)
        self.assertEqual(float_attr, 1.5)
        self.assertIsInstance(float_attr, float)

    def test_it_should_create_classes_on_the_fly(self):
        """Test that ``get_class_for_value works and cache its results."""

        # Empty list of cached classes to really test.
        ChoiceAttributeMixin._classes_by_type = {}

        # Create a class on the fly.
        IntClass = ChoiceAttributeMixin.get_class_for_value(1)
        self.assertEqual(IntClass.__name__, 'IntChoiceAttribute')
        self.assertIn(int, IntClass.mro())
        self.assertDictEqual(ChoiceAttributeMixin._classes_by_type, {
            int: IntClass
        })

        # Using the same type should return the same class as before.
        IntClass2 = ChoiceAttributeMixin.get_class_for_value(2)
        self.assertIs(IntClass2, IntClass2)

        int_attr = IntClass(1, self.choice_entry)
        self.assertEqual(int_attr, 1)
        self.assertIsInstance(int_attr, int)

        # Create another class on the fly.
        FloatClass = ChoiceAttributeMixin.get_class_for_value(1.5)
        self.assertEqual(FloatClass.__name__, 'FloatChoiceAttribute')
        self.assertIn(float, FloatClass.mro())
        self.assertDictEqual(ChoiceAttributeMixin._classes_by_type, {
            int: IntClass,
            float: FloatClass
        })

        float_attr = FloatClass(1.5, self.choice_entry)
        self.assertEqual(float_attr, 1.5)
        self.assertIsInstance(float_attr, float)

    def test_it_should_access_choice_entry_attributes(self):
        """Test that an instance can access the choice entry and its attributes."""
        IntClass = ChoiceAttributeMixin.get_class_for_value(1)
        attr = IntClass(1, self.choice_entry)

        # We should access the choice entry.
        self.assertEqual(attr.choice_entry, self.choice_entry)

        # And the attributes of the choice entry.
        self.assertEqual(attr.constant, self.choice_entry.constant)
        self.assertEqual(attr.value, self.choice_entry.value)
        self.assertEqual(attr.display, self.choice_entry.display)

    def test_it_should_work_with_django_promises(self):
        """Test that it works with django promises, like ``ugettext_lazy``."""

        # Init django, only needed starting from django 1.7
        if django.VERSION >= (1, 7):
            django.setup()

        value = ugettext_lazy('foo')
        klass = ChoiceAttributeMixin.get_class_for_value(value)
        attr = klass(value, self.choice_entry)

        self.assertIsInstance(attr, Promise)
        self.assertEqual(attr, ugettext_lazy('foo'))


class ChoiceEntryTestCase(BaseTestCase):
    """Test the ``ChoiceEntry`` class."""

    def test_it_should_act_as_a_normal_tuple(self):
        """Test that a ``ChoiceEntry`` instance acts as a real tuple."""

        # Test without additional attributes
        choice_entry = ChoiceEntry(('FOO', 1, 'foo'))
        self.assertIsInstance(choice_entry, tuple)
        self.assertEqual(choice_entry, ('FOO', 1, 'foo'))

        # Test with additional attributes
        choice_entry = ChoiceEntry(('FOO', 1, 'foo', {'bar': 1, 'baz': 2}))
        self.assertIsInstance(choice_entry, tuple)
        self.assertEqual(choice_entry, ('FOO', 1, 'foo'))

    def test_it_should_have_new_attributes(self):
        """Test that new specific attributes are accessible anv valid."""

        choice_entry = ChoiceEntry(('FOO', 1, 'foo'))

        self.assertEqual(choice_entry.constant, 'FOO')
        self.assertEqual(choice_entry.value, 1)
        self.assertEqual(choice_entry.display, 'foo')
        self.assertEqual(choice_entry.choice, (1, 'foo'))

    def test_new_attributes_are_instances_of_choices_attributes(self):
        """Test that the new attributes are instances of ``ChoiceAttributeMixin``."""

        choice_entry = ChoiceEntry(('FOO', 1, 'foo'))

        # 3 attributes should be choice attributes
        self.assertIsInstance(choice_entry.constant, ChoiceAttributeMixin)
        self.assertIsInstance(choice_entry.value, ChoiceAttributeMixin)
        self.assertIsInstance(choice_entry.display, ChoiceAttributeMixin)

        # As a choice attribute allow to access the other attributes of the choice entry,
        # check that it's really possible

        self.assertIs(choice_entry.constant.constant, choice_entry.constant)
        self.assertIs(choice_entry.constant.value, choice_entry.value)
        self.assertIs(choice_entry.constant.display, choice_entry.display)

        self.assertIs(choice_entry.value.constant, choice_entry.constant)
        self.assertIs(choice_entry.value.value, choice_entry.value)
        self.assertIs(choice_entry.value.display, choice_entry.display)

        self.assertIs(choice_entry.display.constant, choice_entry.constant)
        self.assertIs(choice_entry.display.value, choice_entry.value)
        self.assertIs(choice_entry.display.display, choice_entry.display)

        # Extreme test
        self.assertIs(choice_entry.display.value.constant.value.display.display.constant,
                      choice_entry.constant)

    def test_additional_attributes_are_saved(self):
        """Test that a dict passed as 4th tuple entry set its entries as attributes."""

        choice_entry = ChoiceEntry(('FOO', 1, 'foo', {'bar': 1, 'baz': 2}))
        self.assertEqual(choice_entry.bar, 1)
        self.assertEqual(choice_entry.baz, 2)

    def test_it_should_check_number_of_entries(self):
        """Test that it allows only tuples with 3 entries + optional attributes dict."""

        # Less than 3 shouldn't work
        with self.assertRaises(AssertionError):
            ChoiceEntry(('foo',))
        with self.assertRaises(AssertionError):
            ChoiceEntry((1, 'foo'))

        # More than 4 shouldn't work.
        with self.assertRaises(AssertionError):
            ChoiceEntry(('FOO', 1, 'foo', {'bar': 1, 'baz': 2}, 'QUZ'))
        with self.assertRaises(AssertionError):
            ChoiceEntry(('FOO', 1, 'foo', {'bar': 1, 'baz': 2}, 'QUZ', 'QUX'))

    def test_it_should_work_with_django_promises(self):
        """Test that ``ChoiceEntry`` class works with django promises, like ``ugettext_lazy``."""

        # Init django, only needed starting from django 1.7
        if django.VERSION >= (1, 7):
            django.setup()

        choice_entry = ChoiceEntry(('FOO', 1, ugettext_lazy('foo')))

        self.assertIsInstance(choice_entry.display, Promise)
        self.assertEqual(choice_entry.display, ugettext_lazy('foo'))

        self.assertEqual(choice_entry.display.constant, 'FOO')
        self.assertEqual(choice_entry.display.value, 1)
        self.assertEqual(choice_entry.display.display, ugettext_lazy('foo'))

    def test_it_should_raise_with_none_value(self):
        """Test that it's clear that we don't support None values."""

        with self.assertRaises(ValueError):
            ChoiceEntry(('FOO', None, 'foo'))


class AutoDisplayChoicesTestCase(BaseTestCase):

    def test_normal_usage(self):

        MY_CHOICES = AutoDisplayChoices(
            ('SIMPLE', 1),
            ('NOT_SIMPLE', 2),
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'Simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'Not simple')

    def test_pass_transform_function(self):

        MY_CHOICES = AutoDisplayChoices(
            ('SIMPLE', 1),
            ('NOT_SIMPLE', 2),
            display_transform=lambda const: const.lower()
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'not_simple')

    def test_override_transform_function(self):

        class MyAutoDisplayChoices(AutoDisplayChoices):
            display_transform = staticmethod(lambda const: const.lower())

        MY_CHOICES = MyAutoDisplayChoices(
            ('SIMPLE', 1),
            ('NOT_SIMPLE', 2),
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'not_simple')

        MY_CHOICES = MyAutoDisplayChoices(
            ('SIMPLE', 1),
            ('NOT_SIMPLE', 2),
            display_transform=lambda const: const.title()
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'Simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'Not_Simple')

    def test_adding_subset(self):

        MY_CHOICES = AutoDisplayChoices(('A', 'a'), ('B', 'b'), ('C', 'c'))
        MY_CHOICES.add_subset('AB', ['A', 'B'])

        self.assertEqual(MY_CHOICES.AB.constants, {
            'A': MY_CHOICES.A.choice_entry,
            'B': MY_CHOICES.B.choice_entry,
        })

    def test_passing_choice_entry(self):
        MY_CHOICES = AutoDisplayChoices(
            ChoiceEntry(('A', 'aa', 'aaa', {'foo': 'bar'})),
            ('B', 'bb'),
        )
        self.assertEqual(MY_CHOICES.A.value, 'aa')
        self.assertEqual(MY_CHOICES.A.display, 'aaa')
        self.assertEqual(MY_CHOICES.B.value, 'bb')
        self.assertEqual(MY_CHOICES.B.display, 'B')

    def test_passing_not_only_constant(self):
        MY_CHOICES = AutoDisplayChoices(
            ChoiceEntry(('A', 'aa', 'aaa', {'foo': 'bara'})),
            ('E', 'ee'),
            ('F', 'ff', {'foo': 'barf'}),
            ('G', 'gg', 'ggg'),
            ('H', 'hh', 'hhh', {'foo': 'barh'}),
        )

        self.assertEqual(MY_CHOICES.A.value, 'aa')
        self.assertEqual(MY_CHOICES.A.display, 'aaa')
        self.assertEqual(MY_CHOICES.A.foo, 'bara')
        self.assertEqual(MY_CHOICES.E.value, 'ee')
        self.assertEqual(MY_CHOICES.E.display, 'E')
        self.assertEqual(MY_CHOICES.F.value, 'ff')
        self.assertEqual(MY_CHOICES.F.display, 'F')
        self.assertEqual(MY_CHOICES.F.foo, 'barf')
        self.assertEqual(MY_CHOICES.G.value, 'gg')
        self.assertEqual(MY_CHOICES.G.display, 'ggg')
        self.assertEqual(MY_CHOICES.H.value, 'hh')
        self.assertEqual(MY_CHOICES.H.display, 'hhh')
        self.assertEqual(MY_CHOICES.H.foo, 'barh')

        MY_CHOICES.add_subset('ALL', ['A', 'E', 'F', 'G', 'H'])
        self.assertEqual(MY_CHOICES.ALL.constants, MY_CHOICES.constants)


class AutoChoicesTestCase(BaseTestCase):

    def test_normal_usage(self):

        MY_CHOICES = AutoChoices(
            'SIMPLE',
            ('NOT_SIMPLE', ),
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'Simple')
        self.assertEqual(MY_CHOICES.SIMPLE.value, 'simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'Not simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.value, 'not_simple')

    def test_pass_transform_functions(self):

        MY_CHOICES = AutoChoices(
            'SIMPLE',
            ('NOT_SIMPLE', ),
            display_transform=lambda const: const.lower(),
            value_transform=lambda const: const[::-1]
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'simple')
        self.assertEqual(MY_CHOICES.SIMPLE.value, 'ELPMIS')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'not_simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.value, 'ELPMIS_TON')

    def test_override_transform_functions(self):

        class MyAutoChoices(AutoChoices):
            display_transform = staticmethod(lambda const: const.lower())
            value_transform = staticmethod(lambda const: const.lower()[::-1])

        MY_CHOICES = MyAutoChoices(
            'SIMPLE',
            ('NOT_SIMPLE', ),
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'simple')
        self.assertEqual(MY_CHOICES.SIMPLE.value, 'elpmis')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'not_simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.value, 'elpmis_ton')

        MY_CHOICES = MyAutoChoices(
            'SIMPLE',
            ('NOT_SIMPLE', ),
            display_transform=lambda const: const.title(),
            value_transform=lambda const: const.title()[::-1]
        )

        self.assertEqual(MY_CHOICES.SIMPLE.display, 'Simple')
        self.assertEqual(MY_CHOICES.SIMPLE.value, 'elpmiS')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.display, 'Not_Simple')
        self.assertEqual(MY_CHOICES.NOT_SIMPLE.value, 'elpmiS_toN')

    def test_adding_subset(self):

        MY_CHOICES = AutoChoices('A', 'B', 'C')
        MY_CHOICES.add_subset('AB', ['A', 'B'])

        self.assertEqual(MY_CHOICES.AB.constants, {
            'A': MY_CHOICES.A.choice_entry,
            'B': MY_CHOICES.B.choice_entry,
        })

    def test_passing_not_only_constant(self):
        MY_CHOICES = AutoChoices(
            ChoiceEntry(('A', 'aa', 'aaa', {'foo': 'bara'})),
            'B',
            ('C', ),
            ('D', {'foo': 'bard'}),
            ('E', 'ee'),
            ('F', 'ff', {'foo': 'barf'}),
            ('G', 'gg', 'ggg'),
            ('H', 'hh', 'hhh', {'foo': 'barh'}),
            ('I', None, 'iii'),
            ('J', None, 'jjj', {'foo': 'barj'}),
        )

        self.assertEqual(MY_CHOICES.A.value, 'aa')
        self.assertEqual(MY_CHOICES.A.display, 'aaa')
        self.assertEqual(MY_CHOICES.A.foo, 'bara')
        self.assertEqual(MY_CHOICES.B.value, 'b')
        self.assertEqual(MY_CHOICES.B.display, 'B')
        self.assertEqual(MY_CHOICES.C.value, 'c')
        self.assertEqual(MY_CHOICES.C.display, 'C')
        self.assertEqual(MY_CHOICES.D.value, 'd')
        self.assertEqual(MY_CHOICES.D.display, 'D')
        self.assertEqual(MY_CHOICES.D.foo, 'bard')
        self.assertEqual(MY_CHOICES.E.value, 'ee')
        self.assertEqual(MY_CHOICES.E.display, 'E')
        self.assertEqual(MY_CHOICES.F.value, 'ff')
        self.assertEqual(MY_CHOICES.F.display, 'F')
        self.assertEqual(MY_CHOICES.F.foo, 'barf')
        self.assertEqual(MY_CHOICES.G.value, 'gg')
        self.assertEqual(MY_CHOICES.G.display, 'ggg')
        self.assertEqual(MY_CHOICES.H.value, 'hh')
        self.assertEqual(MY_CHOICES.H.display, 'hhh')
        self.assertEqual(MY_CHOICES.H.foo, 'barh')
        self.assertEqual(MY_CHOICES.I.value, 'i')
        self.assertEqual(MY_CHOICES.I.display, 'iii')
        self.assertEqual(MY_CHOICES.J.value, 'j')
        self.assertEqual(MY_CHOICES.J.display, 'jjj')
        self.assertEqual(MY_CHOICES.J.foo, 'barj')

        MY_CHOICES.add_subset('ALL', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'])
        self.assertEqual(MY_CHOICES.ALL.constants, MY_CHOICES.constants)


if __name__ == "__main__":
    unittest.main()
