#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# DirWatch scan script for NZBGet to move nzb files detected elsewhere
# into NZBGet's file queue for processing.
#
# Copyright (C) 2017 Chris Caron <lead2gold@gmail.com>
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
### TASK TIME: *                                                           ###
##############################################################################
##############################################################################
### NZBGET SCHEDULER SCRIPT                                                ###

# The script searches the paths you tell it to for NZB-Files.  If one is found
# it is moved automatically for into the NZBGet incoming path for downloading.
#
# Info about this DirWatch NZB Script:
# Author: Chris Caron (lead2gold@gmail.com).
# Date: Sun, Feb 19th, 2017.
# License: GPLv3 (http://www.gnu.org/licenses/gpl.html).
# Script Version: 0.2.0
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
# You can additionally specify options too such as:
#   - c=category
#
# Options are specified at the end of the path name like one would do for
# a URL. For example, one might specify the following to always load content
# from a specific path and treat the NZBs found as books:
#    /path/to/book/dir?c=books
#
#WatchPaths=~/Downloads, ~/Dropbox/NZB-Files

# Maximum Archive Size in Kilobytes.
#
# If we find a Zip file within one of our WatchPath's (defined above), then we
# verify that it is no larger then this value (in Kilobytes). This is to
# prevent processing excessively large compressed files that in no way would
# have ever had an NZB-File in them anyway.
#
#MaxArchiveSizeKB=150

# Scan Cycles.
#
# Specify the number of seconds you wish to poll the specified watch paths
# for content. Set this to zero to just use the times defined by the
# NZBGet Scheduler instead. By setting this to any value larger then 0
# (but no less then 30), The script will run indefinitely (or until
# NZB-Get is shutdown)
#
#PollTimeSec=60

# DirWatch TempFile Auto-Cleanup (yes, no).
#
# This script renames NZB-Files (even the ZIPs that contain them) with
# a .dw extension just prior to handling them.  This is a failsafe
# way of not processing it a second time around.  Once these files have
# been handled, this script attempts to remove them automatically.
#
# However... there are cases where file permissions allow for the initial
# rename (to .dw) to occur, but do not allow the auto-cleanup afterwards.
#
# By setting this flag to Yes, you're allowing the script to attempt to
# remove any lingering .dw files still residing in the DirWatch directories
# if they're found under the presumption they've been handled already.
#
#AutoCleanup=No

# Enable debug logging (yes, no).
#
# If you experience a problem, you can bet the developer of this script will
# have a much easier time troubleshootng it for you if your logs include
# debugging.  Debugging is made possible by flipping this flag here.
#
#Debug=no

# Issue a tidy of any directories you defined above here:
#NZBScan@Scan Defined NZB Paths

### NZBGET SCHEDULER SCRIPT                                                ###
##############################################################################

import re
from os import unlink
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
from shutil import copy
from zipfile import ZipFile
from time import sleep
try:
    # Python 2.7
    from urlparse import parse_qsl

except ImportError:
    from urllib.parse import parse_qsl

# This is required if the below environment variables
# are not included in your environment already
import sys

# Script dependencies identified below
from datetime import timedelta
from datetime import datetime

# pynzbget Script Wrappers
from nzbget import SchedulerScript
from nzbget import EXIT_CODE
from nzbget import SCRIPT_MODE
from nzbget.Utils import tidy_path

# Stick an extension on files prior to handling them.  This prevents
# them from being detected later, and we can also grasp a handle
# of what our disk access permissions are because if we can't even
# rename the file, then we shouldn't be handling it it.
HANDLING_EXTENSION = ".dw"

# Match paths (path can't have a question makr in it though)
ARG_EXTRACT_RE = re.compile('^(?P<path>[^?]+)(\?(?P<args>.*))?$')

# Regular expression for the handling of NZB-Files
STRICTLY_NZB_FILE_RE = re.compile(
    '^(?P<filename>.*)(?P<ext>\.nzb)$', re.IGNORECASE)

# A bit looser version of an NZB-File to which we account for our
# Handled/Ignore extension
NZB_FILE_RE = re.compile(
    '^(?P<filename>.*)(?P<ext>\.nzb)(?P<ignore>\.dw)?$', re.IGNORECASE)

# Regular expression for the handling of ZIP-Files
ZIP_FILE_RE = re.compile(
    '^(?P<filename>.*)(?P<ext>\.zip)(?P<ignore>\.dw)?$', re.IGNORECASE)

