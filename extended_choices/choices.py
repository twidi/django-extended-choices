"""Provides a ``Choices`` class to help using "choices" in Django fields.

The aim is to replace:

.. code-block:: python

    STATE_ONLINE  = 1
    STATE_DRAFT   = 2
    STATE_OFFLINE = 3

    STATE_CHOICES = (
        (STATE_ONLINE,  'Online'),
        (STATE_DRAFT,   'Draft'),
        (STATE_OFFLINE, 'Offline'),
    )

    STATE_DICT = dict(STATE_CHOICES)

    class Content(models.Model):
        title      = models.CharField(max_length=255)
        content    = models.TextField()
        state      = models.PositiveSmallIntegerField(choices=STATE_CHOICES, default=STATE_DRAFT)

        def __unicode__(self):
            return 'Content "%s" (state=%s)' % (self.title, STATE_DICT[self.state])

    print(Content.objects.filter(state=STATE_ONLINE))

By this:

.. code-block:: python

    from extended_choices import Choices

    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
    )

    class Content(models.Model):
        title      = models.CharField(max_length=255)
        content    = models.TextField()
        state      = models.PositiveSmallIntegerField(choices=STATES, default=STATES.DRAFT)

        def __unicode__(self):
            return 'Content "%s" (state=%s)' % (self.title, STATES.for_value(self.state).display)

    print(Content.objects.filter(state=STATES.ONLINE))


Notes
-----

The documentation format in this file is numpydoc_.

.. _numpydoc: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

"""

from __future__ import unicode_literals
import six

from collections import OrderedDict
try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

from .helpers import ChoiceEntry

__all__ = [
    'Choices',
    'OrderedChoices',
    'AutoDisplayChoices',
    'AutoChoices',
]

_NO_SUBSET_NAME_ = '__NO_SUBSET_NAME__'


