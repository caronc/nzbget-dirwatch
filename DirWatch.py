#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# DirWatch scan script for NZBGet to move nzb files detected elsewhere
# into NZBGet's file queue for processing.
#
# Copyright (C) 2016 Chris Caron <lead2gold@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
#


##############################################################################
### NZBGET SCHEDULER SCRIPT                                                ###

# The script searches the paths you tell it to for NZB-Files.  If one is found
# it is moved automatically for into the NZBGet incoming path for downloading.
#
# Info about this DirWatch NZB Script:
# Author: Chris Caron (lead2gold@gmail.com).
# Date: Mon, Oct 31th, 2016.
# License: GPLv3 (http://www.gnu.org/licenses/gpl.html).
# Script Version: 0.0.2
#
# The script takes a series of directories you want to monitor.
#
# NOTE: This script requires Python to be installed on your system.
#

##############################################################################
### OPTIONS                                                                ###

# Watch Paths.
#
# Specify the directories you want to monitor for NZB-Files.
# The Tildy (~) can be used to expand the path in efforts to support the home
# directory. You can specify as many paths as you want, simply just add a
# comma (,) to delimit them. eg:
#   path1, path2, path3, etc
#
#WatchPaths=~/Downloads, ~/Dropbox

# Maximum Archive Size in Kilobytes.
#
# If we find a Zip file within one of our WatchPath's (defined above), then we
# verify that it is no larger then this value (in Kilobytes). This is to
# prevent processing excessively large compressed files that in no way would
# have ever had an NZB-File in them anyway.
#
#MaxArchiveSizeKB=150

# Enable debug logging (yes, no).
#
# If you experience a problem, you can bet the developer of this script will
# have a much easier time troubleshootng it for you if your logs include
# debugging.  Debugging is made possible by flipping this flag here.
#
#Debug=no

### NZBGET SCHEDULER SCRIPT                                                ###
##############################################################################

import re
from os.path import join
from os.path import basename
from os.path import abspath
from os.path import dirname
from os.path import isdir
from os.path import isfile
from os.path import splitext
from os.path import expanduser
from os.path import exists
from shutil import move
from zipfile import ZipFile

# This is required if the below environment variables
# are not included in your environment already
import sys
sys.path.insert(0, join(dirname(__file__), 'DirWatch'))

# Script dependencies identified below
from datetime import timedelta
from datetime import datetime

# pynzbget Script Wrappers
from nzbget import SchedulerScript
from nzbget import EXIT_CODE
from nzbget import SCRIPT_MODE
from nzbget.Utils import tidy_path

# Regular expression for the handling of NZB-Files
NZB_FILE_RE = re.compile('^(?P<filename>.*)\.nzb$', re.IGNORECASE)

# Regular expression for the handling of ZIP-Files
ZIP_FILE_RE = re.compile('^(?P<filename>.*)\.zip$', re.IGNORECASE)

# The number of seconds a matched directory/file has to have aged before it
# is processed further.  This prevents the script from removing content
# that may being processed 'now'.  All content must be older than this
# to be considered. This value is represented in seconds.
DEFAULT_MATCH_MINAGE = 30

# The maximum size a compressed file can be before it is considered to
# be looked within for NZB-Files
DEFAULT_COMPRESSED_MAXSIZE_KB = 150

class DIRWATCH_MODE(object):
    # Move content to the path specified instead of deleting it
    MOVE = "Move"
    # Do nothing; just preview what was intended to be tidied
    PREVIEW = "Preview"

# TidyIt Modes
DIRWATCH_MODES = (
    DIRWATCH_MODE.PREVIEW,
    DIRWATCH_MODE.MOVE,
)

# Default in a Read-Only Mode; It's the safest way!
DIRWATCH_MODE_DEFAULT = DIRWATCH_MODE.PREVIEW