# Ignore Regular Expression
IGNORE_FILE_RE = re.compile(
    '^(?P<filename>.*)(?P<ignore>\.dw)$', re.IGNORECASE)

# The number of seconds a matched directory/file has to have aged before it
# is processed further.  This prevents the script from removing content
# that may being processed 'now'.  All content must be older than this
# to be considered. This value is represented in seconds.
DEFAULT_MATCH_MINAGE = 30

# The default setting for Auto Cleanup
DEFAULT_AUTO_CLEANUP = False

# The maximum size a compressed file can be before it is considered to
# be looked within for NZB-Files
DEFAULT_COMPRESSED_MAXSIZE_KB = 150

# The default polling time for the directory watch script
DEFAULT_POLL_TIME_SEC = 60

# The minimum allowable setting the poll time can be
MINIMUM_POLL_TIME_SEC = 30

# Keyword that triggers the auto-detection of the category based
# on what is parsed from the NZB-File (and or filename)
AUTO_DETECT_CATEGORY_KEY = '*'

class DIRWATCH_MODE(object):
    # Move content to the path specified instead of deleting it
    MOVE = "Move"
    # Do nothing; just preview what was intended to be tidied
    PREVIEW = "Preview"
    # Do nothing; just preview what was intended to be tidied
    REMOTE = "Remote Push"

# TidyIt Modes
DIRWATCH_MODES = (
    DIRWATCH_MODE.PREVIEW,
    DIRWATCH_MODE.MOVE,
    DIRWATCH_MODE.REMOTE,
)

# Default in a Read-Only Mode; It's the safest way!
DIRWATCH_MODE_DEFAULT = DIRWATCH_MODE.PREVIEW

# Allow different combinations of the category keyword when
# specifying it on the command line
CATEGORY_KEYWORDS = ('c', 'cat', 'category')


