Changelog
=========

In development
--------------
* officiel support for Python 3.7 and Django 2.1

Release *v1.3* - ``2018-02-17``
-------------------------------
* correct inability fo ``Auto*Choices`` be able to have subsets
* `Auto*Choices` can accept entries with forced value/display
* additional attributes are now correctly (un)pickled
* additional attributes are now also accessible from constant/value/display

Release *v1.2* - ``2018-02-01``
-------------------------------
* add ``AutoChoices`` and ``AutoDisplayChoices``
* document the fourth argument to tuples to pass additional attributes
* remove support for Python 3.3
* add support for Django 2.0

Release *v1.1.2* - ``2017-09-20``
---------------------------------
* add ``__all__`` at package root
* supports Django 1.8, 1.9, 1.10 and 1.11
* follow the latests django/python support matrix
* tested on travis via tox (tests, pep8 validation and code coverage)

Release *v1.1.1* - ``2016-11-03``
---------------------------------
* make ``OrderedChoices`` available at the package root

Release *v1.1* - ``2016-11-03``
-------------------------------
* add the ``extract_subset`` method
* add the ``OrderedChoices`` subclass
* add support for Django 1.10
* drop retro-compatibility support

Release *v1.0.7* - ``2016-03-13``
---------------------------------
* ensure falsy values are considered as so

Release *v1.0.6* - ``2016-02-12``
---------------------------------
* add compatibility with "display" values set using ``ugettext_lazy``

Release *v1.0.5* - ``2015-10-14``
---------------------------------
* add compatibility with the  ``pickle`` module

Release *v1.0.4* - ``2015-05-05``
---------------------------------
* explicitly raise ``ValueError`` when using ``None`` for constant, value or display name.

Release *v1.0.3* - ``2015-05-05``
---------------------------------
* make it work again with Django ``ugettext_lazy``
* remove support for Django 1.4

Release *v1.0.2* - ``2015-05-02``
---------------------------------
* change License from GPL to BSD

Release *v1.0* - ``2015-05-01``
-------------------------------
* full rewrite
* new API
* still compatible 0.4.1
