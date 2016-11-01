__Note:__ This script was intended to be an [NZBGet](http://nzbget.net) and _Scheduling_
script for _NZBGet_. However, it also works perfectly well as a standalone script for others too! It can be easily adapted to anyone's environment.
See the _Command Line_ section below for details how you can easily use this on it's own (without NZBGet).

DirWatch Scheduler Script
========================
DirWatch is a script designed to scan a set of directories that you
tell it to.  When an NZB-File becomes present in one of these folders it
is automatically moved to the NZBGet's download directory for processing.

Installation Instructions
=========================
1. Ensure you have at least Python v2.6 or higher installed onto your system.
2. Simply place the __DirWatch.py__ and __DirWatch__ directory together.
   * __NZBGet users__: you will want to place these inside of your _nzbget/scripts_ directory. Please ensure you are running _(at least)_ NZBGet v11.0 or higher. You can acquire the latest version of of it from [here](http://nzbget.net/download).

The Non-NZBGet users can also use this script via a cron (or simply call it
from the command line) to automatically poll directories for the latest
subtitles for the video content within it. See the __Command Line__ section
below for more instructions on how to do this.

**Note:** The _DirWatch_ directory provides all of the nessisary dependencies
in order for this script to work correctly. The directory is only required
if you do not have the packages already available to your global
environment. These dependant packages are all identified under the
_Dependencies_ section below.

Dependencies
============
The following dependencies are already provided for you within the
_DirWatch_ directory and no further effort is required by you. However, it
should be known that DirWatch.py depends on the following packages:

| Name                         | Version | Source                                                                               |
| ---------------------------- |:------- |:------------------------------------------------------------------------------------ |
| pynzbget                     | 0.2.3   | https://pypi.python.org/pypi/pynzbget/0.2.3                                          |

Command Line
============
DirWatch.py has a built in command line interface that can be easily tied
to a cron entry or can be easilly called from the command line to automate
the fetching of subtitles.

Here are the switches available to you:
```
Usage: DirWatch.py [options] -t TargetDir [scandir1 [scandir2 [...]]]

  -h, --help            show this help message and exit
  -t DIR, --target-dir=DIR
                        The directory you want to move found NZB-Files from
                        the identified source directories to.
  -a AGE_IN_SEC, --min-age=AGE_IN_SEC
                        Specify the minimum age a NZB-File must be before
                        considering it for processing. This value is
                        interpreted in seconds and defaults to 30 sec(s). This
                        is just a safety switch to prevent us from creating a
                        racing condition where an NZB-File is still being
                        written to disk at the same time as we're trying to
                        process it.
  -p, --preview         This is like a test switch; the actions the script
                        would have otherwise performed are instead just
                        printed to the screen.
  -L FILE, --logfile=FILE
                        Send output to the specified logfile instead of
                        stdout.
  -D, --debug           Debug Mode

```

Here is a simple example:
```bash
# Scan your library for NZB-Files and print to the sreen what
# you plan on doing (observe the -p switch):
python DirWatch.py -p -t /path/to/NZBGet/NzbDir 
	/path/to/location/with/NZB-Files

# Happy with the plan of action? Just drop the -p switch and the
# matched NZB-Files will be moved:
python DirWatch.py -t /path/to/NZBGet/NzbDir 
	/path/to/location/with/NZB-Files

```

You can scan as many directories as you want to type inline on the shell:
```bash
# Scan your libraries for NZB-Files and move them
# into: /path/to/NZBGet/NzbDir
python DirWatch.py -t /path/to/NZBGet/NzbDir \
	/home/joe/Downloads \
	/home/jason/Downloads \
	/home/trevor/Downloads \
	/home/joe/Dropbox/NZBFiles \
	/home/jason/Dropbox/NZBFiles \
	/home/trevor/Dropbox/NZBFiles \
```

Don't forget that if you're using the CLI, you can take advantage of wildcards
supported by your shell:
```bash
# Take advantage of shell wildcards:
python DirWatch.py -t /path/to/NZBGet/NzbDir \
	/home/*/Downloads /home/*/Dropbox/NZBFiles
```

If the script behaves as you expect it should, you can schedule it as a cron
to frequently move matched NZB-Files found in the specified Source Directories
```bash
# $> crontab -e
0 0 * * * /path/to/DirWatch.py -t /path/to/NZBGet/NzbDir ~/DropBox
```
