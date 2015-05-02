|PyPI Version| |Build Status| |Doc Status|

django-extended-choices
=======================

A little application to improve django choices
----------------------------------------------

``django-extended-choices`` aims to provide a better and more readable
way of using choices_ in django_.

Installation
------------

You can install directly via pip (since version ```0.3``)::

    $ pip install django-extended-choices

Or from the Github_ repository (``master`` branch by default)::

    $ git clone git://github.com/twidi/django-extended-choices.git
    $ cd django-extended-choices
    $ sudo python setup.py install

Usage
-----

The aim is to replace this:

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
            return u'Content "%s" (state=%s)' % (self.title, STATE_DICT[self.state])

    print(Content.objects.filter(state=STATE_ONLINE))

by this:

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
            return u'Content "%s" (state=%s)' % (self.title, STATES.for_value(self.state).display)

    print(Content.objects.filter(state=STATES.ONLINE))


As you can see there is only one declaration for all states with, for each state, in order:

* the pseudo-constant name which can be used (``STATES.ONLINE`` replaces the previous ``STATE_ONLINE``)
* the value to use as key in database - which could equally be a string
* the name to be displayed - and you can wrap the text in ``ugettext_lazy()`` if you need i18n

And then, you can use:

* ``STATES``, or ``STATES.choices``, to use with ``choices=`` in fields declarations
* ``STATES.for_constant(constant)``, to get the choice entry from the constant name
* ``STATES.for_value(constant)``, to get the choice entry from the key used in database
* ``STATES.for_display(constant)``, to get the choice entry from the displayable value (can be useful in some case)

Each choice entry obtained by ``for_constant``, ``for_value`` and ``for_display`` return a tuple as
given to the ``Choices`` constructor, but with additional attributes:

.. code-block:: python

    >>> entry = STATES.for_constant('ONLINE')
    >>> entry == ('ONLINE', 1, 'Online')
    True
    >>> entry.constant
    'ONLINE'
    >>> entry.value
    1
    >>> entry.display
    'Online'

These attributes are chainable (with a weird example to see chainability):

.. code-block:: python

    >>> entry.constant.value
    1
    >>> entry.constant.value.value.display.constant.display
    'Online'

Note that constants can be accessed via a dict key (``STATES['ONLINE']`` for example) if
 you want to fight your IDE that may warn you about undefined attributes.


You can check whether a value is in a ``Choices`` object directly:

.. code-block:: python

    >>> 1 in STATES
    True
    >>> 42 in STATES
    False


You can even iterate on a ``Choices`` objects to get choices as seen by Django:

.. code-block:: python

    >>> for choice in STATES:
    ...     print(choice)
    (1, 'Online')
    (2, 'Draf')
    (3, 'Offline')

To get all choice entries as given to the ``Choices`` object, you can use the ``entries``
attribute:

.. code-block:: python

    >>> for choice_entry in STATES.entries:
    ...     print(choice_entry)
    ('ONLINE',  1, 'Online'),
    ('DRAFT',   2, 'Draft'),
    ('OFFLINE', 3, 'Offline'),

Or the following dicts, using constants, value or display name as keys, and the matching
choice entry as values:

* ``STATES.constants``
* ``STATES.values``
* ``STATES.displays``


.. code-block:: python

    >>> STATES.constants['ONLINE'] is STATES.for_constant('ONLINE')
    True
    >>> STATES.values[2] is STATES.for_value(2)
    True
    >>> STATES.displays['Offline'] is STATES.for_display('Offline')
    True

If you want these dicts to be ordered, you can pass the dict class to use to the
``Choices`` constructor:

.. code-block:: python

    from collections import OrderedDict
    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
        dict_class = OrderedDict
    )

You can check if a constant, value, or display name exists:

.. code-block:: python

    >>> STATES.has_constant('ONLINE')
    True
    >>> STATES.has_value(1)
    True
    >>> STATES.has_display('Online')
    True

You can create subsets of choices within the sane ``Choices`` instance:

.. code-block:: python

    >>> STATES.add_subset('NOT_ONLINE', ('DRAFT', 'OFFLINE',))
    >>> STATES.NOT_ONLINE
    (2, 'Draft')
    (3, 'Offline')

Now, ``STATES.NOT_ONLINE`` is a real ``Choices`` instance, with a subset of the main ``STATES``
instance.

You can use it to generate choices for when you only want a subset of choices available:

.. code-block:: python

    offline_state = models.PositiveSmallIntegerField(
        choices=STATES.NOT_ONLINE,
        default=STATES.DRAFT
    )

As the subset is a real ``Choices`` instance, you have the same attributes and methods:

.. code-block:: python

    >>> STATES.NOT_ONLINE.for_constant('OFFLINE').value
    3
    >>> STATES.NOT_ONLINE.for_value(1).constant
    Traceback (most recent call last):
    ...
    KeyError: 3
    >>> list(STATES.NOT_ONLINE.constants.keys())
    ['DRAFT', 'OFFLINE]
    >>> STATES.NOT_ONLINE.has_display('Online')
    False

You can create as many subsets as you want, reusing the same constants if needed:

.. code-block:: python

    STATES.add_subset('NOT_OFFLINE', ('ONLINE', 'DRAFT'))

If you want to check membership in a subset you could do:

.. code-block:: python

    def is_online(self):
        # it's an example, we could have just tested with STATES.ONLINE
        return self.state not in STATES.NOT_ONLINE_DICT

You can add choice entries in many steps using ``add_choices``, possibly creating subsets at
the same time.

To construct the same ``Choices`` as before, we could have done:

.. code-block:: python

    STATES = Choices()
    STATES.add_choices(
        ('ONLINE', 1, 'Online)
    )
    STATES.add_choices(
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
        name='NOT_ONLINE'
    )

Notes
-----

* You also have a very basic field (``NamedExtendedChoiceFormField```) in ``extended_choices.fields`` which accept constant names instead of values
* Feel free to read the source to learn more about this little django app.
* You can declare your choices where you want. My usage is in the ``models.py`` file, just before the class declaration.

