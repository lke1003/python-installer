#!/bin/bash

DD_FLASH_DEV=$1

echo "################# Create Flash Partition ########################" >> fullinstall.log   
# clear install target #
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

+20G
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


