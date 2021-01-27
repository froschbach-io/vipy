# vi.py

Python script designed for a Raspberry Pi to play videos in a loop using omxplayer.
Supports
* subtitles
* headline/logo image (overlay image)
* switching HDMI signal on/off (using tvservice)
* SIGHUP to reload video folder
* SIGTERM for graceful termination

## Usage

```
$ python3 vi.py -h
usage: vi.py [-h] [-s [START]] [-v] [-p] [-d] folder

Play videos from a folder in a loop with omxplayer.

positional arguments:
  folder                folder with video files

optional arguments:
  -h, --help            show this help message and exit
  -s [START], --start [START]
                        index at which to start
  -v, --verbose         verbose output
  -p, --pause           add pause between videos
  -d, --dryrun          dry run mode (do not use omxplayer/tvservice)
```