class DirWatchScript(SchedulerScript):
    """A Script for NZBGet to allow one to monitor multiple locations that
    may potentially contain an NZB-File.

    If a file is found, it's contents are automatically moved into the
    NZBGet queue for processing.
    """

    # Define our minimum age a file can be
    min_age = DEFAULT_MATCH_MINAGE

    # Define our maxium archive size a compressed file can be
    max_archive_size = DEFAULT_COMPRESSED_MAXSIZE_KB

    def _handle(self, source_path, target_dir):
        """
        A Simple wrapper to handle content in addition to logging it.
        """

        if not isfile(source_path):
            self.logger.warning(
                "The source file '%s' was not found (for handling)." % \
                source_path,
            )
            return False

        if not isdir(target_dir):
            self.logger.error(
                "The target directory '%s' was not found (for handling)." % \
                target_dir,
            )
            return False

        self.logger.info('Scanning Source: %s' % source_path)

        # Generate the new filename
        new_fullpath = join(
            target_dir,
            basename(source_path),
        )

        # Handle duplicate files by prefixing them with a digit:
        if exists(new_fullpath):
            _path, _ext = splitext(new_fullpath)
            index = 1
            _new_fullpath = '%s.%.5d%s' % (_path, index, _ext)
            while exists(_new_fullpath):
                _path, _ext = splitext(new_fullpath)
                index += 1
                _new_fullpath = '%s.%.5d%s' % (_path, index, _ext)

            # Store our new path
            new_fullpath = _new_fullpath

        if self.mode == DIRWATCH_MODE.MOVE:
            # Move our file
            try:
                move(source_path, new_fullpath)
                self.logger.info('Moved FILE: %s (%s)' % (
                    source_path, basename(new_fullpath),
                ))

            except Exception, e:
                self.logger.error('Could not move FILE: %s (%s)' % (
                    source_path, basename(new_fullpath),
                ))
                self.logger.debug('Move Exception %s' % str(e))
                return False

        else:
            self.logger.info('PREVIEW ONLY: Handle FILE: %s (%s)' % (
                source_path, basename(new_fullpath),
            ))

        return True

    def watch_library(self, sources, target_dir, *args, **kwargs):
        """
          Recursively scan source directories specified for NZB-Files
          and move found entries to the target directory

        """
        # Target Directory
        target_dir = abspath(expanduser(target_dir))
        if not isdir(target_dir):
            # We're done if the target path isn't a directory
            self.logger.error(
                'Target directory %s was not found.' % target_dir)
            return False

        self.logger.info('Target directory set to: %s' % target_dir)

        # Create a reference time
        ref_time = datetime.now() - timedelta(seconds=self.min_age)

        for _path in sources:
            # Get our absolute path
            path = abspath(expanduser(_path))

            if not isdir(path):
                # We're done if the target path isn't a directory
                self.logger.warning(
                    'Source directory %s was not found.' % path)
                continue

            if path == target_dir:
                # We're done if the target path isn't a directory
                self.logger.warning(
                    'Source and Target directory (%s) are the same.' % path)
                continue

            regex_filter=[ NZB_FILE_RE, ]
            if self.max_archive_size > 0:
                # Add ZIP Files into our mix
                regex_filter.append(ZIP_FILE_RE)

            # Scan our directory (but not recursively)
            possible_matches = self.get_files(
                path,
                regex_filter=regex_filter,
                min_depth=1, max_depth=1,
                fullstats=True,
                skip_directories=True,
            )

            # Filter our files that are too new
            filtered_matches = dict(
                [ (k, v) for (k, v) in possible_matches.iteritems() \
                 if v['modified'] < ref_time ])

            # Do our compression check as a second step since it's
            # possible to disable it
            if self.max_archive_size > 0:
                zip_files = [ f for (f, m) in filtered_matches.iteritems() \
                             if ZIP_FILE_RE.match(f) is not None and \
                             m['filesize'] > 0 and \
                             (m['filesize']/1000) < self.max_archive_size ]

                for zfile in zip_files:
                    # Iterate over each zip file and peak inside it
                    z_contents = None
                    try:
                        zp = ZipFile(zfile, mode='r')
                        z_contents = zp.namelist()

                    except Exception, e:
                        self.logger.error('Could not peek in ZIP: %s' % zfile)
                        self.logger.debug('Peek Exception %s' % str(e))
                        # pop file from our move list
                        del filtered_matches[zfile]
                        continue

                    # Let's have a look at our contents to see if there is a
                    # non-NZB-File entry
                    is_nzb_only = next((False for i in z_contents \
                                             if NZB_FILE_RE.match(i) is None), True)
                    if not is_nzb_only:
                        self.logger.debug(
                            'ZIP %s: contains non NZB-Files within it.' % (
                            zfile,
                        ) + ' Skipping')

                        # pop file from our move list
                        del filtered_matches[zfile]
                        continue

                    self.logger.debug('ZIP %s: contains NZB-Files.' % zfile)

            if len(filtered_matches) <= 0:
                self.logger.debug(
                    'No NZB-Files found in directory %s. Skipping' % path,
                )
                continue

            for fullpath in filtered_matches.iterkeys():
                # want to avoid destroying something we shouldn't
                self._handle(fullpath, target_dir)

        return True


    def watch(self):
        """All of the core cleanup magic happens here.
        """

        if not self.validate(keys=(
            'WatchPaths',
            'NzbDir',
            )):

            return False

        # Store our variables
        self.max_archive_size = int(
            self.get('MaxArchiveSizeKB', self.max_archive_size))

        self.min_age = int(self.get('ProcessMinAge', self.min_age))

        # Store our source paths
        source_paths = self.parse_path_list(self.get('WatchPaths'))

        # Store target directory
        target_path = tidy_path(self.get('NzbDir'))
        self.mode = script.get('Mode', DIRWATCH_MODE_DEFAULT)
        if not isdir(target_path):
            self.logger.error(
                "The target directory '%s' was not found." % \
                target_path,
            )
            return False

        return self.watch_library(
            source_paths,
            target_path,
        )

    def scheduler_main(self, *args, **kwargs):
        """Scheduler
        """

        return self.watch()

    def main(self, *args, **kwargs):
        """CLI
        """
        return self.watch()


