#!/bin/env python3

import sys
import argparse
import math
import re
import traceback

from directives import DirectiveProcessor
from tokens import Tokenizer
from readers import CodeReader
from renderers import *
import statements

# ==================== Command Line Arguments processing =======================

parser = argparse.ArgumentParser(description='SDS-C macro preprocessor')

parser.add_argument(
		'source',
		help='The source file to process'
)

parser.add_argument(
		'-o', '--output',
		help='The output file. To just print the output, use -d'
)

parser.add_argument(
		'-d', '--display',
		action='store_true',
		default=False,
		help='Show the final source (Works together with -o)'
)

parser.add_argument(
		'-v', '--verbose',
		action='store_true',
		default=False,
		help='Show all optional debug info.'
)

parser.add_argument(
		'-G', '--show-generated',
		action='store_true',
		default=False,
		help='Show the code generated from statements.'
)

parser.add_argument(
		'-O', '--show-original',
		action='store_true',
		default=False,
		help='Show original source (only main file)'
)

parser.add_argument(
		'-M', '--show-macros',
		action='store_true',
		default=False,
		help='List all macros'
)

parser.add_argument(
		'-R', '--show-resolved',
		action='store_true',
		default=False,
		help='Show code after processing includes and # branching.'
)

parser.add_argument(
		'-P', '--show-processed',
		action='store_true',
		default=False,
		help='Show code after replacing macros'
)

parser.add_argument(
		'-T', '--show-tokens',
		action='store_true',
		default=False,
		help='Show tokens (source divided to pieces).'
)

parser.add_argument(
		'-S', '--show-statements',
		action='store_true',
		default=False,
		help='Show statements (high-level code abstraction).'
)

args = parser.parse_args()


SRC		= args.source
DEST	= args.output


SHOW_ORIGINAL	= args.verbose or args.show_original

SHOW_RESOLVED	= args.verbose or args.show_resolved
SHOW_MACROS		= args.verbose or args.show_macros
SHOW_PROCESSED	= args.verbose or args.show_processed
SHOW_TOKENS		= args.verbose or args.show_tokens
SHOW_STATEMENTS	= args.verbose or args.show_statements
SHOW_GENERATED	= args.verbose or args.show_generated
SHOW_OUTPUT		= args.verbose or args.display


# ==================== Utils =======================


def banner(text, fill='-', length=80):
	""" Show a banner line """
	blob = (fill*length + ' ' + text + ' ' + fill*length)
	overlap = len(blob)-80
	print('\n' + blob[ math.floor(overlap/2) : math.floor(-overlap/2)] + '\n')


def prep4disp(code):
	c = '  ' + re.sub(r'\n', '\n  ', code)
	c = re.sub(r'\t', '    ', c)
	return c


# ==================== MAIN TASK =======================

try:

	banner('SDS-C Preprocessor', ':')

	print('Reading file:', SRC)

	# read the file
	dproc = DirectiveProcessor(SRC)

	if SHOW_ORIGINAL:
		banner('SOURCE', '-')
		print(prep4disp( dproc.source ) + '\n')

	# ---------------- Resolve directives ------------------


	# include files, resolve branching, find macros...
	dproc.process()


	if SHOW_MACROS:
		banner('MACROS', '-')
		print('List of all found macros, in definition order:\n')
		for d in dproc.get_defines().values():
			for m in d:
				print('  ' + str(m))
		print()



	if SHOW_RESOLVED:
		banner('RESOLVED', '-')
		print('Code after resolving includes, # branching, and extracting macros:\n')
		print(prep4disp( dproc.get_output() ) + '\n')


	# -------------------- Apply macros --------------------

	# perform macro replacements
	dproc.apply_macros()
	# get output code
	processed = dproc.get_output()


	if SHOW_PROCESSED:
		banner('PROCESSED', '-')
		print('Code after replacing macros:\n')

		print(prep4disp(processed) + '\n')


	tk = Tokenizer(processed)

	tokens = tk.tokenize()
	sts = statements.parse(tokens)


	if SHOW_TOKENS:
		banner('TOKENIZED', '-')
		print('Tokenization of the processed code:\n')
		tk.show()
		print('')


	if SHOW_STATEMENTS:
		banner('STATEMENTS', '-')
		print('Source code abstraction:\n')


		for s in sts:
			print(str(s))


	if SHOW_GENERATED:
		banner('GENERATED', '-')
		print('Code generated from statements:\n')

		rndr = BasicRenderer(sts)
		print(prep4disp(rndr.render()))


	if DEST != None or SHOW_OUTPUT:

		# perform tweaks to match some of SDS-C's broken syntax
		rndr = SdsRenderer(sts)
		for_sds = rndr.render()

		if SHOW_OUTPUT:
			banner('OUTPUT SDS-C CODE', '-')
			print(prep4disp(for_sds) + '\n')

		if DEST != None:
			print('Writing to file: %s' % DEST)
			f = open(DEST, 'w')
			f.write(for_sds)
			f.close()
		else:
			print('No output file specified.')


	print('\nDone.\n')

except SyntaxError as e:
	banner('SYNTAX ERROR', '#')
	type_, value_, traceback_ = sys.exc_info()
	ex = traceback.format_exception(type_, value_, traceback_)
	for line in ex:
		# discard useless junk
		if 'raise SyntaxError' in line:
			continue
		if 'File "<string>", line None' in line:
			continue

		print(line)