class Choices(list):
    """Helper class for choices fields in Django

    A choice entry has three representation: constant name, value and
    display name). So ``Choices`` takes list of such tuples.

    It's easy to get the constant, value or display name given one of these value. See in
    example.

    Parameters
    ----------
    *choices : list of tuples
        It's the list of tuples to add to the ``Choices`` instance, each tuple having three
        entries: the constant name, the value, the display name.

        A dict could be added as a 4th entry in the tuple to allow setting arbitrary
        arguments to the final ``ChoiceEntry`` created for this choice tuple.

    name : string, optional
        If set, a subset will be created containing all the constants. It could be used if you
        construct your ``Choices`` instance with many calls to ``add_choices``.
    dict_class : type, optional
        ``dict`` by default, it's the dict class to use to create dictionaries (``constants``,
        ``values`` and ``displays``. Could be set for example to ``OrderedDict`` (you can use
        ``OrderedChoices`` that is a simple subclass using ``OrderedDict``.

    Example
    -------

    Start by declaring your ``Choices``:

    >>> ALIGNMENTS = Choices(
    ...     ('BAD', 10, 'bad'),
    ...     ('NEUTRAL', 20, 'neutral'),
    ...     ('CHAOTIC_GOOD', 30, 'chaotic good'),
    ...     ('GOOD', 40, 'good'),
    ...     dict_class=OrderedDict
    ... )

    Then you can use it in a django field, Notice its usage in ``choices`` and ``default``:

    >>> from django.conf import settings
    >>> try:
    ...     settings.configure(DATABASE_ENGINE='sqlite3')
    ... except: pass
    >>> from django.db.models import IntegerField
    >>> field = IntegerField(choices=ALIGNMENTS,  # use ``ALIGNMENTS`` or ``ALIGNMENTS.choices``.
    ...                      default=ALIGNMENTS.NEUTRAL)

    The ``Choices`` returns a list as expected by django:

    >>> ALIGNMENTS == ((10, 'bad'), (20, 'neutral'), (30, 'chaotic good'), (40, 'good'))
    True

    But represents it with the constants:

    >>> repr(ALIGNMENTS)
    "[('BAD', 10, 'bad'), ('NEUTRAL', 20, 'neutral'), ('CHAOTIC_GOOD', 30, 'chaotic good'), ('GOOD', 40, 'good')]"

    Use ``choices`` which is a simple list to represent it as such:

    >>> ALIGNMENTS.choices
    ((10, 'bad'), (20, 'neutral'), (30, 'chaotic good'), (40, 'good'))


    And you can access value by their constant, or as you want:

    >>> ALIGNMENTS.BAD
    10
    >>> ALIGNMENTS.BAD.display
    'bad'
    >>> 40 in ALIGNMENTS
    True
    >>> ALIGNMENTS.has_constant('BAD')
    True
    >>> ALIGNMENTS.has_value(20)
    True
    >>> ALIGNMENTS.has_display('good')
    True
    >>> ALIGNMENTS.for_value(10)
    ('BAD', 10, 'bad')
    >>> ALIGNMENTS.for_value(10).constant
    'BAD'
    >>> ALIGNMENTS.for_display('good').value
    40
    >>> ALIGNMENTS.for_constant('NEUTRAL').display
    'neutral'
    >>> ALIGNMENTS.constants
    OrderedDict([('BAD', ('BAD', 10, 'bad')), ('NEUTRAL', ('NEUTRAL', 20, 'neutral')), ('CHAOTIC_GOOD', ('CHAOTIC_GOOD', 30, 'chaotic good')), ('GOOD', ('GOOD', 40, 'good'))])
    >>> ALIGNMENTS.values
    OrderedDict([(10, ('BAD', 10, 'bad')), (20, ('NEUTRAL', 20, 'neutral')), (30, ('CHAOTIC_GOOD', 30, 'chaotic good')), (40, ('GOOD', 40, 'good'))])
    >>> ALIGNMENTS.displays
    OrderedDict([('bad', ('BAD', 10, 'bad')), ('neutral', ('NEUTRAL', 20, 'neutral')), ('chaotic good', ('CHAOTIC_GOOD', 30, 'chaotic good')), ('good', ('GOOD', 40, 'good'))])

    You can create subsets of choices:

    >>> ALIGNMENTS.add_subset('WESTERN',('BAD', 'GOOD'))
    >>> ALIGNMENTS.WESTERN.choices
    ((10, 'bad'), (40, 'good'))
    >>> ALIGNMENTS.BAD in ALIGNMENTS.WESTERN
    True
    >>> ALIGNMENTS.NEUTRAL in ALIGNMENTS.WESTERN
    False

    To use it in another field (only the values in the subset will be available), or for checks:

    >>> def is_western(value):
    ...     return value in ALIGNMENTS.WESTERN
    >>> is_western(40)
    True

    """

    # Allow to easily change the ``ChoiceEntry`` class to use in subclasses.
    ChoiceEntryClass = ChoiceEntry

    def __init__(self, *choices, **kwargs):

        # Init the list as empty. Entries will be formatted for django and added in
        # ``add_choices``.
        super(Choices, self).__init__()

        # Class to use for dicts.
        self.dict_class = kwargs.get('dict_class', dict)

        # List of ``ChoiceEntry``, one for each choice in this instance.
        self.entries = []

        # List of the created subsets
        self.subsets = []

        # Dicts to access ``ChoiceEntry`` instances by constant, value or display value.
        self.constants = self.dict_class()
        self.values = self.dict_class()
        self.displays = self.dict_class()

        # For now this instance is mutable: we need to add the given choices.
        self._mutable = True
        self.add_choices(*choices, name=kwargs.get('name', None))

        # Now we can set ``_mutable`` to its correct value.
        self._mutable = kwargs.get('mutable', True)

    @property
    def choices(self):
        """Property that returns a tuple formatted as expected by Django.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.choices
        ((1, 'foo'), (2, 'bar'))

        """
        return tuple(self)

    def _convert_choices(self, choices):
        """Validate each choices

        Parameters
        ----------
        choices : list of tuples
            The list of choices to be added

        Returns
        -------
        list
            The list of the added constants

        """

        # Check that each new constant is unique.
        constants = [c[0] for c in choices]
        constants_doubles = [c for c in constants if constants.count(c) > 1]
        if constants_doubles:
            raise ValueError("You cannot declare two constants with the same constant name. "
                             "Problematic constants: %s " % list(set(constants_doubles)))

        # Check that none of the new constants already exists.
        bad_constants = set(constants).intersection(self.constants)
        if bad_constants:
            raise ValueError("You cannot add existing constants. "
                             "Existing constants: %s." % list(bad_constants))

        # Check that none of the constant is an existing attributes
        bad_constants = [c for c in constants if hasattr(self, c)]
        if bad_constants:
            raise ValueError("You cannot add constants that already exists as attributes. "
                             "Existing attributes: %s." % list(bad_constants))

        # Check that each new value is unique.
        values = [c[1] for c in choices]
        values_doubles = [c for c in values if values.count(c) > 1]
        if values_doubles:
            raise ValueError("You cannot declare two choices with the same name."
                             "Problematic values: %s " % list(set(values_doubles)))

        # Check that none of the new values already exists.
        try:
            bad_values = set(values).intersection(self.values)
        except TypeError:
            raise ValueError("One value cannot be used in: %s" % list(values))
        else:
            if bad_values:
                raise ValueError("You cannot add existing values. "
                                 "Existing values: %s." % list(bad_values))

        # We can now add each choice.
        for choice_tuple in choices:

            # Convert the choice tuple in a ``ChoiceEntry`` instance if it's not already done.
            # It allows to share choice entries between a ``Choices`` instance and its subsets.
            choice_entry = choice_tuple
            if not isinstance(choice_entry, self.ChoiceEntryClass):
                choice_entry = self.ChoiceEntryClass(choice_entry)

            # Append to the main list the choice as expected by django: (value, display name).
            self.append(choice_entry.choice)
            # And the ``ChoiceEntry`` instance to our own internal list.
            self.entries.append(choice_entry)

            # Make the value accessible via an attribute (the constant being its name).
            setattr(self, choice_entry.constant, choice_entry.value)

            # Fill dicts to access the ``ChoiceEntry`` instance by its constant, value or display..
            self.constants[choice_entry.constant] = choice_entry
            self.values[choice_entry.value] = choice_entry
            self.displays[choice_entry.display] = choice_entry

        return constants

    def add_choices(self, *choices, **kwargs):
        """Add some choices to the current ``Choices`` instance.

        The given choices will be added to the existing choices.
        If a ``name`` attribute is passed, a new subset will be created with all the given
        choices.

        Note that it's not possible to add new choices to a subset.

        Parameters
        ----------
        *choices : list of tuples
            It's the list of tuples to add to the ``Choices`` instance, each tuple having three
            entries: the constant name, the value, the display name.

            A dict could be added as a 4th entry in the tuple to allow setting arbitrary
            arguments to the final ``ChoiceEntry`` created for this choice tuple.

            If the first entry of ``*choices`` is a string, then it will be used as a name for a
            new subset that will contain all the given choices.
        **kwargs : dict
            name : string
                Instead of using the first entry of the ``*choices`` to pass a name of a subset to
                create, you can pass it via the ``name`` named argument.

        Example
        -------

        >>> MY_CHOICES = Choices()
        >>> MY_CHOICES.add_choices(('ZERO', 0, 'zero'))
        >>> MY_CHOICES
        [('ZERO', 0, 'zero')]
        >>> MY_CHOICES.add_choices('SMALL', ('ONE', 1, 'one'), ('TWO', 2, 'two'))
        >>> MY_CHOICES
        [('ZERO', 0, 'zero'), ('ONE', 1, 'one'), ('TWO', 2, 'two')]
        >>> MY_CHOICES.SMALL
        [('ONE', 1, 'one'), ('TWO', 2, 'two')]
        >>> MY_CHOICES.add_choices(('THREE', 3, 'three'), ('FOUR', 4, 'four'), name='BIG')
        >>> MY_CHOICES
        [('ZERO', 0, 'zero'), ('ONE', 1, 'one'), ('TWO', 2, 'two'), ('THREE', 3, 'three'), ('FOUR', 4, 'four')]
        >>> MY_CHOICES.BIG
        [('THREE', 3, 'three'), ('FOUR', 4, 'four')]

        Raises
        ------
        RuntimeError
            When the ``Choices`` instance is marked as not mutable, which is the case for subsets.

        ValueError

            * if the subset name is defined as first argument and as named argument.
            * if some constants have the same name or the same value.
            * if at least one constant or value already exists in the instance.

        """

        # It the ``_mutable`` flag is falsy, which is the case for subsets, we refuse to add
        # new choices.
        if not self._mutable:
            raise RuntimeError("This ``Choices`` instance cannot be updated.")

        # Check for an optional subset name as the first argument (so the first entry of *choices).
        subset_name = None
        if choices and isinstance(choices[0], six.string_types) and choices[0] != _NO_SUBSET_NAME_:
            subset_name = choices[0]
            choices = choices[1:]

        # Check for an optional subset name in the named arguments.
        if kwargs.get('name', None):
            if subset_name:
                raise ValueError("The name of the subset cannot be defined as the first "
                                 "argument and also as a named argument")
            subset_name = kwargs['name']

        constants = self._convert_choices(choices)

        # If we have a subset name, create a new subset with all the given constants.
        if subset_name:
            self.add_subset(subset_name, constants)

    def extract_subset(self, *constants):
        """Create a subset of entries

        This subset is a new ``Choices`` instance, with only the wanted constants from the
        main ``Choices`` (each "choice entry" in the subset is shared from the main ``Choices``)

        Parameters
        ----------
        *constants: list
            The constants names of this ``Choices`` object to make available in the subset.

        Returns
        -------
        Choices
            The newly created subset, which is a ``Choices`` object


        Example
        -------

        >>> STATES = Choices(
        ...     ('ONLINE',  1, 'Online'),
        ...     ('DRAFT',   2, 'Draft'),
        ...     ('OFFLINE', 3, 'Offline'),
        ... )
        >>> STATES
        [('ONLINE', 1, 'Online'), ('DRAFT', 2, 'Draft'), ('OFFLINE', 3, 'Offline')]
        >>> subset = STATES.extract_subset('DRAFT', 'OFFLINE')
        >>> subset
        [('DRAFT', 2, 'Draft'), ('OFFLINE', 3, 'Offline')]
        >>> subset.DRAFT
        2
        >>> subset.for_constant('DRAFT') is STATES.for_constant('DRAFT')
        True
        >>> subset.ONLINE
        Traceback (most recent call last):
        ...
        AttributeError: 'Choices' object has no attribute 'ONLINE'


        Raises
        ------
        ValueError
            If a constant is not defined as a constant in the ``Choices`` instance.

        """

        # Ensure that all passed constants exists as such in the list of available constants.
        bad_constants = set(constants).difference(self.constants)
        if bad_constants:
            raise ValueError("All constants in subsets should be in parent choice. "
                             "Missing constants: %s." % list(bad_constants))

        # Keep only entries we asked for.
        choice_entries = [self.constants[c] for c in constants]

        # Create a new ``Choices`` instance with the limited set of entries, and pass the other
        # configuration attributes to share the same behavior as the current ``Choices``.
        # Also we set ``mutable`` to False to disable the possibility to add new choices to the
        # subset.
        subset = self.__class__(
            *choice_entries,
            **{
                'dict_class': self.dict_class,
                'mutable': False,
            }
        )

        return subset

    def add_subset(self, name, constants):
        """Add a subset of entries under a defined name.

        This allow to defined a "sub choice" if a django field need to not have the whole
        choice available.

        The sub-choice is a new ``Choices`` instance, with only the wanted the constant from the
        main ``Choices`` (each "choice entry" in the subset is shared from the main ``Choices``)
        The sub-choice is accessible from the main ``Choices`` by an attribute having the given
        name.

        Parameters
        ----------
        name : string
            Name of the attribute that will old the new ``Choices`` instance.
        constants: list or tuple
            List of the constants name of this ``Choices`` object to make available in the subset.


        Returns
        -------
        Choices
            The newly created subset, which is a ``Choices`` object


        Example
        -------

        >>> STATES = Choices(
        ...     ('ONLINE',  1, 'Online'),
        ...     ('DRAFT',   2, 'Draft'),
        ...     ('OFFLINE', 3, 'Offline'),
        ... )
        >>> STATES
        [('ONLINE', 1, 'Online'), ('DRAFT', 2, 'Draft'), ('OFFLINE', 3, 'Offline')]
        >>> STATES.add_subset('NOT_ONLINE', ('DRAFT', 'OFFLINE',))
        >>> STATES.NOT_ONLINE
        [('DRAFT', 2, 'Draft'), ('OFFLINE', 3, 'Offline')]
        >>> STATES.NOT_ONLINE.DRAFT
        2
        >>> STATES.NOT_ONLINE.for_constant('DRAFT') is STATES.for_constant('DRAFT')
        True
        >>> STATES.NOT_ONLINE.ONLINE
        Traceback (most recent call last):
        ...
        AttributeError: 'Choices' object has no attribute 'ONLINE'


        Raises
        ------
        ValueError

            * If ``name`` is already an attribute of the ``Choices`` instance.
            * If a constant is not defined as a constant in the ``Choices`` instance.

        """

        # Ensure that the name is not already used as an attribute.
        if hasattr(self, name):
            raise ValueError("Cannot use '%s' as a subset name. "
                             "It's already an attribute." % name)

        subset = self.extract_subset(*constants)

        # Make the subset accessible via an attribute.
        setattr(self, name, subset)
        self.subsets.append(name)

    def for_constant(self, constant):
        """Returns the ``ChoiceEntry`` for the given constant.

        Parameters
        ----------
        constant: string
            Name of the constant for which we want the choice entry.

        Returns
        -------
        ChoiceEntry
            The instance of ``ChoiceEntry`` for the given constant.

        Raises
        ------
        KeyError
            If the constant is not an existing one.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.for_constant('FOO')
        ('FOO', 1, 'foo')
        >>> MY_CHOICES.for_constant('FOO').value
        1
        >>> MY_CHOICES.for_constant('QUX')
        Traceback (most recent call last):
        ...
        KeyError: 'QUX'

        """

        return self.constants[constant]

    def for_value(self, value):
        """Returns the ``ChoiceEntry`` for the given value.

        Parameters
        ----------
        value: ?
            Value for which we want the choice entry.

        Returns
        -------
        ChoiceEntry
            The instance of ``ChoiceEntry`` for the given value.

        Raises
        ------
        KeyError
            If the value is not an existing one.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.for_value(1)
        ('FOO', 1, 'foo')
        >>> MY_CHOICES.for_value(1).display
        'foo'
        >>> MY_CHOICES.for_value(3)
        Traceback (most recent call last):
        ...
        KeyError: 3

        """

        return self.values[value]

    def for_display(self, display):
        """Returns the ``ChoiceEntry`` for the given display name.

        Parameters
        ----------
        display: string
            Display name for which we want the choice entry.

        Returns
        -------
        ChoiceEntry
            The instance of ``ChoiceEntry`` for the given display name.

        Raises
        ------
        KeyError
            If the display name is not an existing one.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.for_display('foo')
        ('FOO', 1, 'foo')
        >>> MY_CHOICES.for_display('foo').constant
        'FOO'
        >>> MY_CHOICES.for_display('qux')
        Traceback (most recent call last):
        ...
        KeyError: 'qux'

        """

        return self.displays[display]

    def has_constant(self, constant):
        """Check if the current ``Choices`` object has the given constant.

        Parameters
        ----------
        constant: string
            Name of the constant we want to check..

        Returns
        -------
        boolean
            ``True`` if the constant is present, ``False`` otherwise.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.has_constant('FOO')
        True
        >>> MY_CHOICES.has_constant('QUX')
        False

        """

        return constant in self.constants

    def has_value(self, value):
        """Check if the current ``Choices`` object has the given value.

        Parameters
        ----------
        value: ?
            Value we want to check.

        Returns
        -------
        boolean
            ``True`` if the value is present, ``False`` otherwise.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.has_value(1)
        True
        >>> MY_CHOICES.has_value(3)
        False

        """

        return value in self.values

    def has_display(self, display):
        """Check if the current ``Choices`` object has the given display name.

        Parameters
        ----------
        display: string
            Display name we want to check..

        Returns
        -------
        boolean
            ``True`` if the display name is present, ``False`` otherwise.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES.has_display('foo')
        True
        >>> MY_CHOICES.has_display('qux')
        False

        """

        return display in self.displays

    def __contains__(self, item):
        """Check if the current ``Choices`` object has the given value.

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> 1 in MY_CHOICES
        True
        >>> 3 in MY_CHOICES
        False

        """

        return self.has_value(item)

    def __getitem__(self, key):
        """Return the attribute having the given name for the current instance

        It allows for example to retrieve constant by keys instead of by attributes (as constants
        are set as attributes to easily get the matching value.)

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES['FOO']
        1
        >>> MY_CHOICES['constants'] is MY_CHOICES.constants
        True

        """

        # If the key is an int, call ``super`` to access the list[key] item
        if isinstance(key, int):
            return super(Choices, self).__getitem__(key)

        if not hasattr(self, key):
            raise KeyError("Attribute '%s' not found." % key)

        return getattr(self, key)

    def __repr__(self):
        """String representation of this ``Choices`` instance.

        Notes
        -----
        It will represent the data passed and store in ``self.entries``, not the data really
        stored in the base list object, which is in the format expected by django, ie a list of
        tuples with only value and display name.
        Here, we display everything.

        Example
        -------

        >>> Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        [('FOO', 1, 'foo'), ('BAR', 2, 'bar')]

        """

        return '%s' % self.entries

    def __eq__(self, other):
        """Override to allow comparison with a tuple of choices, not only a list.

        It also allow to compare with default django choices, ie (value, display name), or
        with the format of ``Choices``, ie (constant name, value, display_name).

        Example
        -------

        >>> MY_CHOICES = Choices(('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        >>> MY_CHOICES == [('FOO', 1, 'foo'), ('BAR', 2, 'bar')]
        True
        >>> MY_CHOICES == (('FOO', 1, 'foo'), ('BAR', 2, 'bar'))
        True
        >>> MY_CHOICES == [(1, 'foo'), (2, 'bar')]
        True
        >>> MY_CHOICES == ((1, 'foo'), (2, 'bar'))
        True

        """

        # Convert to list if it's a tuple.
        if isinstance(other, tuple):
            other = list(other)

        # Compare to the list of entries if the first element seems to have a constant
        # name as first entry.
        if other and len(other[0]) == 3:
            return self.entries == other

        return super(Choices, self).__eq__(other)

    # TODO: implement __iadd__ and __add__

    def __reduce__(self):
        """Reducer to make the auto-created classes picklable.

        Returns
        -------
        tuple
            A tuple as expected by pickle, to recreate the object when calling ``pickle.loads``:
            1. a callable to recreate the object
            2. a tuple with all positioned arguments expected by this callable

        """

        return (
            # Function to create a ``Choices`` instance
            create_choice,
            (
                # The ``Choices`` class, or a subclass, used to create the current instance
                self.__class__,
                # The list of choices
                [
                    (
                        entry.constant.original_value,
                        entry.value.original_value,
                        entry.display.original_value,
                        entry.attributes,
                    )
                    for entry in self.entries
                ],
                # The list of subsets
                [
                    (
                        # The name
                        subset_name,
                        # The list of constants to use in this subset
                        [
                            c.original_value
                            for c in getattr(self, subset_name).constants.keys()
                        ]
                    )
                    for subset_name in self.subsets
                ],
                # Extra kwargs to pass to ``__ini__``
                {
                    'dict_class': self.dict_class,
                    'mutable': self._mutable,
                }
            )
        )