class DirWatchScript(SchedulerScript):
    """A Script for NZBGet to allow one to monitor multiple locations that
    may potentially contain an NZB-File.

    If a file is found, it's contents are automatically moved into the
    NZBGet queue for processing.
    """

    # Our default polling time in seconds; set this to zero to disable
    # poll checks.
    poll_time_sec = DEFAULT_POLL_TIME_SEC

    # Define our minimum age a file can be
    min_age = DEFAULT_MATCH_MINAGE

    # Define our maxium archive size a compressed file can be
    max_archive_size = DEFAULT_COMPRESSED_MAXSIZE_KB

    def remote_push(self, source_path, category=None):
        """
        Processes the specified source path and handles remote api
        calls to NZBGet. If category is set to None, then it is auto-detected
        (if possible) by reading it from the Meta entries within the NZB-Files
        """

        # If we reach here, we have some extra processing to do before
        # we pass the data right into NZBGet via its API
        result = ZIP_FILE_RE.match(basename(source_path))
        if result:
            try:
                zp = ZipFile(source_path, mode='r')
                z_contents = zp.namelist()

            except Exception as e:
                self.logger.warning(
                    'Could not access Zipped NZB-File %s%s.' % (
                        result.group('filename'),
                        result.group('ext'),
                    ))
                self.logger.debug('ZIP Exception %s' % str(e))
                return False

            # Iterate over our zip files
            for znzb in z_contents:
                # We search exclusively for .nzb files
                if STRICTLY_NZB_FILE_RE.match(znzb):
                    continue

                # Read our content back
                if not self.add_nzb(basename(znzb),
                                    content=zp.read(znzb),
                                    category=category):

                    self.logger.warning(
                        'Failed to push Compressed NZB-File content '
                        '%s%s to NZBGet (category=%s)' % (
                            result.group('filename'),
                            result.group('ext'),
                            category,
                        ))

        # Load our content directly via it's file
        elif not self.add_nzb(source_path, category=category):
            self.logger.warning(
                'Failed to load NZB-File %s%s' % (
                basename(source_path),
                ((category) and ", category='%s'" % category or ""),
            ))
            return False

        self.logger.info('Loaded NZB-File: %s%s' % (
            basename(source_path),
            ((category) and ", category='%s'" % category or ""),
        ))

        return True

    def local_push(self, source_path, target_dir, target_file=None):
        """
        A Simple wrapper to handle content in addition to logging it.
        """

        if not target_dir:
            return False

        if not isdir(target_dir):
            self.logger.error(
                "The target directory '%s' was not found (for handling)." % \
                target_dir,
            )
            return False

        if not isfile(source_path):
            self.logger.warning(
                "The source file '%s' was not found (for handling)." % \
                source_path,
            )
            return False

        if target_file is None:
            target_file = basename(source_path)

        self.logger.info('Scanning Source: %s' % target_file)

        # Generate the new filename
        new_fullpath = join(
            target_dir,
            target_file,
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
            if self.cleanup:
                _handle = move
            else:
                _handle = copy

            # Handle our file
            try:
                _handle(source_path, new_fullpath)
                self.logger.info('Handled FILE: %s (%s)' % (
                    join(dirname(source_path), target_file),
                    basename(new_fullpath),
                ))

            except Exception as e:
                self.logger.error('Could not handle FILE: %s (%s)' % (
                    join(dirname(source_path), target_file),
                    basename(new_fullpath),
                ))
                self.logger.debug('Handle Exception %s' % str(e))
                return False

        return True

    def watch_library(self, sources, target_dir, *args, **kwargs):
        """
          Recursively scan source directories specified for NZB-Files
          and move found entries to the target directory

        """
        if target_dir is not None:
            # Target Directory exists (we're not doing remote pushes)
            target_dir = abspath(expanduser(target_dir))
            if not isdir(target_dir):
                # We're done if the target path isn't a directory
                self.logger.error(
                    'Target directory %s was not found.' % target_dir)
                return False
            self.logger.debug('Target directory set to: %s' % target_dir)

        # Create a reference time
        ref_time = datetime.now() - timedelta(seconds=self.min_age)

        for _path in sources:

            _parsed = ARG_EXTRACT_RE.match(_path)

            # create an argument map
            _args = {}

            if _parsed is None:
                # Could not math path; just use what we were passed in
                path = _path
            else:
                path = _parsed.group('path')
                try:
                    _args = dict([ (k.lower().strip(), v.strip()) \
                                      for k, v in parse_qsl(
                            _parsed.group('args'),
                            keep_blank_values=True,
                            strict_parsing=False,
                    )])

                except AttributeError:
                    # No problem; there simply wasn't anything to parse
                    pass

            # Get our absolute path
            path = abspath(expanduser(path))

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

            ignored_matches = dict(
                [ (k, v) for (k, v) in filtered_matches.iteritems() \
                 if IGNORE_FILE_RE.match(k) and \
                    IGNORE_FILE_RE.match(k).group('ignore') ])

            for ignored, _ in ignored_matches.iteritems():
                self.logger.debug('Ignoring file: %s' % ignored)
                if self.cleanup:
                    # file should not be handled as it already has
                    # been but still lingers; attempt to tidy:
                    try:
                        unlink(ignored)
                        self.logger.info('Auto-Cleanup removed %s' % ignored)

                    except Exception as e:
                        self.logger.warning(
                            'Auto-Cleanup failed to remove %s' % (
                                ignored,
                        ))
                        self.logger.debug('Auto-Cleanup Exception %s' % str(e))

                # Eliminate file from search
                del filtered_matches[ignored]

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

                    except Exception as e:
                        self.logger.error('Could not peek in ZIP: %s' % zfile)
                        self.logger.debug('ZIP Exception %s' % str(e))
                        # pop file from our move list
                        del filtered_matches[zfile]
                        continue

                    # Let's have a look at our contents to see if there is a
                    # non-NZB-File entry
                    is_nzb_only = next((False for i in z_contents \
                        if STRICTLY_NZB_FILE_RE.match(i) is None), True)
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
                    'No NZB-Files found in directory %s' % path,
                )
                continue

            category = next(( _args[k] \
                             for k in CATEGORY_KEYWORDS if k in _args), "")\
                            .strip()

            if category:
                if not self.api_connect():
                    self.logger.warning(
                        'A category was defined, but a connection to NZBGet '\
                        ' could not be established.')
                    continue

            for _fullpath in filtered_matches.iterkeys():
                # Iterate over each file and move it's content into the source
                # however, if a category was parsed, then we need to directly
                # connect to the NZBGet API and pass the NZB-File along bearing
                # the category we specified.  This gets a bit more tricky if
                # we're dealing with zip (compressed files).
                # We need to open these up and parse the content from within
                # them instead.
                if self.mode == DIRWATCH_MODE.PREVIEW:
                    self.logger.info('PREVIEW ONLY: Handle FILE: %s' % (
                        _fullpath,
                    ))
                    continue

                # Append our extension onto the file
                fullpath = _fullpath + HANDLING_EXTENSION

                # Move our file into a processing
                try:
                    move(_fullpath, fullpath)
                    self.logger.debug('Prepared FILE: %s (%s)' % (
                        _fullpath, basename(fullpath),
                    ))

                except Exception as e:
                    self.logger.error('Could not prep FILE: %s (%s)' % (
                        _fullpath, basename(fullpath),
                    ))
                    self.logger.debug('Prep Exception %s' % str(e))
                    continue

                if not category and self.mode != DIRWATCH_MODE.REMOTE:
                    # move/preview our content
                    if not self.local_push(fullpath, target_dir, basename(_fullpath)):
                        try:
                            move(fullpath, _fullpath)
                            self.logger.debug('Reverted FILE: %s (%s)' % (
                                fullpath, basename(_fullpath),
                            ))

                        except Exception as e:
                            self.logger.error('Could not revert FILE: %s (%s)' % (
                                fullpath, basename(_fullpath),
                            ))
                            self.logger.debug('Revert Exception %s' % str(e))

                    continue

                # Wild card to detect category from the NZB-File and load it
                if category == AUTO_DETECT_CATEGORY_KEY:
                    category = None

                # Handle Remote Files
                if not self.remote_push(fullpath, category):
                    # Move our file back for processing later
                    try:
                        move(fullpath, _fullpath)
                        self.logger.debug('Reverted FILE: %s (%s)' % (
                            fullpath, basename(_fullpath),
                        ))

                    except Exception as e:
                        self.logger.error('Could not revert FILE: %s (%s)' % (
                            fullpath, basename(_fullpath),
                        ))
                        self.logger.debug('Revert Exception %s' % str(e))
                    continue

                if self.cleanup:
                    # We were successful and cleanup flag is set,
                    # therefore we unlink our (handled) content:
                    try:
                        unlink(fullpath)
                        self.logger.info('Auto-Cleanup removed %s' % fullpath)

                    except Exception as e:
                        self.logger.warning(
                            'Auto-Cleanup failed to remove %s' % (
                                fullpath,
                        ))

        return True


    def watch(self):
        """All of the core cleanup magic happens here.
        """

        if not self.validate(keys=(
            'WatchPaths',
            'AutoCleanup',
            'NzbDir',
            )):
            self.logger.error("Missing Environment Variables.")
            return False

        # Store our variables
        self.max_archive_size = int(
            self.get('MaxArchiveSizeKB', self.max_archive_size))

        self.min_age = int(self.get('ProcessMinAge', self.min_age))

        # Store our source paths
        source_paths = self.parse_path_list(self.get('WatchPaths'))

        # Get our Mode
        self.mode = self.get('Mode', DIRWATCH_MODE_DEFAULT)

        # Cleanup Flag set?
        self.cleanup = self.parse_bool(self.get('AutoCleanup', DEFAULT_AUTO_CLEANUP))

        if self.mode != DIRWATCH_MODE.REMOTE:
            # Store target directory
            target_path = tidy_path(self.get('NzbDir'))
            if not isdir(target_path):
                self.logger.error(
                    "The target directory '%s' was not found." % \
                    target_path,
                )
                return False
        else:
            target_path = None

        return self.watch_library(
            source_paths,
            target_path,
        )

    def scheduler_main(self, *args, **kwargs):
        """Scheduler
        """
        # We always use MOVE mode when the call comes from
        # NZBGet
        self.set('Mode', DIRWATCH_MODE.MOVE)
        self.get('PollTimeSec', DEFAULT_POLL_TIME_SEC)
        try:
            poll_time = abs(int(
                self.get('PollTimeSec', DEFAULT_POLL_TIME_SEC)))

        except (ValueError, TypeError):
            self.logger.warning(
                "The poll time specified was invalid; " +
                "Defaulting it to %ds." % DEFAULT_POLL_TIME_SEC)
            poll_time = DEFAULT_POLL_TIME_SEC

        if poll_time != 0 and poll_time < MINIMUM_POLL_TIME_SEC:
            self.logger.warning(
                "The poll time specified was to small; " +
                "Defaulting it to %ds." % MINIMUM_POLL_TIME_SEC)

        if poll_time == 0:
            self.logger.debug('Single Instance Mode')
            # run a single instance
            return self.watch()

        # If we reach here, we run indefinitely presuming we are not
        # already runnning elsewhere

        # Create our PID
        self.is_unique_instance()

        self.logger.debug('Parallel Instance Mode')

        # Run until we have to quit
        while self.is_unique_instance():
            # Infinit loop; we rely on a signal sent by
            # NZBGet to quit
            if self.watch() is False:
                # We're done if we have a problem
                return False

            self.logger.debug(
                "Next NZB-File Scan in %d seconds..." % poll_time,
            )
            sleep(poll_time)

    def action_nzbscan(self, *args, **kwargs):
        """
        Execute the NZBScan Test Action
        """
        # run a single instance
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
    usage = "Usage: %prog [options] [SrcDir1 [SrcDir2 [...]]]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-t",
        "--target-dir",
        dest="target_dir",
        help="The directory you want to move found NZB-Files from the " +\
             "identified source directories to. This option is required " +\
             "if not using the --remote (-r) switch.",
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
        "-u",
        "--api-url",
        dest="api_url",
        help="Specify the URL of the NZB-Get API server such as: "
        " nzbget://user:pass@control.nzbget.host (to access insecure "
        "port 6789), "
        " nzbgets://user:pass@control.nzbget.host (to access secure "
        "port 6791), "
        " nzbget://user:pass@control.nzbget.host:port (to specify your "
        "own insecure port), and"
        " nzbgets://user:pass@control.nzbget.host:port (to specify your "
        "own secure port).  By default nzbget://127.0.0.1 is used.",
        metavar="API_URL",
    )
    parser.add_option(
        "-r",
        "--remote-push",
        action="store_true",
        dest="remote",
        help="Perform a remote push to NZBGet. This allows you to scan "
        "directories for NZB-Files on different machines and still remotely "
        "push them to your central NZBGet server.",
    )
    parser.add_option(
        "-c",
        "--auto-cleanup",
        action="store_true",
        dest="auto_clean",
        help="Removes any .dw files detected prior to the handling of "
        "detected NZB-Files (and/or ZIP files containing them).",
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
    _api_url = options.api_url
    _remote = options.remote
    _auto_clean = options.auto_clean

    # Default Script Mode
    script_mode = None

    if _auto_clean or _remote or _api_url or _preview or _watch_paths \
            or _target_dir:
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

    if _api_url:
        # attempt to parse the URL specified and set the appropriate
        # system variables
        url = script.parse_url(_api_url)
        if url:
            if 'schema' in url and url['schema']:
                if url['schema'][-1] in ('s', 'S'):
                    script.set('SecureControl', 'True')
                else:
                    script.set('SecureControl', 'False')

            if 'host' in url and url['host']:
                script.set('ControlIP', url['host'])

            try:
                if 'port' in url and url['port']:
                    _port = str(abs(int(url['port'])))
                    script.set('SecurePort', _port)
                    script.set('ControlPort', _port)

            except (ValueError, TypeError):
                script.logger.error(
                    'An invalid port was specified in the `api url` '
                    '(%s).' % (url['port'])
                )
                exit(EXIT_CODE.FAILURE)

            if 'user' in url:
                if url['user']:
                    script.set('ControlUsername', url['user'])
                else:
                    script.set('ControlUsername', '')

            if 'password' in url:
                if url['password']:
                    script.set('ControlPassword', url['password'])
                else:
                    script.set('ControlPassword', '')

    if _watch_paths:
        # Default mode to Move
        script.set('Mode', DIRWATCH_MODE.MOVE)

        # Set our Watch paths
        script.set('WatchPaths', _watch_paths)

    if _preview:
        # Toggle Preview Mode
        script.set('Mode', DIRWATCH_MODE.PREVIEW)

    elif _remote:
        # Toggle Remote Mode
        script.set('Mode', DIRWATCH_MODE.REMOTE)

        # Ensure NzbDir is set
        script.set('NzbDir', '')

    if script.script_mode == SCRIPT_MODE.NONE:
        # AutoClean Handling
        if _auto_clean:
            script.set('AutoCleanup', 'Yes')
        else:
            script.set('AutoCleanup', 'No')

    if not _remote and not script.get('NzbDir') and _target_dir:
        if not (_preview or _watch_paths):
            script.set('Mode', DIRWATCH_MODE_DEFAULT)

        if script.get('WatchPaths') is None:
            # Allow this flag to exist
            script.set('WatchPaths', '')

        # Finally set the directory the user specified for scanning
        script.set('NzbDir', _target_dir)

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

    if not script.script_mode and not script.get('WatchPaths'):
        # Provide some CLI help when NzbDir has been
        # detected as not being identified
        parser.print_help()
        exit(1)

    # call run() and exit() using it's returned value
    exit(script.run())
