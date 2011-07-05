class Choices:
    """
    Helper class for choices fields in Django.

    A choice value has three representation (constant name, value and
    string). So Choices takes list of such tuples.

    Here is an example of Choices use:

    >>> CHOICES_ALIGNEMENT = Choices(
    ...     ('BAD', 10, u'bad'),
    ...     ('NEUTRAL', 20, u'neutral'),
    ...     ('CHAOTIC_GOOD', 30, u'chaotic good'),
    ...     ('GOOD', 40, u'good'),
    ... )
    >>> CHOICES_ALIGNEMENT.BAD
    10
    >>> CHOICES_ALIGNEMENT.CHOICES_DICT[30]
    u'chaotic good'
    >>> CHOICES_ALIGNEMENT.REVERTED_CHOICES_DICT[u'good']
    40

    As you can see in the above example usage, Choices objects gets three
    attributes:
    - one attribute built after constant names provided in the tuple (like BAD,
      NEUTRAL etc...)
    - a CHOICES_DICT that match value to string
    - a REVERTED_CHOICES_DICT that match string to value

    If you don't like the word CHOICES, you can provide you own nomenclature.

    >>> ALIGNEMENTS = Choices(
    ...     ('BAD', 10, u'bad'),
    ...     ('NEUTRAL', 20, u'neutral'),
    ...     ('CHAOTIC_GOOD', 30, u'chaotic good'),
    ...     ('GOOD', 40, u'good'),
    ...     name='KIND'
    ... )
    >>> ALIGNEMENTS.KIND
    ((10, u'bad'), (20, u'neutral'), (30, u'chaotic good'), (40, u'good'))
    >>> ALIGNEMENTS.KIND_DICT[20]
    u'neutral'
    >>> ALIGNEMENTS.REVERTED_KIND_DICT[u'neutral']
    20

    If you want to create other choices for the same instance, you can
    use the add_choices method
    This method take a name (to use in place of "CHOICES" in all variable
    names), and then all the tuples like in the constructor

    >>> CHOICES_ALIGNEMENT.add_choices('WESTERN',
    ...                                ('UGLY', 50, 'ugly'),
    ...                                ('CHAOTIC_UGLY', 60, 'chaotic ugly'),
    ...                               )
    >>> CHOICES_ALIGNEMENT.WESTERN
    ((50, 'ugly'), (60, 'chaotic ugly'))
    >>> CHOICES_ALIGNEMENT.WESTERN_DICT
    {50: 'ugly', 60: 'chaotic ugly'}
    >>> CHOICES_ALIGNEMENT.REVERTED_WESTERN_DICT
    {'chaotic ugly': 60, 'ugly': 50}

    Constants that already exists won't be updated according to the new value:

    >>> CHOICES_ALIGNEMENT.add_choices('GOOD_KIND',
    ...                                ('GOOD', 100, 'good')
    ...                               )
    >>> CHOICES_ALIGNEMENT.GOOD
    40
    """

    def __init__(self, *choices, **kwargs):
        name = kwargs.get('name', 'CHOICES')
        self.add_choices(name, *choices)

    def add_choices(self, name, *choices):
        CHOICES = []
        CHOICES_DICT = {}
        REVERTED_CHOICES_DICT = {}

        for choice in choices:
            const, value, string = choice
            if not hasattr(self, const):
                setattr(self, const, value)
            else:
                value = getattr(self, const)
            CHOICES.append((value, string))
            CHOICES_DICT[value] = string
            REVERTED_CHOICES_DICT[string] = value

        setattr(self, name, tuple(CHOICES))
        setattr(self, '%s_DICT' % name, CHOICES_DICT)
        setattr(self, 'REVERTED_%s_DICT' % name, REVERTED_CHOICES_DICT)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
