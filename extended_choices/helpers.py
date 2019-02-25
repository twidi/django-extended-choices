"""Provides classes used to construct a full ``Choices`` instance.

Notes
-----

The documentation format in this file is numpydoc_.

.. _numpydoc: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

"""

from __future__ import unicode_literals

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

from django.utils.functional import Promise


class ChoiceAttributeMixin(object):
    """Base class to represent an attribute of a ``ChoiceEntry``.

    Used for ``constant``, ``name``, and ``display``.

    It must be used as a mixin with another type, and the final class will be a type with
    added attributes to access the ``ChoiceEntry`` instance and its attributes.

    Attributes
    ----------
    choice_entry : instance of ``ChoiceEntry``
        The ``ChoiceEntry`` instance that hold the current value, used to access its constant,
        value and display name.
    constant : property
        Returns the choice field holding the constant of the attached ``ChoiceEntry``.
    value : property
        Returns the choice field holding the value of the attached ``ChoiceEntry``.
    display : property
        Returns the choice field holding the display name of the attached ``ChoiceEntry``.
    original_value : ?
        The value used to create the current instance.
    creator_type : type
        The class that created a new class. Will be ``ChoiceAttributeMixin`` except if it was
        overridden by the author.

    Example
    -------

    Classes can be created manually:

    >>> class IntChoiceAttribute(ChoiceAttributeMixin, int): pass
    >>> field = IntChoiceAttribute(1, ChoiceEntry(('FOO', 1, 'foo')))
    >>> field
    1
    >>> field.constant, field.value, field.display
    ('FOO', 1, 'foo')
    >>> field.choice_entry
    ('FOO', 1, 'foo')

    Or via the ``get_class_for_value`` class method:

    >>> klass = ChoiceAttributeMixin.get_class_for_value(1.5)
    >>> klass.__name__
    'FloatChoiceAttribute'
    >>> float in klass.mro()
    True

    """

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """Construct the object (the other class used with this mixin).

        Notes
        -----

        Only passes the very first argument to the ``super`` constructor.
        All others are not needed for the other class, only for this mixin.

        """

        if issubclass(cls, Promise):
            # Special case to manage lazy django stuff like ugettext_lazy
            return super(ChoiceAttributeMixin, cls).__new__(cls)

        return super(ChoiceAttributeMixin, cls).__new__(cls, *args[:1])

    def __init__(self, value, choice_entry):
        """Initiate the object to save the value and the choice entry.

        Parameters
        ----------
        value : ?
            Value to pass to the ``super`` constructor (for the other class using this mixin)
        choice_entry: ChoiceEntry
            The ``ChoiceEntry`` instance that hold the current value, used to access its constant,
            value and display name.

        Notes
        -----

        Call the ``super`` constructor with only the first value, as the other class doesn't
        expect the ``choice_entry`` parameter.

        """

        if isinstance(self, Promise):
            # Special case to manage lazy django stuff like ugettext_lazy
            # pylint: disable=protected-access
            super(ChoiceAttributeMixin, self).__init__(value._proxy____args, value._proxy____kw)
        else:
            super(ChoiceAttributeMixin, self).__init__()

        self.original_value = value
        self.choice_entry = choice_entry
        if self.choice_entry.attributes:
            for key, value in self.choice_entry.attributes.items():
                setattr(self, key, value)

    @property
    def constant(self):
        """Property that returns the ``constant`` attribute of the attached ``ChoiceEntry``."""
        return self.choice_entry.constant

    @property
    def value(self):
        """Property that returns the ``value`` attribute of the attached ``ChoiceEntry``."""
        return self.choice_entry.value

    @property
    def display(self):
        """Property that returns the ``display`` attribute of the attached ``ChoiceEntry``."""
        return self.choice_entry.display

    @classmethod
    def get_class_for_value(cls, value):
        """Class method to construct a class based on this mixin and the type of the given value.

        Parameters
        ----------
        value: ?
            The value from which to extract the type to create the new class.

        Notes
        -----
        The  create classes are cached (in ``cls.__classes_by_type``) to avoid recreating already
        created classes.
        """
        type_ = value.__class__

        # Check if the type is already a ``ChoiceAttribute``
        if issubclass(type_, ChoiceAttributeMixin):
            # In this case we can return this type
            return type_

        # Create a new class only if it wasn't already created for this type.
        if type_ not in cls._classes_by_type:
            # Compute the name of the class with the name of the type.
            class_name = str('%sChoiceAttribute' % type_.__name__.capitalize())
            # Create a new class and save it in the cache.
            cls._classes_by_type[type_] = type(class_name, (cls, type_), {
                'creator_type': cls,
            })

        # Return the class from the cache based on the type.
        return cls._classes_by_type[type_]

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
            # Function to create a choice attribute
            create_choice_attribute,
            (
                # The class that created the class of the current value
                self.creator_type,
                # The original type of the current value
                self.original_value,
                # The tied `choice_entry`
                self.choice_entry
            )
        )

    def __bool__(self):
        """Use the original value to know if the value is truthy of falsy"""
        return bool(self.original_value)

    _classes_by_type = {}


