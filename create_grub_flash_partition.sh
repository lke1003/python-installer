#!/bin/bash

RESULT=0
GV_FLASH_P1_LABEL=$1
GV_FLASH_P3_LABEL=$2
DD_FLASH_DEV=$3

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

echo "################# Creating flash #####################" >> fullinstall.log  
dd if=/dev/zero of=$DD_FLASH_DEV bs=1024k count=10 >/dev/null 2>&1

#### partition 1 for boot
umount ""$DD_FLASH_DEV"1" >/dev/null 2>&1
fdisk $DD_FLASH_DEV >/dev/null 2>&1 <<EOF
n
p
1

+10G
n
p
2

+5G
n
e



n

+1M
n

+2M
n

+3M
n

+4M
w


EOF
sleep 1

#Create Partition 1 filesystem
mkfs.ext4 -FL "$GV_FLASH_P1_LABEL" ""$DD_FLASH_DEV"1" >/dev/null 2>&1
func_check_error $? "Can not create filesystem in partition1 of flash."

sleep 1
mkfs.ext4 -FL "$GV_FLASH_P3_LABEL" ""$DD_FLASH_DEV"2" >/dev/null 2>&1
func_check_error $? "Can not create filesystem in partition2 of flash."
sleep 3

exit $RESULT
