class hashdict(dict):
    """
    hashable dict implementation, suitable for use as a key into
    other dicts or sets

    based on answers from
       http://stackoverflow.com/questions/1151658/python-hashable-dicts
    """
    def __key(self):
        try:
            return self.hashdict_key
        except AttributeError:
            pass
        k = self.hashdict_key = tuple(sorted(self.items()))
        return k

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__,
            ", ".join("{0}={1}".format(
                    str(i[0]),repr(i[1])) for i in self.__key()))

    def __hash__(self):
        try:
            return self.hashdict_hash
        except AttributeError:
            pass
        h = self.hashdict_hash = hash(self.__key())
        return h

    def __setitem__(self, key, value):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    def __delitem__(self, key):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    def clear(self):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    def pop(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    def popitem(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    def setdefault(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    def update(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))

    # update is not ok because it mutates the object
    # __add__ is ok because it creates a new object
    # while the new object is under construction, it's ok to mutate it
    def __add__(self, right):
        result = hashdict(self)
        dict.update(result, right)
        return result
