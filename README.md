morsewav.py
===========

A morse code wav file generator written in python by Cary Dreelan VK5CD

* GNU GPL Licensed
* Based on version at http://svn.python.org/projects/python/trunk/Demo/scripts/morse.py
* Improvements:
* Adding key click filter (ramp amplitude up/down)
* More command line options:
* - Specify sample rate
* - Frequency of morse signal
* - Amplitude of signal
* - Words per minute
* - Letter spacing as percentage (allowing Farnsworth style)
* Cached sinusodial waves for faster performance

Command line options
--------------------

* -o outfile # name/path of file to create
* -f morse_freq_hz # Frequency in hz of tones to generate, default 850 Hz
* -s sample_rate # of wav file, default 22050 Hz
* -w words_per_minute # default is 25 wpm
* -a amplitude # 0 (silence) to 32767 (loudest), default 30000
* -l letter spacing % # Default is 100%, increase for Farnsworth style
* -v verbose # Output details about what is to be generated, including morse representation
* [ words ] # Actual words to be converted, either as cmd line options, or can be stdin

Examples
--------

Generate 'hello_world.wav' test file with default parameters in current directory:

	./morsewav.py -o hello_world.wav hello world

Convert a book text file into a morse wav file with additional letter spacing (eg. Farnsworth style)

	cat book.txt | ./morsewav.py -o book.wav -l 200