class OrderedChoices(Choices):
    """Simple subclass of ``Choices`` using ``OrderedDict`` as ``dict_class``

    Example
    -------

    Start by declaring your ``Choices``:

    >>> ALIGNMENTS = OrderedChoices(
    ...     ('BAD', 10, 'bad'),
    ...     ('NEUTRAL', 20, 'neutral'),
    ...     ('CHAOTIC_GOOD', 30, 'chaotic good'),
    ...     ('GOOD', 40, 'good'),
    ... )

    >>> ALIGNMENTS.dict_class
    <class 'collections.OrderedDict'>

    >>> ALIGNMENTS.constants
    OrderedDict([('BAD', ('BAD', 10, 'bad')), ('NEUTRAL', ('NEUTRAL', 20, 'neutral')), ('CHAOTIC_GOOD', ('CHAOTIC_GOOD', 30, 'chaotic good')), ('GOOD', ('GOOD', 40, 'good'))])
    >>> ALIGNMENTS.values
    OrderedDict([(10, ('BAD', 10, 'bad')), (20, ('NEUTRAL', 20, 'neutral')), (30, ('CHAOTIC_GOOD', 30, 'chaotic good')), (40, ('GOOD', 40, 'good'))])
    >>> ALIGNMENTS.displays
    OrderedDict([('bad', ('BAD', 10, 'bad')), ('neutral', ('NEUTRAL', 20, 'neutral')), ('chaotic good', ('CHAOTIC_GOOD', 30, 'chaotic good')), ('good', ('GOOD', 40, 'good'))])

    """

    def __init__(self, *choices, **kwargs):

        # Class to use for dicts
        if 'dict_class' not in kwargs:
            kwargs['dict_class'] = OrderedDict

        super(OrderedChoices, self).__init__(*choices, **kwargs)


