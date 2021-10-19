import glob
import os
l = glob.glob('*/[!_]*')

for word in l:
	print('.'.join(os.path.basename(word).split('.')[:-1]))
