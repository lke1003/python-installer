#!/bin/bash

DD_FLASH_DEV=$1
RESULT=0

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

grub-install --boot-directory=/disk/boot $DD_FLASH_DEV >/dev/null 2>&1
func_check_error $? "Grub install error."

exit $RESULT