#!/bin/bash
# usage: run_chunk.sh <tree: baseline|after> <chunk name>
R=$HOME/brixreview; T=$1; C=$2
if [ "$T" = baseline ]; then cd $HOME/baseline; else cd $HOME/mnt/commerce_ai_generator; fi
case $C in
  food) ARGS="tests/services/food";;
  rec) ARGS="tests/services/recommendation";;
  xb_chat) ARGS="tests/services/cross_border tests/services/chat";;
  rest) ARGS="tests --ignore=tests/services/food --ignore=tests/services/recommendation --ignore=tests/services/cross_border --ignore=tests/services/chat";;
esac
timeout 175 $HOME/testenv/bin/python -m pytest $ARGS -p no:cacheprovider -q -rfE --tb=long --junitxml=$R/${T}_${C}_junit.xml > $R/${T}_${C}.log 2>&1
echo "$T $C exit=$? :: $(tail -1 $R/${T}_${C}.log)"
