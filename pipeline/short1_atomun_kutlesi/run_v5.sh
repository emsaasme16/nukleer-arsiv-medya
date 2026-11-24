#!/bin/bash
cd /home/claude/short1/code
rm -f ../out/v3_chunk_*.mp4
printf "0 8\n8 16\n16 24\n24 32\n32 38.2\n" | xargs -P 3 -L 1 python3 render3.py chunk
echo CHUNKS_DONE
