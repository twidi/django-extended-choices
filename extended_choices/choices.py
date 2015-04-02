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
    >>> CHOICES_ALIGNEMENT.CHOICES_CONST_DICT['NEUTRAL']
    20
    >>> CHOICES_ALIGNEMENT.REVERTED_CHOICES_CONST_DICT[20]
    'NEUTRAL'

    As you can see in the above example usage, Choices objects gets five
    attributes:
    - one attribute built after constant names provided in the tuple (like BAD,
      NEUTRAL etc...)
    - a CHOICES_DICT that match value to string
    - a REVERTED_CHOICES_DICT that match string to value
    - a CHOICES_CONST_DICT that match constant to value
    - a REVERTED_CHOICES_CONST_DICT that match value to constant

    You can also check membership of choices directly:

    >>> 10 in CHOICES_ALIGNEMENT
    True
    >>> 11 in CHOICES_ALIGNEMENT
    False

    If you want to create subset of choices, you can
    use the add_subset method
    This method take a name, and then the constants you want to
    have in this subset:

    >>> CHOICES_ALIGNEMENT.add_subset('WESTERN',('BAD', 'GOOD'))
    >>> CHOICES_ALIGNEMENT.WESTERN
    ((10, u'bad'), (40, u'good'))
    >>> CHOICES_ALIGNEMENT.BAD in CHOICES_ALIGNEMENT.WESTERN_DICT
    True
    >>> CHOICES_ALIGNEMENT.REVERTED_WESTERN_DICT[u'bad']
    10
    """

    def __init__(self, *choices, **kwargs):
        # allow usage of collections.OrdereDdict for example
        self.dict_class = kwargs.get('dict_class', dict)

        self.CHOICES = tuple()
        self.CHOICES_DICT = self.dict_class()
        self.REVERTED_CHOICES_DICT = self.dict_class()
        # self.CHOICES_CONST_DICT['const'] is the same as getattr(self, 'const')
        self.CHOICES_CONST_DICT = self.dict_class()
        self.REVERTED_CHOICES_CONST_DICT = self.dict_class()
        # For retrocompatibility
        name = kwargs.get('name', 'CHOICES')
        if name != "CHOICES":
            self.add_choices(name, *choices)
        else:
            self._build_choices(*choices)

    def __contains__(self, item):
        """
        Make smarter to check if a value is valid for a Choices.
        """
        return item in self.CHOICES_DICT

    def __iter__(self):
        return self.CHOICES.__iter__()

    def __getitem__(self, key):
        if not hasattr(self, key):
            raise KeyError("Key Error : '" + str(key) + "' not found")
        return getattr(self, key)

    def _build_choices(self, *choices):
        CHOICES = list(self.CHOICES)  # for retrocompatibility
                                      # we may have to call _build_choices
                                      # more than one time and so append the
                                      # new choices to the already existing ones
        for choice in choices:
            const, value, string = choice
            if hasattr(self, const):
                raise ValueError(u"You cannot declare two constants "
                                  "with the same name! %s " % unicode(choice))
            if value in self.CHOICES_DICT:
                raise ValueError(u"You cannot declare two constants "
                                  "with the same value! %s " % unicode(choice))
            setattr(self, const, value)
            CHOICES.append((value, string))
            self.CHOICES_DICT[value] = string
            self.REVERTED_CHOICES_DICT[string] = value
            self.CHOICES_CONST_DICT[const] = value
            self.REVERTED_CHOICES_CONST_DICT[value] = const
        # CHOICES must be a tuple (to be immutable)
        setattr(self, "CHOICES", tuple(CHOICES))

    def add_choices(self, name="CHOICES", *choices):
        self._build_choices(*choices)
        if name != "CHOICES":
            # for retrocompatibility
            # we make a subset with new choices
            constants_for_subset = []
            for choice in choices:
                const, value, string = choice
                constants_for_subset.append(const)
            self.add_subset(name, constants_for_subset)

    def add_subset(self, name, constants):
        if hasattr(self, name):
            raise ValueError(u"Cannot use %s as a subset name."
                              "It's already an attribute." % name)
        SUBSET = []
        SUBSET_DICT = self.dict_class()  # retrocompatibility
        REVERTED_SUBSET_DICT = self.dict_class()  # retrocompatibility
        SUBSET_CONST_DICT = self.dict_class()
        REVERTED_SUBSET_CONST_DICT = self.dict_class()
        for const in constants:
            value = getattr(self, const)
            string = self.CHOICES_DICT[value]
            SUBSET.append((value, string))
            SUBSET_DICT[value] = string  # retrocompatibility
            REVERTED_SUBSET_DICT[string] = value  # retrocompatibility
            SUBSET_CONST_DICT[const] = value
            REVERTED_SUBSET_CONST_DICT[value] = const
        # Maybe we should make a @property instead
        setattr(self, name, tuple(SUBSET))

        # For retrocompatibility
        setattr(self, '%s_DICT' % name, SUBSET_DICT)
        setattr(self, 'REVERTED_%s_DICT' % name, REVERTED_SUBSET_DICT)
        setattr(self, '%s_CONST_DICT' % name, SUBSET_CONST_DICT)
        setattr(self, 'REVERTED_%s_CONST_DICT' % name, REVERTED_SUBSET_CONST_DICT)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
