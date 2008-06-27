import os
import textwrap
import optparse
import log
from optparse import OptionContainer
from gettext import gettext
_ = gettext

class MyOptParser(optparse.OptionParser):
    def format_arg_help(self, formatter):
        result = []
        for arg in self.arg_help:
            result.append(self.format_arg(formatter, arg))
        return "".join(result)

    def format_arg(self, formatter, arg):
        result = []
        arghelp = arg[1]()
        arg = arg[0]
        width = formatter.help_position - formatter.current_indent - 2
        if len(arg) > width:
            arg = "%*s%s\n" % (self.current_indent, "", arg)
            indent_first = formatter.help_position
        else:                       # start help on same line as opts
            arg = "%*s%-*s  " % (formatter.current_indent, "", width, arg)
            indent_first = 0
        result.append(arg)
        help_lines = textwrap.wrap(arghelp, formatter.help_width)
        result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
        result.extend(["%*s%s\n" % (formatter.help_position, "", line)
                           for line in help_lines[1:]])
        return "".join(result)

    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        if self.arg_help:
            result.append(formatter.format_heading(_("Arguments")))
            formatter.indent()
            result.append(self.format_arg_help(formatter))
            result.append("\n")
            formatter.dedent()
        result.append(formatter.format_heading(_("Options")))
        formatter.indent()
        if self.option_list:
            result.append(OptionContainer.format_option_help(self, formatter))
            result.append("\n")
        for group in self.option_groups:
            result.append(group.format_help(formatter))
            result.append("\n")
        formatter.dedent()
        # Drop the last "\n", or the header if no options or option groups:
        return "".join(result[:-1])


def create_optparser():
    epilog = 'ubuntu-vm-builder is Copyright (C) 2007-2008 Canonical Ltd. and written by Soren Hansen <soren@canonical.com>'
    optparser = MyOptParser(epilog=epilog, usage='%prog hypervisor distro [distro specific args] [options]')
    optparser.arg_help = (('hypervisor', hypervisor_help), ('distro', distro_help),)

    if 'TMPDIR' in os.environ.keys():
        optparser.set_defaults(tmp=os.environ['TMPDIR'])
    else:
        optparser.set_defaults(tmp='/tmp')

    optparser.add_option('-c', dest='altconfig', default='~/.ubuntu-vm-builder', help='Specify a optional configuration file [default: %default]')
    optparser.add_option('-d', '--dest', help='Specify the destination directory. [default: <hypervisor>-<distro>]')
    optparser.add_option('--debug', action='callback', callback=log.set_verbosity, help='Show debug information')
    optparser.add_option('-v', '--verbose', action='callback', callback=log.set_verbosity, help='Show progress information')
    optparser.add_option('-q', '--quiet', action='callback', callback=log.set_verbosity, help='Silent operation')
    optparser.add_option('-t', '--tmp', help='Use TMP as temporary working space for image generation. Defaults to $TMPDIR if it is defined or /tmp otherwise. [default: %default]')
    optparser.add_option('-o', '--overwrite', action='store_true', default='False', help='Force overwrite of destination directory if it already exist. [default: %default]')
    optparser.add_option('--in-place', action='store_true', default='False', help='Install directly into the filesystem images. This is needed if your \$TMPDIR is nodev and/or nosuid, but will result in slightly larger file system images.')
    optparser.add_option('--tmpfs', metavar="OPTS", help='Use a tmpfs as the working directory, specifying its size or "-" to use tmpfs default (suid,dev,size=1G).')
    optparser.add_option('--mem', type='int', default=128, help='Assign MEM megabytes of memory to the guest vm. [default: %default]')
    optparser.add_option('--rootsize', metavar='SIZE', type='int', default=4096, help='Size (in MB) of the root filesystem [default: %default]')
    optparser.add_option('--optsize', metavar='SIZE', type='int', default=0, help='Size (in MB) of the /opt filesystem. If not set, no /opt filesystem will be added.')
    optparser.add_option('--swapsize', metavar='SIZE', type='int', default=1024, help='Size (in MB) of the swap partition [default: %default]')

    return optparser

def distro_help():
    return 'Distro. Valid options: %s' % " ".join(VMBuilder.distros.keys())

def hypervisor_help():
    return 'Hypervisor. Valid options: %s' % " ".join(VMBuilder.hypervisors.keys())

