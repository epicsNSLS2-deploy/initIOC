#!/bin/bash

git clone https://github.com/jwlodek/npdoc2md
cd npdoc2md
python3 -u npdoc2md.py -i ../.. -o ../../docs
cd ..
rm -rf npdoc2md