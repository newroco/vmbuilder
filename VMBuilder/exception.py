"""VMBuilderException is currently the exact same as Exception,
but having a separate class for it allows us to catch those, but
let others bubble to the user."""

class VMBuilderException(Exception):
    pass
