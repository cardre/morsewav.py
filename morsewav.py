#! /usr/bin/env python

# Morse code wav file generator
# =============================
# - By Cary Dreelan VK5CD
# - GNU GPL Licensed
# - Based on version at http://svn.python.org/projects/python/trunk/Demo/scripts/morse.py
# - Improvements:
#    - Adding key click filter (ramp amplitude up/down)
#    - More command line options:
#      - Specify sample rate
#      - Frequency of morse signal
#      - Amplitude of signal
#      - Words per minute
#      - Letter spacing as percentage (allowing Farnsworth style)
#    - Cached sinusodial waves for faster performance

# Run command using the following options:
# -o outfile		# name/path of file to create
# -f morse_freq_hz	# Frequency in hz of tones to generate, default 850 Hz
# -s sample_rate 	# of wav file, default 22050 Hz
# -w words_per_minute # default is 25 wpm
# -a amplitude 		# 0 (silence) to 32767 (loudest), default 30000
# -l letter spacing % # Default is 100%, increase for Farnsworth style
# -v verbose		# Output details about what is to be generated, including morse representation
# [ words ]			# Actual words to be converted, either as cmd line options, or can be stdin

# Examples
# 
# Generate 'hello_world.wav' test file with default parameters in current directory:
#	./morsewav.py -o hello_world.wav hello world
#
# Convert a book text file into a morse wav file with additional letter spacing (Farnsworth)
#	cat book.txt | ./morsewav.py -o book.wav -l 200

# -- Morse code rules --
# DAH should be three DOTs.
# Space between DOTs and DAHs should be one DOT.
# Space between two letters should be one DAH.
# Space between two words should be DOT DAH DAH.

# -- Words per minute conversion --
# Sending the word PARIS is standard way of determining morse words per minute
# PARIS in morse contains 50 elements with a dit/dot taking one element
# morse_wpm = 60 (seconds) / ( dot_msecs * 50 (elements) / 1000 msecs )
# dot_msecs = 60 (seconds) * 1000 msecs / ( morse_wpm * 50 (elements) ) 
# or simplified
#  T = 1200 / W

import sys, math, audiodev

# Default constants
DEF_SAMPLE_RATE = 22050
DEF_MORSE_FREQ = 850.0 # Hz
DEF_AMPLITUDE = 30000 # 0-32767
DEF_WORDS_PER_MIN = 25
DEF_LETTER_SPACING = 100 # Percent

# How many samples to spend ramping up or down
RAMP_SAMPLE_PERCENT = .075 # = 7.5%

# Globals
global morse_freq_hz
global sample_rate
global amplitude
global words_per_min
global letter_spacing
global verbose

morsetab = {
		'A': '.-',				'a': '.-',
		'B': '-...',			'b': '-...',
		'C': '-.-.',			'c': '-.-.',
		'D': '-..',				'd': '-..',
		'E': '.',				'e': '.',
		'F': '..-.',			'f': '..-.',
		'G': '--.',				'g': '--.',
		'H': '....',			'h': '....',
		'I': '..',				'i': '..',
		'J': '.---',			'j': '.---',
		'K': '-.-',				'k': '-.-',
		'L': '.-..',			'l': '.-..',
		'M': '--',				'm': '--',
		'N': '-.',				'n': '-.',
		'O': '---',				'o': '---',
		'P': '.--.',			'p': '.--.',
		'Q': '--.-',			'q': '--.-',
		'R': '.-.',				'r': '.-.',
		'S': '...',				's': '...',
		'T': '-',				't': '-',
		'U': '..-',				'u': '..-',
		'V': '...-',			'v': '...-',
		'W': '.--',				'w': '.--',
		'X': '-..-',			'x': '-..-',
		'Y': '-.--',			'y': '-.--',
		'Z': '--..',			'z': '--..',
		'0': '-----',			',': '--..--',
		'1': '.----',			'.': '.-.-.-',
		'2': '..---',			'?': '..--..',
		'3': '...--',			';': '-.-.-.',
		'4': '....-',			':': '---...',
		'5': '.....',			"'": '.----.',
		'6': '-....',			'-': '-....-',
		'7': '--...',			'/': '-..-.',
		'8': '---..',			'(': '-.--.-',
		'9': '----.',			')': '-.--.-',
		' ': ' ',				'_': '..--.-',
}

