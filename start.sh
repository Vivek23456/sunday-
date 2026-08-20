#!/bin/bash

cd /home/vivek/Projects/sunday

source .venv/bin/activate

export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cublas/lib:$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"

exec python sunday.py

