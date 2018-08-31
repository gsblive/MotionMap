#
#
#		Test Routines for GitLab Summit SA 2018
#
#
#
#
#

hBannerAlphabet = 	{
						' ': ['  ', '  ', '  ', '  ', '  ', '  ', '  '],
						'!': ['   !!!   ', '   !!!   ', '   !!!   ', '   !!!   ', '    !    ', '         ', '   !!!   '],
						'A': ['   AAA   ', ' AAA AAA ', 'AAA   AAA', 'AAAAAAAAA', 'AAAAAAAAA', 'AAA   AAA', 'AAA   AAA'],
						'B': ['BBBBBBBB ', 'BBB   BBB', 'BBB   BBB', 'BBBBBBB  ', 'BBB   BBB', 'BBB   BBB', 'BBBBBBBB '],
						'C': [' CCCCCCC ', 'CCC   CCC', 'CCC      ', 'CCC      ', 'CCC      ', 'CCC   CCC', ' CCCCCCC '],
						'D': ['DDDDDDD  ', 'DDD  DDD ', 'DDD   DDD', 'DDD   DDD', 'DDD   DDD', 'DDD  DDD ', 'DDDDDDD  '],
						'E': ['EEEEEEEEE', 'EEEEEEEEE', 'EE       ', 'EEEEEEE  ', 'EEE      ', 'EEEEEEEEE', 'EEEEEEEEE'],
						'F': ['FFFFFFFFF', 'FFFFFFFFF', 'FFF      ', 'FFFFFFF  ', 'FFF      ', 'FFF      ', 'FFF      '],
						'G': [' GGGGGGG ', 'GGGGGGGGG', 'GGG      ', 'GGG   GGG', 'GGG    GG', 'GGGGGGGGG', ' GGGGGGG '],
						'H': ['HHH   HHH', 'HHH   HHH', 'HHHHHHHHH', 'HHHHHHHHH', 'HHH   HHH', 'HHH   HHH', 'HHH   HHH'],
						'I': ['IIIIIIIII', 'IIIIIIIII', '   III   ', '   III   ', '   III   ', 'IIIIIIIII', 'IIIIIIIII'],
						'J': ['     JJJJ', '      JJJ', '      JJJ', '      JJJ', 'JJJ   JJJ', 'JJJJJJJJJ', ' JJJJJJJ '],
						'K': ['KKK   KKK', 'KKK  KKK ', 'KKK KKK  ', 'KKKKKK   ', 'KKK KKK  ', 'KKK  KKK ', 'KKK   KKK'],
						'L': ['LLL      ', 'LLL      ', 'LLL      ', 'LLL      ', 'LLL      ', 'LLLLLLLLL', 'LLLLLLLLL'],
						'M': ['MMM   MMM', 'MMMM MMMM', 'MMMM MMMM', 'MM MMM MM', 'MM MMM MM', 'MM  M  MM', 'MM     MM'],
						'N': ['NNN    NN', 'NNNN   NN', 'NN NN  NN', 'NN  NN NN', 'NN   NNNN', 'NN    NNN', 'NN     NN'],
						'O': ['  OOOOO  ', ' OO   OO ', 'OO     OO', 'OO     OO', 'OO     OO', ' OO   OO ', '  OOOOO  '],
						'P': ['PPPPPPPP ', 'PPP    PP', 'PPP    PP', 'PPPPPPPP ', 'PPP      ', 'PPP      ', 'PPP      '],
						'Q': ['  QQQQQ  ', ' QQ   QQ ', 'QQ     QQ', 'QQ     QQ', 'QQ   Q QQ', ' QQ   QQ ', '  QQQQQ Q'],
						'R': ['RRRRRRRR ', 'RRRRRRRRR', 'RRR   RRR', 'RRRRRRRR ', 'RRRRRR   ', 'RRR  RRR ', 'RRR   RRR'],
						'S': ['  SSSSS  ', 'SSS   SSS', ' SSS     ', '   SSS   ', '      SSS', 'SSS   SSS', '  SSSSS  '],
						'T': ['TTTTTTTTT', 'TTTTTTTTT', '   TTT   ', '   TTT   ', '   TTT   ', '   TTT   ', '   TTT   '],
						'U': ['UUU   UUU', 'UUU   UUU', 'UUU   UUU', 'UUU   UUU', 'UUU   UUU', 'UUUUUUUUU', ' UUUUUUU '],
						'V': ['VVV   VVV', 'VVV   VVV', 'VVV   VVV', ' VVV VVV ', ' VVV VVV ', '  VVVVV  ', '   VVV   '],
						'W': ['WW     WW', 'WW  W  WW', 'WW WWW WW', 'WW WWW WW', 'WWWW WWWW', 'WWWW WWWW', 'WWW   WWW'],
						'X': ['XXX   XXX', ' XX   XX ', '  XX XX  ', '   XXX   ', '  XX XX  ', ' XX   XX ', 'XXX   XXX'],
						'Y': ['YYY   YYY', ' YY   YY ', '  YY YY  ', '   YYY   ', '   YYY   ', '   YYY   ', '   YYY   '],
						'Z': ['ZZZZZZZZZ', 'ZZZZZZZZZ', '     ZZZ ', '   ZZZ   ', ' ZZZ     ', 'ZZZZZZZZZ', 'ZZZZZZZZZ']}


def printHorizontalWord(theWord):
	count = len(hBannerAlphabet['A'])
	for lineNum in range(0,count):
		lineAccumulator = ""
		for aChar in theWord:
			charLine = hBannerAlphabet[aChar][lineNum]
			lineAccumulator = lineAccumulator + charLine + hBannerAlphabet[' '][lineNum]
		print(lineAccumulator)


def printHorizontalBanner(theString):
	lineList = theString.split("\n")
	for parsedWord in lineList:
		printHorizontalWord(parsedWord)
		print("\n\n\n")





print("\n\n\n")
printHorizontalBanner("GIRAFFES\n       CAN\nDANCE !!!")