def main():
	import getopt
	global verbose

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'o:f:s:w:a:l:v')
	except getopt.error:
		sys.stderr.write('Usage ' + sys.argv[0] +
			' [-o outfile] [-f morse_freq_hz] [-s sample_rate] [-w words_per_minute] [-a amplitude (0-32767)] [-l letter spacing % (100+)] [-v verbose] [ words ] ...\n')
		sys.exit(1)

	dev = None
	morse_freq_hz = DEF_MORSE_FREQ
	sample_rate = DEF_SAMPLE_RATE
	amplitude = DEF_AMPLITUDE
	words_per_min = DEF_WORDS_PER_MIN
	letter_spacing = DEF_LETTER_SPACING
	verbose = False

	# Check cmd line options
	for o, a in opts:
		if o == '-o':
			# Wav file little endian
			import wave as filewave
			dev = filewave.open(a, 'w')
		if o == '-f':
			morse_freq_hz = float(a)
		if o == '-s':
			sample_rate = int(a)
		if o == '-w':
			words_per_min = int(a)
		if o == '-a':
			amplitude = int(a)
		if o == '-l':
			letter_spacing = int(a)
		if o == '-v':
			verbose = True

	if verbose:
		print "File =", dev
		print "morse_freq_hz =", morse_freq_hz
		print "sample_rate =", sample_rate
		print "amplitude =", amplitude
		print "words_per_min =", words_per_min
		print "letter_spacing =", letter_spacing

	# If no device specified, try open audio device (on Linux, won't work on Mac/Win?)
	if not dev:
		import audiodev
		dev = audiodev.AudioDev()
		dev.setoutrate(sample_rate)
		dev.setsampwidth(2)
		dev.setnchannels(1)
		dev.close = dev.stop
		dev.writeframesraw = dev.writeframes

	# Get the words to be converted either from command line or stdin
	if args:
		source = [' '.join(args)]
	else:
		source = iter(sys.stdin.readline, '')

	# Set file/dev sample rate & parameters
	dev.setparams((1, 2, sample_rate, 0, 'NONE', 'not compressed'))

	# Calculate speed of morse based on WPM (Dot Time = 1200 / WPM)
	dot_msecs =  1200 / words_per_min # Time in msecs a dot should take (25 wpm = 48 msecs)
	dot_samples = int( float(dot_msecs) / 1000 * sample_rate )
	dah_samples = 3 * dot_samples

	if verbose:
		print "dot_msecs =", dot_msecs
		print "dot_samples =", dot_samples
		print "dah_samples =", dah_samples
		
	# CD - add space in front (time for squelch to open?) of 0.5s
	pause(dev, sample_rate / 2)
	
	# Play out morse
	for line in source:
		mline, vmline = morse(line)
		if verbose:
			print vmline
		play(mline, dev, morse_freq_hz, amplitude, sample_rate, dot_samples, dah_samples, letter_spacing)
		if hasattr(dev, 'wait'):
			dev.wait()
	dev.close()

# Convert a string to morse code with \001 between the characters in the string.
def morse(line):
	vres = res = ''
	for c in line:
		try:
			res += morsetab[c] + '\001'
			vres += morsetab[c] + ' '
		except KeyError:
			pass
	return res, vres

# Play a line of morse code.
def play(line, dev, morse_freq_hz, amplitude, sample_rate, dot_samples, dah_samples, letter_spacing):
	ramp_samples = int( dot_samples * RAMP_SAMPLE_PERCENT )
	dot_bytes = sinusodial(dev, morse_freq_hz, amplitude, sample_rate, dot_samples, ramp_samples)
	dah_bytes = sinusodial(dev, morse_freq_hz, amplitude, sample_rate, dah_samples, ramp_samples)
	for c in line:
		if c == '.':
			dev.writeframesraw( dot_bytes )
		elif c == '-':
			dev.writeframesraw( dah_bytes )
		else:					# space
			pause(dev, int ( ( dah_samples + dot_samples ) * letter_spacing / 100 ) )
		pause(dev, dot_samples)

def sinusodial(dev, morse_freq_hz, amplitude, sample_rate, length, ramp_samples):
	
	# Add in ramp up/down of sinusodial wave to avoid clicks
	# This also means using cos instead of sine to allow smother ramping start/stop points

	res = ''
	sample = 0

	# Calculate the amount we need to increase pi for each sample
	radian_inc = 2 * math.pi * morse_freq_hz 
	
	# Ramp up
	for i in range(ramp_samples):
		val = int(math.cos(radian_inc * sample / sample_rate ) * amplitude * i / ramp_samples )
		res += chr(val & 255) + chr((val >> 8) & 255)
		sample += 1

	# Full amplitude
	for i in range(length - ramp_samples * 2):
		val = int(math.cos(radian_inc * sample / sample_rate ) * amplitude )
		res += chr(val & 255) + chr((val >> 8) & 255)
		sample += 1

	# Ramp down
	for i in range(ramp_samples):
		val = int(math.cos(radian_inc * sample / sample_rate ) * amplitude * (ramp_samples - i) / ramp_samples )
		res += chr(val & 255) + chr((val >> 8) & 255) 
		sample += 1

	return res


def pause(dev, length):
	dev.writeframesraw('\0' * length * 2) # * 2 bytes p/sample

if __name__ == '__main__':
	main()
