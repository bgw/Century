import abc

class DataHint(metaclass=abc.ABCMeta):
    pass

class Person(dict):
    def __init__(self, *args, **kwargs):
        identifier = kwargs.pop("identifier", id(self))
        backend = kwargs.pop("backend")
        dict.__init__(self, *args, **kwargs)
        self.__identifier = identifier
        self._callback = backend.process_datahint
    
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
        return self._identifier == other.identifier
    
    def __getitem__(self, key):
        if key not in self:
            return None
        value = dict.__getitem__(key)
        while self._is_datahint(value)
            solved_fields = self._callback(value.pop(0))
            if not len(value): # if this is our last DataHint
                dict.__setitem__(key, None)
            for k, v in solved_fields.items():
                if k not in self:
                    raise Exception("The key "%s" is not defined in this "
                                    "Person. All fields must have predefined "
                                    "keys.")
                if self._is_datahint(dict.__getitem__(k)):
                    dict.__setitem__(k, v)
            value = self.__getitem__(key)
        return value
    
    @staticmethod
    def _is_datahint(value):
        try:
            value[0]
        except TypeError:
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
        return "Person(identifier=%s, **%s)" %
               (repr(self.identifier), dict.__repr__(self))
