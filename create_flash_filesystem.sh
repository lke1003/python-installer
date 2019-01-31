#!/bin/bash

GV_FLASH_P1_LABEL=$1
GV_FLASH_P2_LABEL=$2
DD_FLASH_DEV=$3
GV_INSTALL_OS_TO_FLASH=$4

#Create Partition 1 filesystem
yes | mkfs.ext4 -L "$GV_FLASH_P1_LABEL" ""$DD_FLASH_DEV"1" >/dev/null 2>&1

#umount /flash >/dev/null 2>&1
if [ "$GV_INSTALL_OS_TO_FLASH" == "0" ]; then
### partition 2 for OS
umount ""$DD_FLASH_DEV"1" >/dev/null 2>&1
sleep 1
yes | mkfs.ext4 -L "$GV_FLASH_P2_LABEL" ""$DD_FLASH_DEV"2" >/dev/null 2>&1
sleep 1
fi
