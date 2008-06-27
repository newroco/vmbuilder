import os

def load_plugins():
    for plugin_dir in __path__:
        for p in os.listdir(plugin_dir):
            path = '%s/%s' % (plugin_dir, p)
            if os.path.isdir(path) and os.path.isfile('%s/__init__.py' % path):
                exec "import VMBuilder.plugins.%s" % p
