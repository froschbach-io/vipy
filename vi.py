import argparse
import glob
import os
import subprocess
import signal
import time
from pid import PidFile
from datetime import datetime

parser = argparse.ArgumentParser(description='Play videos from a folder in a loop with omxplayer.')
parser.add_argument('-s', '--start', type=int, nargs='?', default=0, help='index at which to start')
parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
parser.add_argument('-p', '--pause', action='store_true', help='add pause between videos')
parser.add_argument('-d', '--dryrun', action='store_true', help='dry run mode (do not use omxplayer/tvservice)')
parser.add_argument('folder', help='folder with video files')

args = parser.parse_args()

extensions = ["MOV", "mov", "AVI", "avi", "MKV", "mkv"]
player = "omxplayer"
tvservice = "tvservice"
videos = []
start = args.start
cursor = 0
pidfname = "/tmp/vipy.pid"

if args.dryrun:
	player = "echo"
	tvservice = "echo"

reloadConfig = True
terminate = False

def handleHUP(signalNumber, frame):
	global reloadConfig
	print('Reloading config...')
	reloadConfig = True
	return

def handleTERM(signalNumber, frame):
	global terminate
	print('Terminating...')
	terminate = True
	return

signal.signal(signal.SIGHUP, handleHUP)
signal.signal(signal.SIGTERM, handleTERM)

def getIndex(fname):
	vindex = -1
	elements = fname.split('-')
	if len(elements) > 0:
		try:
			vindex = int(elements[0])
		except Exception:
			pass
	return vindex

# load video file names
def loadConfig():
	global videos, cursor
	videos = []
	cursor = 0
	for ext in extensions:
		videos.extend(glob.glob(args.folder + "/*." + ext))
	videos.sort()
	if len(videos) == 0:
		print("No videos found.")
		exit()

	# advance to start
	while cursor < len(videos):
		video = videos[cursor]
		fname = os.path.basename(video)
		vindex = getIndex(fname)
		if vindex >= start or vindex < 0:
			break
		cursor = (cursor + 1)
	if cursor >= len(videos):
		cursor = 0

# infinite loop
def mainLoop():
	global cursor, start, reloadConfig, terminate
	while True:
		video = videos[cursor]
		fname = os.path.basename(video)
		cmd = [player, video, "-n", "-1", "--blank"]

		subtitle = None
		try:
			fbase = os.path.splitext(video)[0]
			if os.path.isfile(fbase + ".srt"):
				subtitle = fbase + ".srt"
			elif os.path.isfile(fbase + ".SRT"):
				subtitle = fbase + ".SRT"
		except Exception:
			pass
		if not subtitle is None:
			cmd.append("--subtitle")
			cmd.append(subtitle)
		
		now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print("--", now, "Playing", fname)
		result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
		if result.returncode != 0 or args.verbose:
			print(str(result.stdout))

		if args.pause:
			time.sleep(1)

		if reloadConfig or terminate:
			start = getIndex(fname)+1
			break
		cursor = (cursor + 1) % len(videos)

if __name__ == '__main__':
	pid = os.getpid()
	print("--", "PID", pid)

	try:	
		with PidFile('vipy') as pidf:
			print("--", "PID File", pidf.piddir, pidf.pidname)
			print("--", "Switching tvservice on")
			result = subprocess.run([tvservice, "-p"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
			if result.returncode != 0 or args.verbose:
				print(str(result.stdout))

			# control loop
			while True:
				if reloadConfig:
					loadConfig()
					reloadConfig = False
				mainLoop()
				if terminate:
					break
			
			print("--", "Switching tvservice off")
			result = subprocess.run([tvservice, "-o"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
			if result.returncode != 0 or args.verbose:
				print(str(result.stdout))

	except Exception as e:
		print("ERROR", e)
