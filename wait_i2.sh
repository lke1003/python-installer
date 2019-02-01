#!/bin/bash

echo -n "Wait for i2 to start..." >> fullinstall.log
while [ $(pgrep -cx "\<i2\>") -eq 0 ]; do
    sleep 1
    echo -n "."
done
echo Done

exit 0