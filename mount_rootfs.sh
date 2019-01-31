#!/bin/bash

DD_FLASH_DEV=$1
OS_ROOTFS_DEV="${DD_FLASH_DEV}2"
OS_BOOT_DEV="${DD_FLASH_DEV}1"
GV_USB_INSTALL_PART=$2
mount_disk=$3

echo "################# Mount rootfs ########################" >> fullinstall.log
mount -t ext4 $GV_USB_INSTALL_PART /cdrom >/dev/null 2>&1 

mount $OS_ROOTFS_DEV $mount_disk >/dev/null 2>&1 

sleep 3
mkdir -p /disk/boot >/dev/null 2>&1 
mount $OS_BOOT_DEV /disk/boot >/dev/null 2>&1 