Compatibility
-------------

The version 1 provides a totally new API, but stays fully compatible with the previous one
(``0.4.1``). So it adds a lot of attributes in each ``Choices`` instance:

* ``CHOICES``
* ``CHOICES_DICT``
* ``REVERTED_CHOICES_DICT``
* ``CHOICES_CONST_DICT``

(And 4 more for each subset)

If you don't want it, simply set the argument ``retro_compatibility`` to ``False`` when creating
a ``Choices`` instance:

.. code-block:: python

    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
        retro_compatibility=False
    )

This flag is currently ``True`` by default, and it will not be changed for at least 6 months
counting from the publication of this version 1 (1st of May, 2015, so until the 1st of November,
2015, AT LEAST, the compatibility will be on by default).

Then, the flag will stay but will be off by default. To keep compatibility, you'll have to
pass the ``retro_compatibility`` argument and set it to ``True``.

Then, after another period of 6 months minimum, the flag and all the retro_compatibility code
will be removed (so not before 1st of May, 2016).

Note that you can stay to a specific version by pinning it in your requirements.


License
-------

Licensed under the General Public License (GPL). See the ``LICENSE`` file included

Python 3?
---------

Of course! We support python 2.6, 2.7, 3.3 and 3.4, for Django version 1.4.x to 1.8.x,
respecting the `django matrix`_ (except for python 2.5 and 3.2)


Tests
-----

To run tests from the code source, create a virtualenv or activate one, install django, then::

    python -m extended_choices.tests


We also provides some quick doctests in the code documentation. To execute them::

    python -m extended_choices.choices


Source code
-----------

The source code is available on Github_


Developing
----------

If you want to participate to the development of this library, you'll need ``django``
installed in your virtualenv. If you don't have it, simply run::

    pip install -r requirements-dev.txt

Don't forget to run the tests ;)

Feel free to propose a pull request on Github_!

A few minutes after your pull request, tests will be executed on TravisCi_ for all the versions
of python and django we support.


Documentation
-------------

You can find the documentation on ReadTheDoc_

To update the documentation, you'll need some tools::

    pip install -r requirements-makedoc.txt

Then go to the ``docs`` directory, and run::

    make html

Author
------
Written by Stephane "Twidi" Angel <s.angel@twidi.com> (http://twidi.com), originally for http://www.liberation.fr

.. _choices: http://docs.djangoproject.com/en/1.5/ref/models/fields/#choices
.. _django: http://www.djangoproject.com/
.. _Github: https://github.com/twidi/django-extended-choices
.. _django matrix: https://docs.djangoproject.com/en/1.8/faq/install/#what-python-version-can-i-use-with-django
.. _TravisCi: https://travis-ci.org/twidi/django-extended-choices/pull_requests
.. _RedTheDoc: http://django-extended-choices.readthedocs.org

.. |PyPI Version| image:: https://img.shields.io/pypi/v/django-extended-choices.png
   :target: https://pypi.python.org/pypi/django-extended-choices
   :alt: PyPI Version
.. |Build Status| image:: https://travis-ci.org/twidi/django-extended-choices.png
   :target: https://travis-ci.org/twidi/django-extended-choices
   :alt: Build Status on Travis CI
.. |Doc Status| image:: https://readthedocs.org/projects/django-extended-choices/badge/?version=latest
   :target: http://django-extended-choices.readthedocs.org
   :alt: Documentation Status on ReadTheDoc

.. image:: https://d2weczhvl823v0.cloudfront.net/twidi/django-extended-choices/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free
