#!/bin/bash

MountDir=$1
DD_FLASH_DEV=$2

GV_OS_LABEL=$3
GV_BACKUP_LABEL=$4
GV_FLASH_P1_LABEL=$5

RESULT=0

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

cd $MountDir
tar jxmfv /prom-pkg/disk_rootfs.tar.bz2 > $MountDir/progress.log
func_check_error $? "Install root filesystem error."

cd /prom-pkg 
./prom-install.sh $MountDir $DD_FLASH_DEV > $MountDir/PromiseInstall.log
func_check_error $? "Install PromiseInstall error."


cd /
touch /INSTALL_FLAG
sleep 3

echo "LABEL="$GV_OS_LABEL" / ext4 errors=remount-ro 0 0" > $MountDir/etc/fstab
echo "LABEL="$GV_FLASH_P1_LABEL" /boot ext4 defaults 0 0" >> $MountDir/etc/fstab
echo "/swapfile  none swap sw 0 0" >> $MountDir/etc/fstab

echo "LABEL="$GV_BACKUP_LABEL" / ext4 defaults 0 0" > $MountDir/etc/fstab.backup
echo "LABEL="$GV_FLASH_P1_LABEL" /boot ext4 errors=remount-ro 0 0" >> $MountDir/etc/fstab.backup
echo "/swapfile  none swap sw 0 0" >> $MountDir/etc/fstab.backup


if [ ! -e "$MountDir/swapfile" ]; then
dd if=/dev/zero of=$MountDir/swapfile bs=1M count=1024 > $MountDir/progress.log
chmod 600 $MountDir/swapfile > $MountDir/progress.log
mkswap $MountDir/swapfile > $MountDir/progress.log
fi 

exit $RESULT