def create_choice_attribute(creator_type, value, choice_entry):
    """Create an instance of a subclass of ChoiceAttributeMixin for the given value.

    Parameters
    ----------
    creator_type : type
        ``ChoiceAttributeMixin`` or a subclass, from which we'll call the ``get_class_for_value``
        class-method.
    value : ?
        The value for which we want to create an instance of a new subclass of ``creator_type``.
    choice_entry: ChoiceEntry
        The ``ChoiceEntry`` instance that hold the current value, used to access its constant,
        value and display name.

    Returns
    -------
    ChoiceAttributeMixin
        An instance of a subclass of ``creator_type`` for the given value

    """

    klass = creator_type.get_class_for_value(value)
    return klass(value, choice_entry)


class ChoiceEntry(tuple):
    """Represents a choice in a ``Choices`` object, with easy access to its attribute.

    Expecting a tuple with three entries. (constant, value, display name), it will add three
    attributes to access then: ``constant``, ``value`` and ``display``.

    By passing a dict after these three first entries, in the tuple, it's also possible to
    add some other attributes to the ``ChoiceEntry` instance``.

    Parameters
    ----------
    tuple_ : tuple
        A tuple with three entries, the name of the constant, the value, and the display name.
        A dict could be added as a fourth entry to add additional attributes.


    Example
    -------

    >>> entry = ChoiceEntry(('FOO', 1, 'foo'))
    >>> entry
    ('FOO', 1, 'foo')
    >>> (entry.constant, entry.value, entry.display)
    ('FOO', 1, 'foo')
    >>> entry.choice
    (1, 'foo')

    You can also pass attributes to add to the instance to create:

    >>> entry = ChoiceEntry(('FOO', 1, 'foo', {'bar': 1, 'baz': 2}))
    >>> entry
    ('FOO', 1, 'foo')
    >>> entry.bar
    1
    >>> entry.baz
    2

    Raises
    ------
    AssertionError
        If the number of entries in the tuple is not expected. Must be 3 or 4.

    """

    # Allow to easily change the mixin to use in subclasses.
    ChoiceAttributeMixin = ChoiceAttributeMixin

    def __new__(cls, tuple_):
        """Construct the tuple with 3 entries, and save optional attributes from the 4th one."""

        # Ensure we have exactly 3 entries in the tuple and an optional dict.
        assert 3 <= len(tuple_) <= 4, 'Invalid number of entries in %s' % (tuple_,)

        attributes = None
        if len(tuple_) == 4:
            attributes = tuple_[3]
            assert attributes is None or isinstance(attributes, Mapping), 'Last argument must be a dict-like object in %s' % (tuple_,)
            if attributes:
                for invalid_key in {'constant', 'value', 'display'}:
                    assert invalid_key not in attributes, 'Additional attributes cannot contain one named "%s" in %s' % (invalid_key, tuple_,)

        # Call the ``tuple`` constructor with only the real tuple entries.
        obj = super(ChoiceEntry, cls).__new__(cls, tuple_[:3])

        # Save all special attributes.
        # pylint: disable=protected-access
        obj.attributes = attributes
        obj.constant = obj._get_choice_attribute(tuple_[0])
        obj.value = obj._get_choice_attribute(tuple_[1])
        obj.display = obj._get_choice_attribute(tuple_[2])

        # Add an attribute holding values as expected by django.
        obj.choice = (obj.value, obj.display)

        # Add additional attributes.
        if attributes:
            for key, value in attributes.items():
                setattr(obj, key, value)

        return obj

    def _get_choice_attribute(self, value):
        """Get a choice attribute for the given value.

        Parameters
        ----------
        value: ?
            The value for which we want a choice attribute.

        Returns
        -------
        An instance of a class based on ``ChoiceAttributeMixin`` for the given value.

        Raises
        ------
        ValueError
            If the value is None, as we cannot really subclass NoneType.

        """

        if value is None:
            raise ValueError('Using `None` in a `Choices` object is not supported. You may '
                             'use an empty string.')

        return create_choice_attribute(self.ChoiceAttributeMixin, value, self)

    def __reduce__(self):
        """Reducer to pass attributes when pickling.

        Returns
        -------
        tuple
            A tuple as expected by pickle, to recreate the object when calling ``pickle.loads``:
            1. a callable to recreate the object
            2. a tuple with all positioned arguments expected by this callable

        """

        return (
            # The ``ChoiceEntry`` class, or a subclass, used to create the current instance
            self.__class__,
            # The original values of the tuple, and attributes (we pass a tuple as single argument)
            (
                (
                    self.constant.original_value,
                    self.value.original_value,
                    self.display.original_value,
                    self.attributes
                ),
            )
        )
