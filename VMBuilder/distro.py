class Distro(object):
    def extend_optparser(self, optparser):
        """Add whatever you like to the optparser and return it"""
        return optparser

    def install(self, destdir):
        """Install the distro into destdir"""
        raise NotImplemented('Distro subclasses need to implement the install method')