class AutoDisplayChoices(OrderedChoices):
    """Subclass of ``OrderedChoices`` that will compose the display value based on the constant.

    To compose the display value, it will call a  ``display_transform`` function, that is defined
    as a class attribute but can be overridden by     passing it to the constructor.

    Example
    -------

    >>> ALIGNMENTS = AutoDisplayChoices(
    ...     ('BAD', 10),
    ...     ('NEUTRAL', 20),
    ...     ('CHAOTIC_GOOD', 30, 'THE CHAOS'),
    ...     ('GOOD', 40, {'additional': 'attributes'}),
    ... )

    >>> ALIGNMENTS.BAD.display
    'Bad'
    >>> ALIGNMENTS.NEUTRAL.choice_entry
    ('NEUTRAL', 20, 'Neutral')
    >>> ALIGNMENTS.CHAOTIC_GOOD.display
    'THE CHAOS'
    >>> ALIGNMENTS.GOOD.choice_entry.additional
    'attributes'

    """

    display_transform = staticmethod(lambda const: const.lower().replace('_', ' ').capitalize())

    def __init__(self, *choices, **kwargs):
        self.display_transform = kwargs.pop('display_transform', None) or self.display_transform
        super(AutoDisplayChoices, self).__init__(*choices, **kwargs)

    def _convert_choices(self, choices):
        """Auto create display values then call super method"""

        final_choices = []
        for choice in choices:

            if isinstance(choice, ChoiceEntry):
                final_choices.append(choice)
                continue

            original_choice = choice
            choice = list(choice)
            length = len(choice)

            assert 2 <= length <= 4, 'Invalid number of entries in %s' % (original_choice,)

            final_choice = []

            # do we have attributes?
            if length > 2 and isinstance(choice[-1], Mapping):
                final_choice.append(choice.pop())
            elif length == 4:
                attributes = choice.pop()
                assert attributes is None or isinstance(attributes, Mapping), 'Last argument must be a dict-like object in %s' % (original_choice,)
                if attributes:
                    final_choice.append(attributes)

            # the constant
            final_choice.insert(0, choice.pop(0))

            # the db value
            final_choice.insert(1, choice.pop(0))

            if len(choice):
                # we were given a display value
                final_choice.insert(2, choice.pop(0))
            else:
                # no display value, we compute it from the constant
                final_choice.insert(2, self.display_transform(final_choice[0]))

            final_choices.append(final_choice)

        return super(AutoDisplayChoices, self)._convert_choices(final_choices)


