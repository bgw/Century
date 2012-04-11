import abc

class DataHint(metaclass=abc.ABCMeta):
    """The :class:`DataHint` type represents a piece of information which is not
    yet known. When processing a Person field containing a value that is a list
    of instances of this class, it gets passed back to
    :meth:`lib.tasks.phonebook.PhonebookBackend.process_datahint`, which can
    then attempt to look the information up, and return a dictionary of
    key-value pairs of newfound information.
    
    .. note::
        The value of a Person's field should not be a :class:`DataHint` object
        itself, but rather a list of DataHint objects.
    
    .. note::
        While the value of a Person's field can be a list of these objects, if
        you are just using the API (not extending it), you won't ever
        see :class:`DataHint` objects, as they should already resolved to a
        final value or ``None`` by the time you get anything.
    
    An example of this in action takes place in the
    :mod:`lib.tasks.phonebook.http` backend. We get our initial person data from
    the html results page, requring only one page load. Further information is
    often available, but only by pulling up the person's page, requiring a page
    load for each person. To keep unnecessary page loads to a minimum,
    :class:`DataHint` objects are used, so that the data is only checked for
    when requested.
    
    This class itself is just an abstract stub to represent type."""
    pass

class Person(dict):
    """A representation of information known about a person. By extending
    :class:`dict`, one can access data like::
    
        name, email = person["name"], person["email"]
    
    .."""
    def __init__(self, *args, **kwargs):
        identifier = kwargs.pop("identifier", id(self))
        backend = kwargs.pop("backend")
        dict.__init__(self, *args, **kwargs)
        self.__identifier = identifier
        self._callback = backend.process_datahint
        self.__checked_datahints = set()
        for key in backend.fields:
            # if something isn't declared, make sure its None
            if key not in self:
                dict.__setitem__(self, key, None)
        assert set(backend.fields) == self.keys()
    
    def get_identifier(self):
        """Gets the value of :attr:`identifier`."""
        return self.__identifier
    
    identifier = property(get_identifier, doc="""
        An immutable value, unique to a person, that is used for equality and
        identification. The value is typically one passed into the constructor,
        based on some sort of :class:`lib.tasks.phonebook.PhonebookBackend`
        derived value, allowing equality to be tested between different
        :class:`lib.tasks.phonebook.Phonebook` instances. If a value isn't
        passed into the constructor by the
        :class:`lib.tasks.phonebook.PhonebookBackend`, this value is identical
        to ``id(self)``.""")
    
    def __eq__(self, other):
        """Compares Person objects based on their :attr:`identifier` attribute.
        """
        return self.identifier == other.identifier
    
    def __getitem__(self, key):
        """Retrieves the information of a person related to a given ``key``.
        :class:`DataHint` objects will be processed in this step, so execution
        time could be variable."""
        if key not in self:
            return None
        value = dict.__getitem__(self, key)
        while self._is_datahint(value):
            data_hint = value.pop(0)
            if not len(value): # if this is our last DataHint
                dict.__setitem__(self, key, None)
                value = None
            if data_hint in self.__checked_datahints:
                # we already checked the datahint when processing another field,
                # if we didn't find anything out from that, we ain't gonna now
                continue
            self.__checked_datahints.add(data_hint)
            solved_fields = self._callback(data_hint)
            for k, v in solved_fields.items():
                if k not in self:
                    raise Exception("The key \"%s\" is not defined in this "
                                    "Person. All fields must have predefined "
                                    "keys." % k)
                if self._is_datahint(dict.__getitem__(self, k)):
                    # only fill it in if we don't already know it, avoiding
                    # mutating a field
                    dict.__setitem__(self, k, v)
            value = dict.__getitem__(self, key)
        return value
    
    @staticmethod
    def _is_datahint(value):
        """A helper method that returns ``True`` if ``value`` is *a list of*
        :class:`DataHint` objects, ``False`` otherwise."""
        try:
            value[0]
        except:
            return False
        else:
            return isinstance(value[0], DataHint)
    
    def __setitem__(self, key, value):
        """Calling this (directly or indirectly) will raise an exception. A
        :class:`Person` should largely be immutable."""
        raise Exception("""
            A :class:`Person`'s field values shouldn't be explicitly changed, as
            that violates the idea that a :class:`Person` is largely
            immutable.""")
    
    def __delitem__(self, key):
        """Calling this (directly or indirectly) will raise an exception. A
        :class:`Person` should largely be immutable."""
        self[None] = None
    
    def __repr__(self):
        for key in self:
            self[key] # process all the datahints
        return "Person(identifier=%s, **%s)" % \
               (repr(self.identifier), dict.__repr__(self))
