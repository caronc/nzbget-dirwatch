__Note:__ This script was intended to work with [NZBGet](http://nzbget.net) as a  _Scheduling_ script. However, it also works perfectly well as a standalone script for others too! It can be easily adapted to anyone's environment.
See the _Command Line_ section below for details how you can easily use this on it's own (without NZBGet).

[![Paypal](http://repo.nuxref.com/pub/img/paypaldonate.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MHANV39UZNQ5E)
[![Patreon](http://repo.nuxref.com/pub/img/patreondonate.svg)](https://www.patreon.com/caronc)

DirWatch Scheduler Script
========================
DirWatch is a script that allows you to identify one or more directories it
should scan for NZB-Files in. When an NZB-File is found (or even a zip file
containing NZB-Files), it is pushed either locally or remotely (depending on
how it's configured) to a central NZBGet server.

It can also just perform basic moving for any NZB-Processing application (such
as SABnzbd.  It can be easily scripted to simply read NZB-Files from multiple
locations and place them into a central location.

Why Would I Need This?
======================
NZBGet limits you to identifying _just one_ directory it should scan/watch for
NZB-Files in (for processing). This is okay for most people, but consider a
scenario where...
- you have a DropBox share; you could easily download an NZB-File from your
  tablet/phone and copy into here.  Then just know that your NZBGet server
  back at home will processed automatically for you!
- Maybe there are multiple users on your network who each want use
  NZBGet too; rather then giving them your admin login (to NZBGet), you can
  just set this script up to scan a designated folder (in each of their home
  directories) and process everything found. Thus, there is no need to run
  multiple instances of NZBGet.
- Consider that you have a media server somewhere in your house but want to
  post NZB-Files to it manually whenever they appear in your laptops Download
  directory.<br/>No problem! This script can run on any machine and read from
  as many directories as you want! It can also remotely post whatever it finds
  (NZB related) to your central NZBGet server.

Directory to Category Assignments
=================================
With this script, you can control what categories to assign to what NZB-Files
you process. So not only can allow manage mulitple directories containing
NZB-Files, but you can associate whatever category you wish this way too!

This is done by simply adding the __?c=category.name__ to each directory you
wish to monitor. For example, consider a layout like this on your home server:
```bash
   /nzbroot/Movies/
   /nzbroot/TVShows/
   /nzbroot/MyEBooks/
```

Category assignments are mapped by directories, so in this case you might just
add the following to NZBGet (DirWatch) Script's configuration:
```bash
/nzbroot/Movies?c=movie, /nzbroot/TVShows?c=tv, /nzbroot/MyEBooks?c=ebooks
```

With respect to the example above, you would have just acomplished to following
mappings for NZBGet:

| Directory                         | NZBGet Category |
| --------------------------------- |:--------------- |
| /nzbroot/Movies/                  | movies          |
| /nzbroot/TVShows/                 | tv              |
| /nzbroot/MyEBooks/                | ebooks          |

Easy-Peasy Right?

How It Works
============
Whatever additional path you specify, the script will just move the detected NZB-Files
out of them and into the directory NZBGet already processes (identified by _NzbDir_ in
the Paths section of it's configuration). If you're calling this from the command line
then you must provide the _NzbDir_ as an argument. There are examples of this below.

Installation Instructions
=========================
1. Ensure you have at least Python v2.7 or higher installed onto your system.
```bash
# Pull in dependencies:
pip install -r requirements.txt
```
2. Simply place the __DirWatch.py__ into your NZBGet scripts directory.
   * __NZBGet users__: you will want to place these inside of your _nzbget/scripts_ directory. Please ensure you are running _(at least)_ NZBGet v11.0 or higher. You can acquire the latest version of of it from [here](http://nzbget.net/download). <br/><br/>Create a __Schedule__; you can do this from inside NZBGet. From the __Settings__ -> __Scheduler__ section, you can choose to __[Add Task]__.
3. Optionally set up an NZBGet Scheduled Task:
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

Command Line
============
DirWatch.py has a built in command line interface that can be easily tied
to a cron entry or can be easilly called from the command line to automate
the fetching of subtitles.

Here are the switches available to you:
```
Usage: DirWatch.py [options] [SrcDir1 [SrcDir2 [...]]]

Options:
  -h, --help            show this help message and exit
  -t DIR, --target-dir=DIR
                        The directory you want to move found NZB-Files from
                        the identified source directories to. This option is
                        required if not using the --remote (-r) switch.
  -a AGE_IN_SEC, --min-age=AGE_IN_SEC
                        Specify the minimum age a NZB-File must be before
                        considering it for processing. This value is
                        interpreted in seconds and defaults to 30 sec(s). This
                        is just a safety switch to prevent us from creating a
                        racing condition where an NZB-File is still being
                        written to disk at the same time as we're trying to
                        process it.
  -s SIZE_IN_KB, --max-archive-size=SIZE_IN_KB
                        Specify the maximum size a detected compressed file
                        can be before ignoring it. If the found compressed
                        file is within this specified value, it's contents
                        will be scanned to see if it (only) contains NZB-
                        Files. These types of files would qualify to be moved
                        as well. Set this value to Zero (0) to not process
                        compressed files. The value is interpreted in
                        Kilobytes and has a default value of 150if not
                        otherwise specified.
  -p, --preview         This is like a test switch; the actions the script
                        would have otherwise performed are instead just
                        printed to the screen.
  -L FILE, --logfile=FILE
                        Send output to the specified logfile instead of
                        stdout.
  -u API_URL, --api-url=API_URL
                        Specify the URL of the NZB-Get API server such as:
                        nzbget://user:pass@control.nzbget.host (to access
                        insecure port 6789),
                        nzbgets://user:pass@control.nzbget.host (to access
                        secure port 6791),
                        nzbget://user:pass@control.nzbget.host:port (to
                        specify your own insecure port), and
                        nzbgets://user:pass@control.nzbget.host:port (to
                        specify your own secure port).  By default
                        nzbget://127.0.0.1 is used.
  -r, --remote-push     Perform a remote push to NZBGet. This allows you to
                        scan directories for NZB-Files on different machines
                        and still remotely push them to your central NZBGet
                        server.
  -c, --auto-cleanup    Removes any .dw files detected prior to the handling
                        of detected NZB-Files (and/or ZIP files containing
                        them).
  -D, --debug           Debug Mode

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
	/home/trevor/Dropbox/NZBFiles
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

Consider different servers on your network each obtaining NZB-Files in different
locations, but you only have 1 NZBGet instance. Perhaps the NZBGet instance
is even on a different network.  No problem; you can scan multiple locations for
NZB-Files and then push them remotely to your NZBGet server:
```bash
# Scan your libraries for NZB-Files and move them
# into our remote location done by the --remote (-r) switch
python DirWatch.py -r -u nzbget://my.nzbget.host \
	/path/to/nzb-files \
	/another/path/to/nzb-files
```

You can also use the category switches with the command line to force category
assignments per directory:
```bash
# Assign categories per directory (optionally) if you wish:
python DirWatch.py -t /path/to/NZBGet/NzbDir \
	/home/joe/Downloads/NZBFiles/Movies?c=movie \
	/home/joe/Downloads/NZBFiles/Shows?c=tv
	/home/joe/Downloads/NZBFiles/General

# You can do this using remote calls too:
python DirWatch.py -r -u nzbget://my.nzbget.host \
	/home/joe/Downloads/NZBFiles/Movies?c=movie \
	/home/joe/Downloads/NZBFiles/Shows?c=tv
```