# Call your script as follows:
if __name__ == "__main__":
    from sys import exit
    from optparse import OptionParser

    # Support running from the command line
    usage = "Usage: %prog [options] -t TargetDir [SrcDir1 [SrcDir2 [...]]]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-t",
        "--target-dir",
        dest="target_dir",
        help="The directory you want to move found NZB-Files from the " +\
             "identified source directories to.",
        metavar="DIR",
    )
    parser.add_option(
        "-a",
        "--min-age",
        dest="min_age",
        help="Specify the minimum age a NZB-File must be " +\
        "before considering it for processing. This value " +\
        "is interpreted in seconds and defaults to %d sec(s). " % \
        (DEFAULT_MATCH_MINAGE) + "This is just a safety switch to " +\
        "prevent us from creating a racing condition where an " +\
        "NZB-File is still being written to disk at the same time "\
        "as we're trying to process it.",
        metavar="AGE_IN_SEC",
    )
    parser.add_option(
        "-s",
        "--max-archive-size",
        dest="max_archive_size",
        help="Specify the maximum size a detected compressed file can be " +\
        "before ignoring it. If the found compressed file is within this " +\
        "specified value, it's contents will be scanned to see if it " +\
        "(only) contains NZB-Files. These types of files would qualify " +\
        "to be moved as well. Set this value to Zero (0) to not process " +\
        "compressed files. The value is interpreted in Kilobytes and has " +\
        "a default value of %s" % (DEFAULT_COMPRESSED_MAXSIZE_KB) +\
        "if not otherwise specified.",
        metavar="SIZE_IN_KB",
    )
    parser.add_option(
        "-p",
        "--preview",
        dest="preview_only",
        action="store_true",
        help="This is like a test switch; the actions the script would " +\
        "have otherwise performed are instead just printed to the screen."
    )
    parser.add_option(
        "-L",
        "--logfile",
        dest="logfile",
        help="Send output to the specified logfile instead of stdout.",
        metavar="FILE",
    )
    parser.add_option(
        "-D",
        "--debug",
        action="store_true",
        dest="debug",
        help="Debug Mode",
    )
    options, _args = parser.parse_args()

    logger = options.logfile
    if not logger:
        # True = stdout
        logger = True
    debug = options.debug

    _watch_paths = None
    if len(_args):
        # Support command line arguments too
        _watch_paths = ', '.join(_args)

    # We always enter this part of the code, so we have to be
    # careful to only set() values that have been set by an
    # external switch. Otherwise we use defaults or what might
    # already be resident in memory (environment variables).
    _min_age = options.min_age
    _max_archive_size = options.max_archive_size
    _preview = options.preview_only is True
    _target_dir = options.target_dir

    # Default Script Mode
    script_mode = None

    if _preview or _watch_paths or _target_dir:
        # By specifying one of the followings; we know for sure that the
        # user is running this script manually from the command line.
        # is running this as a standalone script,

        # Setting Script Mode to NONE forces main() to execute
        # which is where the code for the cli() is defined
        script_mode = SCRIPT_MODE.NONE

    script = DirWatchScript(
        logger=logger,
        debug=debug,
        script_mode=script_mode,
    )

    if _watch_paths:
        # Default mode to Move
        script.set('Mode', DIRWATCH_MODE.MOVE)

        # Set our Watch paths
        script.set('WatchPaths', _watch_paths)

    if _preview:
        # Toggle Preview Mode
        script.set('Mode', DIRWATCH_MODE.PREVIEW)

    if _max_archive_size:
        try:
            _max_archive_size = str(abs(int(_max_archive_size)))
            script.set('MaxArchiveSizeKB', _max_archive_size)

        except (ValueError, TypeError):
            script.logger.error(
                'An invalid `max_archive_size` (%s) was specified.' % (_max_archive_size)
            )
            exit(EXIT_CODE.FAILURE)

    if _min_age:
        try:
            _min_age = str(abs(int(_min_age)))
            script.set('ProcessMinAge', _min_age)

        except (ValueError, TypeError):
            script.logger.error(
                'An invalid `min_age` (%s) was specified.' % (_min_age)
            )
            exit(EXIT_CODE.FAILURE)

    if not script.get('NzbDir') and _target_dir:
        if not (_preview or _watch_paths):
            script.set('Mode', DIRWATCH_MODE_DEFAULT)

        if script.get('WatchPaths') is None:
            # Allow this flag to exist
            script.set('WatchPaths', '')

        # Finally set the directory the user specified for scanning
        script.set('NzbDir', _target_dir)

    if not script.script_mode and not script.get('NzbDir'):
        # Provide some CLI help when NzbDir has been
        # detected as not being identified
        parser.print_help()
        exit(1)

    # call run() and exit() using it's returned value
    exit(script.run())