class AutoChoices(AutoDisplayChoices):
    """Subclass of ``AutoDisplayChoices`` that will also compose the value to be saved based on the constant.

    To compose the display value, it will call a  ``display_transform`` function, that is defined
    as a class attribute but can be overridden by     passing it to the constructor.

    In this class, the ``*choices`` argument can simply be strings, or tuples with one element (or two
    to add additional attributes)

    Example
    -------

    >>> ALIGNMENTS = AutoChoices(
    ...     'BAD',
    ...     ('NEUTRAL', ),
    ...     ('CHAOTIC_GOOD', 'chaos', 'THE CHAOS'),
    ...     ('GOOD', None, 'Yeah', {'additional': 'attributes'}),
    ... )

    >>> ALIGNMENTS.BAD.value
    'bad'
    >>> ALIGNMENTS.BAD.display
    'Bad'
    >>> ALIGNMENTS.NEUTRAL.choice_entry
    ('NEUTRAL', 'neutral', 'Neutral')
    >>> ALIGNMENTS.CHAOTIC_GOOD.value
    'chaos'
    >>> ALIGNMENTS.CHAOTIC_GOOD.display
    'THE CHAOS'
    >>> ALIGNMENTS.GOOD.value
    'good'
    >>> ALIGNMENTS.GOOD.display
    'Yeah'
    >>> ALIGNMENTS.GOOD.choice_entry.additional
    'attributes'

    """

    value_transform = staticmethod(lambda const: const.lower())

    def __init__(self, *choices, **kwargs):
        self.value_transform = kwargs.pop('value_transform', None) or self.value_transform
        super(AutoChoices, self).__init__(*choices, **kwargs)

    def add_choices(self, *choices, **kwargs):
        """Disallow super method to thing the first argument is a subset name"""
        return super(AutoChoices, self).add_choices(_NO_SUBSET_NAME_, *choices, **kwargs)

    def _convert_choices(self, choices):
        """Auto create db values then call super method"""

        final_choices = []
        for choice in choices:

            if isinstance(choice, ChoiceEntry):
                final_choices.append(choice)
                continue

            original_choice = choice
            if isinstance(choice, six.string_types):
                if choice == _NO_SUBSET_NAME_:
                    continue
                choice = [choice, ]
            else:
                choice = list(choice)

            length = len(choice)

            assert 1 <= length <= 4, 'Invalid number of entries in %s' % (original_choice,)

            final_choice = []

            # do we have attributes?
            if length > 1 and isinstance(choice[-1], Mapping):
                final_choice.append(choice.pop())
            elif length == 4:
                attributes = choice.pop()
                assert attributes is None or isinstance(attributes, Mapping), 'Last argument must be a dict-like object in %s' % (original_choice,)
                if attributes:
                    final_choice.append(attributes)

            # the constant
            final_choice.insert(0, choice.pop(0))

            if len(choice):
                # we were given a db value
                final_choice.insert(1, choice.pop(0))
                if len(choice):
                    # we were given a display value
                    final_choice.insert(2, choice.pop(0))
            else:
                # set None to compute it later
                final_choice.insert(1, None)

            if final_choice[1] is None:
                # no db value, we compute it from the constant
                final_choice[1] = self.value_transform(final_choice[0])

            final_choices.append(final_choice)

        return super(AutoChoices, self)._convert_choices(final_choices)


def create_choice(klass, choices, subsets, kwargs):
    """Create an instance of a ``Choices`` object.

    Parameters
    ----------
    klass : type
        The class to use to recreate the object.
    choices : list(tuple)
        A list of choices as expected by the ``__init__`` method of ``klass``.
    subsets : list(tuple)
        A tuple with an entry for each subset to create. Each entry is a list with two entries:
        - the name of the subsets
        - a list of the constants to use for this subset
    kwargs : dict
        Extra parameters expected on the ``__init__`` method of ``klass``.

    Returns
    -------
    Choices
        A new instance of ``Choices`` (or other class defined in ``klass``).

    """

    obj = klass(*choices, **kwargs)
    for subset in subsets:
        obj.add_subset(*subset)
    return obj
