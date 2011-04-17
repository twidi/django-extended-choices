class Choices:
    """
    Helper to easily create objects for use with the "choices" parameter
    for models fields.

    Default call exemple, with n tuples(constant name, value, string)

        CHOICES_A = Choices(
            ('THE_A_1', 11, u'a_1'),
            ('THE_A_2', 12, u'a_2'),
        )

    Default call create, for CHOICES_A :
     * all named constant (THE_A_1 and THE_A_2)
     * a tuple CHOICES ( (11, u'a_1'), (12, u'a_2') )
     * a dict CHOICES_DICT { 11 => u'a_1', 12 => u'a_2' }
     * a dict CHOICES_RDICT { u'a_1' => 11, u'a_2' => 12 }

    If you want all these names not to contain "CHOICES" but an other name,
    you can add it to the call :

        CHOICES_A = Choices(
            ('THE_A_1', 11, u'a_1'),
            ('THE_A_2', 12, u'a_2'),
            name = 'FOO'
        )

    This exemple will create all constants (no changes here), and FOO will
    be used in place of CHOICES, and FOO_DICT and FOO_RDICT in place of
    CHOICES_DICT and CHOICES_RDICT

    If you want to create other choices for the same instance, you can
    use the add_choices method
    This method take a name (to use in place of "CHOICES" in all variable
    names), and then all the tuples like in the constructor

        CHOICES_A.add_choices('BAR',
            ('THE_A_1', 11, 'a_1_bis'),
            ('THE_A_2', 13, 'a_3'),
        )

    This exemple will create all constants (except for those which already
    exists : we don't create them and ignore the value as we get the one for
    the existed constant), here just THE_A_2,  and add BAR, BAR_DICT and
    REVERTED_BAR_DICT
    """

    def __init__(self, *choices, **kwargs):
        name = kwargs.get('name', 'CHOICES')
        self.add_choices(name, *choices)

    def add_choices(self, name, *choices):

        CHOICES = []
        CHOICES_DICT = {}
        CHOICES_RDICT = {}

        for choice in choices:
            const, value, string = choice
            if not hasattr(self, const):
                setattr(self, const, value)
            else:
                value = getattr(self, const)
            CHOICES.append((value, string))
            CHOICES_DICT[value] = string
            CHOICES_RDICT[string] = value

        setattr(self, name, tuple(CHOICES))
        setattr(self, '%s_DICT' % name, CHOICES_DICT)
        setattr(self, '%s_RDICT' % name, CHOICES_RDICT)

