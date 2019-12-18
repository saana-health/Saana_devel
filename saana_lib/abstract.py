from abc import ABCMeta


class OutIn:
    __metaclass__ = ABCMeta

    def store(self):
        """
        stores the current table content to file
        """
        raise NotImplementedError()

    def sequence(self):
        """
        returns a sequence of all tags (if it's Table) or
        cells (if it's Matrix)
        """
        raise NotImplementedError()

