import datetime
import sys

KEYMAP = {"BEADGCF": "Cb", "BEADGC": "Gb", "BEADG": "Db", "BEAD": "Ab", "BEA": "Eb", "BE": "Bb", "B": "F", "C": "C", "F": "G", "FC": "D", "FCG": "A", "FCGD": "E", "FCGDA": "B", "FCGDAE": "F#", "FCGDAEB": "C#"}
NOTES = ["C,,", "D,,", "E,,", "F,,", "G,,", "A,,", "B,,", "C,", "D,", "E,", "F,", "G,", "A,", "B,", "C", "D", "E", "F", "G", "A", "B", "c", "d", "e", "f", "g", "a", "b", "c'", "d'", "e'", "f'", "g'", "a'", "b'"]
SHIFTS = {"treble":20, "bass":8, "alto":14, "tenor":12}
ACCIDENTALS = {"x": "^^", "#": "^", "n": "=", "b": "_", "v": "__"}

SMALL = .000000001

UPPER = 0
LOWER = 1

def convertNote(nwc, clef):
	abc = ""
	if nwc == "z":
		return "z"
	start = 0
	if nwc[0] in ACCIDENTALS.keys():
		abc += ACCIDENTALS[nwc[0]]
		start += 1
	end = (nwc + "^").find("^")
	pos = int(nwc[start:end])
	abc += NOTES[pos + SHIFTS[clef]]
	return abc

def convertDuration(nwc):
	numerator = 1
	denominator = 1
	if nwc.startswith("Half"):
		denominator = 2
	th = nwc.find("th")
	if th > 0:
		denominator = int(nwc[0:th])
	if nwc.find(",Dotted") > 0:
		numerator = numerator * 3
		denominator = denominator * 2
	if nwc.find(",DblDotted") > 0:
		numerator = numerator * 7
		denominator = denominator * 4
	if nwc.find(",Triplet") > 0:
		return ((numerator/denominator) * (2/3), "/" + str(denominator))
	if nwc.find(",Grace") > 0:
		return (0, "")
	if numerator == 1 and denominator == 1:
		return (1,"")
	if numerator == 1:
		return (1/denominator, "/" + str(denominator))
	return (numerator/denominator, str(numerator) + "/" + str(denominator))

def clean_text(in_text):
	text = in_text
	text = text.replace(chr(13) + chr(10), chr(10))
	text = text.replace(chr(13), chr(10))
	text = text.replace(chr(173), "")
	text = text.replace(chr(232), "e")
	text = text.replace(chr(8211), "-")
	text = text.replace(chr(8217), "'")
	return text

def parse_meter(meter_str):
	norm = meter_str.replace(",",".").replace("+",".").replace("(",".").replace(")",".").replace(" ",".")
	#Common Meter
	if norm.find("CMD") >= 0:
		return [8,6,8,6,8,6,8,6,0]
	if norm.find("CM") >= 0:
		return [8,6,8,6]
	#Long Meter
	if norm.find("LMD") >= 0:
		return [8,8,8,8,8,8,8,8,0]
	if norm.find("LM") >= 0:
		return [8,8,8,8]
	#Short Meter
	if norm.find("SMD") >= 0:
		return [6,6,8,6,6,6,8,6,0]
	if norm.find("SM") >= 0:
		return [6,6,8,6]
	#Hallelujah Meter
	if norm.find("HM") >= 0:
		return [6,6,6,6,8,8]
	ints = []
	for s in norm.split("."):
		if len(s) > 0:
			if s[0].isdigit():
				i = int(s)
				if i >= 20:
					ints.append(int(s[0]))
					ints.append(i % 10)
				else:
					ints.append(i)
			if s == "D":
				size = len(ints)
				for i in range(size):
					ints.append(ints[i])
				ints.append(0)
	if len(ints) > 1:
		return ints
	return None

def meter_string(meter):
	meter_str = str(meter[0])
	size = len(meter)
	doubled = (meter[len(meter) - 1] == 0)
	if doubled:
		size = (size-1) >> 1
	for i in range(1,size):
		meter_str += ("," + str(meter[i]))
	if doubled:
		meter_str += " D"
	return meter_str

