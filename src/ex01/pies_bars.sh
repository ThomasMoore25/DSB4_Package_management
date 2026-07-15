#!/bin/bash
block=$(printf '\u2588')
echo -e "\033[35m${block}\033[0m Pies   \033[33m${block}\033[0m Bars"
echo ""
termgraph data.dat --color magenta yellow