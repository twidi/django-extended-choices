django-extended-choices is a little application to improve django choices (or whatever, no dependencies)

The aim is to replace this :

    STATE_ONLINE  = 1
    STATE_DRAFT   = 2
    STATE_OFFLINE = 3

    STATE_CHOICES = (
        (STATE_ONLINE,  'Online'),
        (STATE_DRAFT,   'Draft'),
        (STATE_OFFLINE, 'Offline'),
    )

    STATE_DICT = dict(STATE_CHOICES)

    class ContentModel(models.Model):
        title      = models.CharField(max_length=255)
        content    = models.TextField()
        state      = models.PositiveSmallIntegerField(choices=STATE_CHOICES, default=STATE_DRAFT)
        related_to = models.ManyToManyField('self', through="ContentToContent", symmetrical=False, blank=True, null=True)

        def __unicode__(self):
            return u'Content "%s" (state=%s)' % (self.title, STATE_DICT[self.state])

        def get_related_content(self):
            return self.related_to.select_related().filter(state=STATE_ONLINE)

by this :

    from extended_choices import Choices

    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
    )

    class ContentModel(models.Model):
        title      = models.CharField(max_length=255)
        content    = models.TextField()
        state      = models.PositiveSmallIntegerField(choices=STATES.CHOICES, default=STATES.DRAFT)
        related_to = models.ManyToManyField('self', through="ContentToContent", symmetrical=False, blank=True, null=True)

        def __unicode__(self):
            return u'Content "%s" (state=%s)' % (self.title, STATES.CHOICES_DICT[self.state])

        def get_related_content(self):
            return self.related_to.select_related().filter(state=STATES.ONLINE)

As you can see, there is only one declaration for all states, with, for each state in order :
    - the pseudo-constant name which can be used (STATES.ONLINE replace the previous STATE_ONLINE)
    - the value to use as key in database
    - the name to be displayed

And then, you can use :

`STATES.CHOICES` to use with `choices=` in fields declarations
`STATES.CHOICES_DICT` a dict to get the value to display with the key used in database
`STATES.CHOICES_RDICT`, a dict to get the key from the displayable value (can be usefull in some case)

To use another name than `CHOICES` :dd a name parameter as a named argument to the constructor

    STATES = Choices(
        ('ONLINE',  1, 'Online'),
        ('DRAFT',   2, 'Draft'),
        ('OFFLINE', 3, 'Offline'),
        name = 'OUR_STATES'
    )

    # ...
        state = models.PositiveSmallIntegerField(choices=STATES.OUR_STATES, default=STATES.DRAFT)
    # ...

And you can add others choices within the same variable :

    STATES.add_choices('OLD_STATES', (
        ('VISIBLE', 10, 'Visible'),
        ('HIDDEN',  20, 'Hidden'),
    ))

    class ContentModel(models.Model):
    # ...
        state     = models.PositiveSmallIntegerField(choices=STATES.OUR_STATES, default=STATES.DRAFT)
        old_state = models.PositiveSmallIntegerField(choices=STATES.OLD_STATES, default=STATES.VISIBLE)
    # ...
        def __unicode__(self):
            return u'Content "%s" (state=%s, old state=%s)' % (self.title, STATES.OUR_STATES_DICT[self.state], STATES.OLD_STATES[self.old_state])

When `add_choices` is used, the `CHOICES` (here `STATES.OLD_STATES`), and the two dictionnaries are initialized.
If a constant name (firt entry in a tuple)  is declared more than one time, the first declared value (second entry of a tuple) is used.

Originaly written by Stephane Angel <s.angel@twidi.com> (http://twidi.com) for http://www.liberation.fr
