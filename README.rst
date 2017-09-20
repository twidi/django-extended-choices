|PyPI Version| |Build Status| |Doc Status|

django-extended-choices
=======================

A little application to improve Django choices
----------------------------------------------

``django-extended-choices`` aims to provide a better and more readable
way of using choices_ in Django_.

Installation
------------

You can install directly via pip (since version ``0.3``)::

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
* the value to use in the database - which could equally be a string
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

To allow this, we had to remove support for ``None`` values. Use empty strings instead.

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

Or the following dicts, using constants, values or display names, as keys, and the matching
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

Since version ``1.1``, the new ``OrderedChoices`` class is provided, that is exactly that:
a ``Choices`` using ``OrderedDict`` by default for ``dict_class``.

You can check if a constant, value, or display name exists:

.. code-block:: python

    >>> STATES.has_constant('ONLINE')
    True
    >>> STATES.has_value(1)
    True
    >>> STATES.has_display('Online')
    True

You can create subsets of choices within the same ``Choices`` instance:

.. code-block:: python

    >>> STATES.add_subset('NOT_ONLINE', ('DRAFT', 'OFFLINE',))
    >>> STATES.NOT_ONLINE
    (2, 'Draft')
    (3, 'Offline')

Now, ``STATES.NOT_ONLINE`` is a real ``Choices`` instance, with a subset of the main ``STATES``
constants.

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

You can also pass the ``argument`` to the ``Choices`` constructor to create a subset with all
the choices entries added at the same time (it will call ``add_choices`` with the name and the
entries)

The list of existing subset names is in the ``subsets`` attributes of the parent ``Choices``
object.

If you want a subset of the choices but not save it in the original ``Choices`` object, you can
use ``extract_subset`` instead of ``add_subset``

.. code-block:: python

    >>> subset = STATES.extract_subset('DRAFT', 'OFFLINE')
    >>> subset
    (2, 'Draft')
    (3, 'Offline')


As for a subset created by ``add_subset``, you have a real ``Choices`` object, but not accessible
from the original ``Choices`` object.

Note that in ``extract_subset``, you pass the strings directly, not in a list/tuple as for the
second argument of ``add_subset``.

Notes
-----

* You also have a very basic field (``NamedExtendedChoiceFormField```) in ``extended_choices.fields`` which accept constant names instead of values
* Feel free to read the source to learn more about this little Django app.
* You can declare your choices where you want. My usage is in the ``models.py`` file, just before the class declaration.

Compatibility
-------------

The version ``1.0`` provided a totally new API, and compatibility with the previous one
(``0.4.1``) was removed in ``1.1``. The last version with the compatibility was ``1.0.7``.

If you need this compatibility, you can use a specific version by pinning it in your requirements.

License
-------

Available under the BSD_ License. See the ``LICENSE`` file included

Python versions support
---------

``django-extended-choices`` Python support follow the `Django Python support matrix`_:


+----------------+-------------------------------------------------+
| Django version | Python versions                                 |
+----------------+-------------------------------------------------+
| 1.8            | 2.7, 3.2 (until the end of 2016), 3.3, 3.4, 3.5 |
+----------------+-------------------------------------------------+
| 1.9, 1.10      | 2.7, 3.4, 3.5                                   |
+----------------+-------------------------------------------------+
| 1.11           | 2.7, 3.4, 3.5, 3.6                              |
+----------------+-------------------------------------------------+


Tests
-----

To run tests from the code source, create a virtualenv or activate one, install Django, then::

    python -m extended_choices.tests


We also provides some quick doctests in the code documentation. To execute them::

    python -m extended_choices.choices


Note: the doctests will work only in python version not display `u` prefix for strings.


Source code
-----------

The source code is available on Github_.


Developing
----------

If you want to participate in the development of this library, you'll need ``Django``
installed in your virtualenv. If you don't have it, simply run::

    pip install -r requirements-dev.txt

Don't forget to run the tests ;)

Feel free to propose a pull request on Github_!

A few minutes after your pull request, tests will be executed on TravisCi_ for all the versions
of python and Django we support.


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
.. _Django: http://www.djangoproject.com/
.. _Github: https://github.com/twidi/django-extended-choices
.. _Django Python support matrix: https://docs.djangoproject.com/en/1.11/faq/install/#what-python-version-can-i-use-with-django
.. _TravisCi: https://travis-ci.org/twidi/django-extended-choices/pull_requests
.. _ReadTheDoc: http://django-extended-choices.readthedocs.org
.. _BSD: http://opensource.org/licenses/BSD-3-Clause

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
