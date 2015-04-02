django-extended-choices
=======================

A little application to improve django choices (or whatever: no dependencies)
-----------------------------------------------------------------------------

django-extended-choices aims to provide a better (ie for me) and more readable
way of using choices_ in django_

------------
Installation
------------

You can install directly via pip (since version `0.3`)::

    $ pip install django-extended-choices

Or from the github_ repository (`master` branch by default)::

    $ git clone git://github.com/twidi/django-extended-choices.git
    $ cd django-extended-choices
    $ sudo python setup.py install

-----
Usage
-----

The aim is to replace this::

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

by this ::

    from extended_choices import Choices

    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
    )

    class Content(models.Model):
        title      = models.CharField(max_length=255)
        content    = models.TextField()
        state      = models.PositiveSmallIntegerField(choices=STATES.CHOICES, default=STATES.DRAFT)

        def __unicode__(self):
            return u'Content "%s" (state=%s)' % (self.title, STATES.CHOICES_DICT[self.state])

    print(Content.objects.filter(state=STATES._ONLINE))


As you can see there is only one declaration for all states with, for each state, in order:

* the pseudo-constant name which can be used (`STATES.ONLINE` replaces the previous `STATE_ONLINE`)
* the value to use as key in database
* the name to be displayed

And then, you can use:

* `STATES.CHOICES`, to use with `choices=` in fields declarations
* `STATES.CHOICES_DICT`, a dict to get the value to display with the key used in database
* `STATES.REVERTED_CHOICES_DICT`, a dict to get the key from the displayable value (can be useful in some case)
* `STATES.CHOICES_CONST_DICT`, a dict to get value from constant name
* `STTES.REVERTED_CHOICES_CONST_DICT`, a dict to get constant name from value

Note that each of these attribute can be accessed via a dict key (`STATES['ONLINE']` for example) if
 you want to fight your IDE that may warn you about undefined attributes.

You can create subsets of choices within the sane variable::

    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
    )

    STATES.add_subset('NOT_ONLINE', ('DRAFT', 'OFFILNE',))

Now, `STATES.NOT_ONLINE` is a full `Choices` object, with a subset of the main STATES choices.
You can use it in a filter::

    def is_online(self):
        # it's an example, we could have test STATES.ONLINE
        return self.state not in STATES.NOT_ONLINE

`not in` ? Yes, you can use `in` and even iterate on Choices objects !

If you want dicts to be ordered, you can pass the dict class to use to the `Choices` constructor::

    from collections import OrderedDict
    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
        dict_class = OrderedDict
    )

-----
Notes
-----

* You also have a very basic field (`NamedExtendedChoiceFormField`) in `extended_choices.fields` which accept constant names instead of values
* Feel free to read the source to learn more about this little django app.
* You can declare your choices where you want. My usage is in the models.py file, just before the class declaration.

------
Future
------

* Next version (1.0 ?) will **NOT** be compatible with 0.X ones, because all the names (`*_DICT`) will be renamed to be easier to memorize (using names "ala" `as_dict`...)


-------
License
-------

Licensed under the General Public License (GPL). See the `License` file included


-----------
Source code
-----------

The source code is available on github_

-----
Tests
-----

To run tests from the code source, create a virtualenv or activate one, install django, then::

    python -m extended_choices.tests


------
Author
------
Written by Stephane "Twidi" Angel <s.angel@twidi.com> (http://twidi.com), originally for http://www.liberation.fr

.. _choices: http://docs.djangoproject.com/en/1.5/ref/models/fields/#choices
.. _django: http://www.djangoproject.com/
.. _github: https://github.com/twidi/django-extended-choices


.. image:: https://d2weczhvl823v0.cloudfront.net/twidi/django-extended-choices/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free