def convert(text, meter_str, rebeam):
	meter = None
	if meter_str is not None:
		meter = meter_str.replace("+",",").replace(".",",").split(",")
		for i in range(len(meter)):
			try:
				meter[i] = int(meter[i])
			except:
				print("Error with meter")

	lines = ("|Begin\n" + clean_text(text) + "\n|Done").split("\n")
	title = ""
	author = ""
	lyricist = ""
	terms = ""
	transcription = ""
	comments = ""
	timesig = None
	timesig_count = 0
	keysig = None
	keysig_count = 0
	tempo = None
	tempo_count = 0
	bpm = 4 # beats per measure
	beat_len = .25
	staves = 0
	longest_lyrics = ["",""]
	
	for line in lines:
		if line.find("Visibility:Never") > 0 or line.find("Muted") > 0:
			continue;
		if line.startswith("|AddStaff"):
			staves += 1
		if line.startswith("|Lyric") and not line.startswith("|Lyrics"):
			lyrics = line[14:-1]
			if lyrics[1] == '.':
				lyrics = lyrics[3:]
				lyrics = lyrics.replace("\\n\\n", "\\n")
			if len(lyrics) > len(longest_lyrics[staves-1]):
				longest_lyrics[staves-1] = lyrics
		if line.startswith("|TimeSig|"):
			for part in line[9:].split("|"):
				if part.startswith("Signature:"):
					value = part[10:]
					timesig_count += (0 if value == timesig else 1)
					if timesig is None:
						timesig = value
					if timesig.find("/") > 0:
						bpm = int(value.split("/")[0])
						beat_len = 1 / int(value.split("/")[1])
		if line.startswith("|Key|"):
			for part in line[5:].split("|"):
				if part.startswith("Signature:"):
					notes = (part[10:]).split(",")
					key = ""
					for i in range(len(notes)):
						key += notes[i][0].upper()
					keysig_count += (0 if KEYMAP[key] == keysig else 1)
					if keysig is None:
						keysig = KEYMAP[key]
		if line.startswith("|Tempo|"):
			for part in line[7:].split("|"):
				if part.startswith("Tempo:"):
					value = part[6:]
					tempo_count += (0 if value == tempo else 1)
					if tempo is None:
						tempo = value
		if line.startswith("|SongInfo|"):
			for part in line[10:].split("|"):
				if part.startswith("Title:"):
					title = part[6:].replace('"','')
					if meter is None:
						meter = parse_meter(title)
						if meter is not None and title.find(str(meter[0])) >= 0:
							title = (title[0:title.find(str(meter[0]))] + "$").replace(", $", "").upper()
				if part.startswith("Author:"):
					author = part[7:].replace('"','')
				if part.startswith("Lyricist:"):
					lyricist = part[9:].replace('"','')
				if part.startswith("Copyright1:"):
					terms = part[11:].replace('"','')
					if terms.lower().find("public domain") < 0:
						print("Warning: Copyright1 is not Public Domain")
				if part.startswith("Copyright2:"):
					if part[11:].find("Courtesy of the Cyber Hymnal") > 0:
						transcription = "Converted from the Cyber Hymnal(tm) on " + str(datetime.date.today()) + " using " + __file__
				if part.startswith("Comments:"):
					comments = part[9:].replace('"','')
	#end for line
	
	staves = max(staves,1)
	
	if timesig is None:
		timesig = "C"
	if keysig is None:
		keysig = "C"
	if tempo is None:
		tempo = "100"
		
	header = "X:1\n"
	header += "T:" + title + "\n"
	if meter_str is not None:
		header += "T:(" + meter_str + ")\n"
	elif meter is not None:
		header += "T:(" + meter_string(meter) + ")\n"
	header += "C:" + author + "\n"
	if terms != "":
		header += "Z:Terms:" + terms + "\n"
	if transcription != "":
		header += "Z:Transcription:" + transcription + "\n"
	if comments != "":
		header += "Z:" + comments + "\n"
	header += "I:score (1 2) (3 4)\n"
	header += "I:voicecombine 1\n"
	header += "L:1/1\n"
	header += "M:" + timesig + "\n"
	header += "Q:1/4=" + str(tempo) + "\n"
	header += "K:" + keysig + "\n"
	
	if timesig_count == 0:
		print ("Warning: No time signature. Using common time.")
	if keysig_count > 1:
		print ("Warning: Multiple key signatures not yet supported.")
	
	splits = [[]]
	music = ["","","",""]

	for passno in range(1,3):
		#print("Pass " + str(passno))
		staff = 0
		for lineno in range(len(lines)):
			line = lines[lineno]
			if line.find("Visibility:Never") > 0 or line.find("Muted") > 0:
				continue;
			if line.startswith("|Flow|") and passno == 2:
				if line.find("Style:Fine") > 0:
					if staff == 0:
						music[0] += "!fine!"
				if line.find("Style:DCalFine") > 0:
					if staff == 0:
						music[0] += "!D.C.!"
			if line.startswith("|Note|") or line.startswith("|Chord|") or line.startswith("|Rest|") or line.startswith("|RestChord|"):
				grace = (line.find("Grace") > 0)
				openings = []
				slurs = []
				notes = []
				positions = []
				durations = []
				options = []
				tie_marks = []
				for suffix in ["", "2"]:
					pos = ""
					dur = None
					opts = ""
					for part in line[1:].split("|"):
						if part.startswith("Pos" + suffix + ":"):
							pos = part[4 + len(suffix):]
						elif part.startswith("Dur" + suffix + ":"):
							dur = part[4 + len(suffix):]
						elif part.startswith("Opts" + suffix + ":"):
							opts = part[5 + len(suffix):]
					if dur is not None:
						for value in pos.split(","):
							if value == "":
								positions.append(None)
							else:
								pos_no = 0
								for i in range(len(value)):
									if value[i].isdigit():
										pos_no = pos_no * 10 + int(value[i])
								if value.find("-") >= 0:
									pos_no = -pos_no
								positions.append(pos_no)
							opening = ""
							if dur.find(",Staccato") > 0:
								opening = "." + opening
							if dur.find(",Accent") > 0:
								opening = "L" + opening
							if dur.find(",Triplet=First") > 0:
								opening = "(3" + opening
							openings.append(opening)
							if len(pos) == 0:
								notes.append("x" if line.find("HideRest") >= 0 else "z");
							else:
								notes.append(convertNote(value, clef))
							durations.append(convertDuration(dur))
							options.append(opts)
							slurs.append(dur.find("Slur") > 0)
							tie_marks.append(value.find("^") > 0)
				longest_index = 0
				shortest_index = 0
				highest_index = 0
				uniform_notes = True
				uniform_len = True
				for i in range(1,len(notes)):
					uniform_notes = (uniform_notes and notes[i] == notes[0])
					uniform_len = (uniform_len and durations[i][0] == durations[0][0])
					if durations[i][0] > durations[longest_index][0]:
						longest_index = i
					if durations[i][0] < durations[shortest_index][0]:
						shortest_index = i
					if positions[highest_index] == None and positions[i] != None:
						highest_index = i
					if positions[highest_index] != None and positions[i] != None and positions[i] > positions[highest_index]:
						highest_index = i
				if None in positions:
					if options[highest_index].find("Stem=Up") < 0:
						for i in range(len(notes)):
							if options[i].find("Stem=Down") < 0:
								highest_index = i
								break
				indexes = [[],[]]
				stem_dir = "down" if staff == 1 else "up"
				if grace or music_len[LOWER] - music_len[UPPER] > SMALL:
					for i in range(len(notes)):
						indexes[UPPER].append(i)
					if staff == 1:
						stem_dir = "up"
				elif music_len[UPPER] - music_len[LOWER] > SMALL:
					for i in range(len(notes)):
						indexes[LOWER].append(i)
					if staff == 0:
						stem_dir = "down"
				else:
					for i in range(0,len(notes)):
						if i == highest_index:
							indexes[UPPER].append(i)
						elif not uniform_len and durations[i][0] == durations[highest_index][0]:
							indexes[UPPER].append(i)
						else:
							indexes[LOWER].append(i)
					if len(notes) == 1:
						indexes[LOWER].append(None)
				for voice in (UPPER, LOWER):
					if not uniform_len:
						if staff == 0 and voice == LOWER:
							stem_dir = "down"
						if staff == 1 and voice == UPPER:
							stem_dir = "up"
					if len(indexes[voice]) > 0:
						music_str = ""
						if indexes[voice][0] == None:
							music_str += " " + openings[indexes[UPPER][0]] + "x" + durations[indexes[UPPER][0]][1]
						else:
							if ((staff == 0 and voice==LOWER) or (staff == 1 and voice==UPPER)) and stem_dir != last_stem_dir:
								last_stem_dir = stem_dir
							at_beat = start_beat is not None and abs(((music_len[voice] - start_beat) / beat_len) - round((music_len[voice] - start_beat) / beat_len)) < SMALL
							if rebeam and (start_beat is None or at_beat): # or durations[indexes[voice][0]][0] - beat_len > SMALL):
								music_str += " "
							if slurs[indexes[voice][0]]:
								if not in_slur[voice]:
									music_str += "("
									in_slur[voice] = True
							music_str += openings[indexes[voice][0]]
							if len(indexes[voice]) > 1:
								music_str += "["
							if grace:
								music_str += "{"
							in_tie[voice] = False
							for i in range(len(indexes[voice])):
								music_str += notes[indexes[voice][i]]
								if len(indexes[voice]) > 1 and tie_marks[indexes[voice][i]]:
									music_str += "-"
								in_tie[voice] = in_tie[voice] or tie_marks[indexes[voice][i]]
							if grace:
								music_str += "}"
							if len(indexes[voice]) > 1:
								music_str += "]"
							music_str += durations[indexes[voice][0]][1]
							if len(indexes[voice]) == 1 and tie_marks[indexes[voice][0]]:
								music_str += "-"
							if not slurs[indexes[voice][0]]:
								if in_slur[voice]:
									music_str += ")"
									in_slur[voice] = False
							if not rebeam and (options[indexes[voice][0]].find("Beam") < 0 or options[indexes[voice][0]].find("Beam=End") >= 0):
								music_str += " "
						if passno == 2:
							music[staff * 2 + voice] += music_str
						if indexes[voice][0] == None:
							music_len[voice] += durations[indexes[UPPER][0]][0]
						else:
							music_len[voice] += durations[indexes[voice][0]][0]
				bar_len += durations[shortest_index][0]
			if line.startswith("|Note|") or line.startswith("|Chord|") or line.startswith("|Rest|") or line.startswith("|RestChord|") or line.startswith("|Bar") or line.startswith("|AddStaff") or line.startswith("|TimeSig|") or line.startswith("|Done"):
				bartype = 0
				if line.startswith("|Bar"):
					bartype = 1
					if line.find("Style:Double") > 0:
						bartype = 2
					if line.find("Style:LocalRepeatOpen") > 0:
						bartype = 3
					if line.find("Style:LocalRepeatClose") > 0:
						bartype = 4
				if line.startswith("|AddStaff"):
					bartype = 8
				if line.startswith("|TimeSig"):
					bartype = 9
				if line.startswith("|Done"):
					bartype = 10
				pos = min(music_len[UPPER], music_len[LOWER])
				max_pos = max(music_len[UPPER], music_len[LOWER])
				at_beat = start_beat is not None and abs(((pos - start_beat) / beat_len) - round((pos - start_beat) / beat_len)) < SMALL
				ipos = 0
				if (at_beat):
					ipos = int(round((pos - start_beat) / beat_len))
				music_str = ""
				if bartype > 0 and bartype < 8:
					if passno == 1:
						if start_beat is None:
							if pos > 1 + SMALL:
								print("Warning: line " + str(lineno) + ": First bar is beyond the first measure.")
						else:
							if bartype == 1 and ((pos - start_beat) * bpm / beat_len + SMALL) - round((pos - start_beat) * bpm / beat_len + SMALL) > SMALL * 2:
								print("Warning: line " + str(lineno) + ": Bar is not at a valid measure boundary.")
							if not at_beat:
								print("Warning: line " + str(lineno) + ": Bar is not on a valid beat.")
						if max_pos - pos > SMALL:
							print("Warning: line " + str(lineno) + ": Long note of previous chord crosses the bar.")
					if start_beat is None:
						start_beat = pos
				valid_split = (at_beat and (max_pos - pos < SMALL) and ipos >= 0 and (not in_slur[0]) and (not in_slur[1]) and (not in_tie[0]) and (not in_tie[1]))
				while len(splits[section]) <= ipos:
					splits[section].append(0)
				if passno == 2:
					valid_split = (valid_split and splits[section][ipos] == staves) 
				if valid_split or bartype > 0:
					if passno == 1 and valid_split and bartype == 0:
						splits[section][ipos] = splits[section][ipos] + 1
				if bartype == 0:
					if valid_split and passno == 2:
						music_str += "!sp!y "
				else:
					bar_len = 0
					if bartype == 1:
						music_str += "| "
					elif bartype == 2:
						music_str += "|| "
					elif bartype == 3:
						music_str += "|: "
					elif bartype == 4:
						music_str += ":| "
				if bartype == 2 or bartype == 9:
					section += 1
					while len(splits) <= section:
						splits.append([])
					start_beat == None
					music_len[UPPER] = 0
					music_len[LOWER] = 0
				if passno == 2:
					music[staff*2] += music_str
					music[staff*2 + 1] += music_str
			if line.startswith("|TimeSig|"):
				for part in line[9:].split("|"):
					if part.startswith("Signature:"):
						timesig = part[10:]
						if passno == 2:
							music[staff*2] += "[M:" + timesig + "] "
						if timesig.find("/") > 0:
							bpm = int(timesig.split("/")[0])
							beat_len = 1 / int(timesig.split("/")[1])
			if line.startswith("|Begin") or line.startswith("|AddStaff"):
				section = 0
				music_len = [0, 0]
				bar_len = 0
				in_slur = [False, False]
				in_tie = [False, False]
				start_beat = None
				if staff == 0 and len(music[0]) > 1:
					staff = 1
				clef = ("bass" if staff == 1 else "treble")
				last_stem_dir = ("down" if staff == 1 else "up")
			if line.startswith("|Clef|"):
				for part in line[6:].split("|"):
					if part.startswith("Type:"):
						clef = part[5:].lower()
			if passno == 2 and line.startswith("|Text"):
				if line.upper().find("REFRAIN") > 0:
					music[0] += "\"REFRAIN\" y "
	body = ""
	for i in range(len(music)):
		body += "V:" + str(i+1) + (" clef=bass" if i > 1 else " clef=treble") + (" stem=up" if i % 2 == 0 else " stem=down") + "\n"
		if i == 2:
			body += "I:pos vocal above\n"
		body += music[i]
		if music[i][-2:].find("|") < 0:
			body += "|]"
		body += "\n"
		if i % 2 == 0 and longest_lyrics[i >> 1] != "":
			body += "w:"
			lines = longest_lyrics[i >> 1].split("\\n")
			for row in range(len(lines)):
				words = lines[row].replace("-", " ").split(" ")
				blank = True
				for col in range(1,len(words)+1):
					if words[col-1] != "":
						if row > 0 and col == 1:
							body += "\n+:"
						if words[col-1] == "-":
							if blank:
								if col > 1:
									body += " "
								body += "~"
							else:
								body += "_"
						else:
							if col > 1:
								body += " "
							body += chr(ord("a" if i > 1 else "A") + row) + str(col)
							blank = False
			body += "\n"
		elif meter and i % 2 == 0:
			body += "w:"
			for row in range(len(meter)):
				for col in range(1,meter[row]+1):
					if row > 0 and col == 1:
						body += "\n+:"
					if col > 1:
						body += " "
					body += chr(ord("a" if i > 1 else "A") + row) + str(col)
			body += "\n"
	body = body.replace("  ", " ")
	body = body.replace("(3x/16 x/16 x/16", "x/8")
	body = body.replace("(3x/8 x/8 x/8", "x/4")
	body = body.replace("!sp!y |", "|")
	return header + body
	

test_text = """
"""

rebeam = False
for i in range(len(sys.argv)):
	if sys.argv[i].find("rebeam") >= 0:
		rebeam = True

meter = None
if len(sys.argv) > 2:
	if sys.argv[2].find("rebeam") < 0:
		meter = sys.argv[2]
	
if len(sys.argv) > 1 and sys.argv[1] == "test":
	print(convert(test_text, meter, rebeam))
elif len(sys.argv) > 1:
	text = ""
	with open(sys.argv[1],encoding="utf-8") as f:
		for line in f:
			text += line
	print(convert(text, meter, rebeam))
else:
	print("Syntax: " + sys.argv[0] + " filename [meter] [rebeam]")