__Note:__ This script was intended to be an [NZBGet](http://nzbget.net) and _Scheduling_
script for _NZBGet_. However, it also works perfectly well as a standalone script for others too! It can be easily adapted to anyone's environment.
See the _Command Line_ section below for details how you can easily use this on it's own (without NZBGet).

DirWatch Scheduler Script
========================
DirWatch is a script that allows you to identify one or more directories it
should scan for NZB-Files in. When an NZB-File is found (or even a zip file
containing NZB-Files), it is moved to a new directory of your choice.

Why Would I Need This?
======================
NZBGet limits you to identifying _just one_ directory it should scan/watch for
NZB-Files in (for processing). This is okay for most people, but consider a
scenario where you have a DropBox share that you might want to put something in
from your phone, or at work.  Wouldn't it be great if NZBGet picked that up for
processing too!  Maybe there are multiple users on your network who want use
NZBGet too, rather then giving them your admin login (to NZBGet), you can just
scan a folder in their home directory (or on a network path) instead.

In short: This script allows you to process NZB-Get files that appear in multiple
directories instead of just the one.

How It Works
============
Whatever additional path you specify, the script will just move the detected NZB-Files
out of them and into the directory NZBGet already processes (identified by _NzbDir_ in
the Paths section of it's configuration). If you're calling this from the command line
then you must provide the _NzbDir_ as an argument. There are examples of this below.

Installation Instructions
=========================
1. Ensure you have at least Python v2.6 or higher installed onto your system.
2. Simply place the __DirWatch.py__ and __DirWatch__ directory together.
   * __NZBGet users__: you will want to place these inside of your _nzbget/scripts_ directory. Please ensure you are running _(at least)_ NZBGet v11.0 or higher. You can acquire the latest version of of it from [here](http://nzbget.net/download). <br/><br/>Create a __Schedule__; you can do this from inside NZBGet. From the __Settings__ -> __Scheduler__ section, you can choose to __[Add Task]__.

1. Ensure you have at least Python v2.6 or higher installed onto your system.
   * TaskX.Time:
      * Setting for NZBGet _Versions < v18_: __*:00,*:05,*:10,*:15,*:20,*:25,*:30,*:35,*:40,*:45,*:50,*:55__ <br/> This basically does a check every _5 minutes_ to see if the _DirWatch_ plugin is running. This means if you restart NZBGet or reload it's configuration for whatever reason; you'll just have to wait up to (a maximum of) 5 minutes before the script re-launches and takes over (using it's configured poll time).
      * Setting for NZBGet _Versions >= v18_: __*__<br/> A new feature allowing NZBGet to automatically start up any Scheduled service if you simply define a single asterix (__*__) as it's scheduled start time. So for this version an astrix is all you need.
   * TaskX.Weekdays: __1-7__
   * TaskX.Command: __Script__
   * TaskX.Param: __DirWatch.py__

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
# Scan every 2 minutes:
*/2 * * * * /path/to/DirWatch.py -t /path/to/NZBGet/NzbDir ~/DropBox
```
