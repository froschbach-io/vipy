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

extensions = ["MOV", "mov", "MP4", "mp4", "AVI", "avi", "MKV", "mkv"]
player = "omxplayer"
viewer = "pngview"
tvservice = "tvservice"
videos = []
start = args.start
cursor = 0

if args.dryrun:
	player = "echo"
	tvservice = "echo"
	viewer = "echo"

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
		cmd = [player, video, "-n", "-1", "--layer", "1"]

		fbase = os.path.splitext(video)[0]

		subtitle = None
		try:
			if os.path.isfile(fbase + ".srt"):
				subtitle = fbase + ".srt"
			elif os.path.isfile(fbase + ".SRT"):
				subtitle = fbase + ".SRT"
		except Exception:
			pass
		if not subtitle is None:
			cmd.append("--subtitle")
			cmd.append(subtitle)
			cmd.append("--align")
			cmd.append("center")

		caption = None
		try:
			if os.path.isfile(fbase + ".png"):
				caption = fbase + ".png"
			elif os.path.isfile(fbase + ".PNG"):
				caption = fbase + ".PNG"
		except Exception:
			pass
		
		now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print("--", now, "Playing", fname)
		pomx = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')

		ppng = None
		if not caption is None:
			ppng = subprocess.Popen([viewer, "-b", "0", "-l", "2", "-x", "0", "-y", "0", caption], 
				stdout=None, stderr=subprocess.STDOUT, encoding='utf8')

		out = pomx.communicate()
		if not ppng is None:
			ppng.kill()
			ppng.communicate()

		if pomx.returncode != 0 or args.verbose:
			print(out)

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
		with PidFile(pidname='vipy', piddir='/tmp') as pidf:
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
