# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 09:44:22 2020

@author: bruger
"""

from pathlib import Path, PurePosixPath, PurePath

with open('Postbuild','wt') as f:
    f.write('''\
#!/bin/bash 
''')
    for dir in Path('../').glob('**'):
        # print(dir.parts)

        if len(dir.parts)>1 and str(dir.parts[1]).startswith('.'): continue
        print(dir)
        for notebook in dir.glob('*.ipynb'):
            n = PurePosixPath(notebook)
            f.write(f'jupyter trust "{str(n).split("/",1)[1]}"\n')
    f.write('jupyter nbextension enable hide_input_all/main\n')  
    f.write('jupyter nbextension enable splitcell/splitcell\n') 
    f.write('python frbus-run-numba.py\n') 
    f.write('exec "$@"')
    # breakpoint()
