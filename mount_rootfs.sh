#!/bin/bash

DD_FLASH_DEV=$1
OS_BOOT_DEV="${DD_FLASH_DEV}1"
OS_ROOTFS_DEV=$2
GV_USB_INSTALL_PART=$3
mount_disk=$4
RESULT=0

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

echo "################# Mount rootfs ########################" >> fullinstall.log
mount -t ext4 $GV_USB_INSTALL_PART /cdrom >/dev/null 2>&1 

mount $OS_ROOTFS_DEV $mount_disk >/dev/null 2>&1 
func_check_error $? "Can not mount root filesystem."

sleep 3
mkdir -p /disk/boot >/dev/null 2>&1 
mount $OS_BOOT_DEV /disk/boot >/dev/null 2>&1 
func_check_error $? "Can not mount boot."

exit $RESULT