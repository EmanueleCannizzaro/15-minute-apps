#!/bin/bash

run_script () {
  cd $1
  echo "Now running... $1"
  python $1.py
  cd ..
}

run_script "browser"
run_script "browser_tabbed"
run_script "calculator"
run_script "camera"
#run_script "colorpicker"
run_script "crypto"
run_script "currency"
run_script "mediaplayer"
run_script "minesweeper"
run_script "notepad"
run_script "notes"
run_script "paint"
run_script "solitaire"
run_script "translate"
#run_script "unzip"
run_script "weather"
run_script "wordprocessor"
