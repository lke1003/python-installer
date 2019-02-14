#!/bin/bash

RAID_MODE=$1
GV_OS_ALIAS="OS_Drive"
SG_MAP_LD_NAME="Promise"
GV_DATA_ALIAS="DATA_Drive"
RESULT=0

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

func_wait_for_ld_init_to_finish() {
    while [ 1 ]
    do
        INIT_FINISHED=$(clitest -u administrator -p password -C init | grep "This background activity is not running")
        if [ x"$INIT_FINISHED" != "x" ]; then
            break
        fi
        sleep 1
    done
}

create_raid_da()
{
    case $1 in
        "RAID_0" | "RAID_1" | "RAID_1+0" | "RAID_5")
            clitest -u administrator -p password -C array -a add -p $PHY_LIST
            func_check_error $? "Can not create DA."
            ;;
        "RAID_5+Hotspare")
            CAPACITY=$(clitest -u administrator -p password -C phydrv -v | grep Configurable | awk '{print $4}')
            MAX=0
            MAXCOUNT=0
            count=0
            for size in $CAPACITY
            do
                count=$((${count}+1))
                unit=$(echo ${size} | tail -c 3)
                if [ "${unit}" == "GB" ]; then
                    size=$(echo $size | sed 's/..$//' )
                    size=${size%.*}
                fi
                
                if [ "${unit}" == "TB" ]; then
                    size=$(echo $size | sed 's/..$//')
                    size=`echo $size \* 1024  |bc`;
                    size=${size%.*}
                fi
                
                if [ ${size} -ge ${MAX} ]; then
                    MAX=${size}
                    MAXCOUNT=${count}
                fi
            done
            
            SPARE_PD=$(clitest -u administrator -p password -C phydrv |grep Slot|awk '{print $1}'| sed -n "${MAXCOUNT}p")

            clitest -u administrator -p password -C spare -a add -p $SPARE_PD -t g -r y
            func_check_error $? "Can no create Hotspare."
            sleep 2

            PHY_LIST=$(clitest -u administrator -p password -C phydrv|grep OK|grep Unconfigured|awk '{print $1}')
            PHY_LIST=$(echo $PHY_LIST|sed 's/ /,/g')

            clitest -u administrator -p password -C array -a add -p $PHY_LIST
            func_check_error $? "Can not create raid 5+Hotspare."
            ;;
        "RAID_6")
            clitest -u administrator -p password -C array -a add -p $PHY_LIST
            func_check_error $? "Can not create raid 6."
            ;;
    esac
}

create_raid_ld()
{
    TMP_RAID=$1
    TMP_ALIAS=$2
    TMP_CAPACITY=$3

    case $TMP_RAID in
        "RAID_0")
            TMP_RAID="0"
            ;;
	"RAID_1")
            TMP_RAID="1"
            ;;
	"RAID_1+0")
            TMP_RAID="10"
            ;;
	"RAID_5" | "RAID_5+Hotspare")
            TMP_RAID="5"
            ;;
        "RAID_6")
            TMP_RAID="6"
            ;;
    esac

    if [ "$TMP_CAPACITY" != 0 ]; then
        clitest -u administrator -p password -C array -a addld -d 0 -l \"raid="$TMP_RAID",alias="$TMP_ALIAS",capacity="$TMP_CAPACITY"\"
        func_check_error $? "Can not create LD"
    else
        clitest -u administrator -p password -C array -a addld -d 0 -l \"raid="$TMP_RAID",alias="$TMP_ALIAS"\"
        func_check_error $? "Can not create LD"
    fi
    func_wait_for_ld_init_to_finish

}

create_raid_da  $RAID_MODE
sleep 2

OLD_DEV=$(sg_map -i |grep "$SG_MAP_LD_NAME" |grep -vn 'V-LUN' |awk '{print $2}')
create_raid_ld $RAID_MODE $GV_OS_ALIAS 20GB

OLD_DEV=$(sg_map -i |grep "$SG_MAP_LD_NAME" |grep -vn 'V-LUN' |awk '{print $2}')
OLD_DEV=$(echo $OLD_DEV | sed 's/\/dev\///g')
for DEV in $OLD_DEV
do
    NEW_DEV=$DEV
done
OS_DEV=$(echo $NEW_DEV|sed 's/ //g')


OLD_DEV=$(sg_map -i |grep "$SG_MAP_LD_NAME" |grep -vn 'V-LUN' |awk '{print $2}')
create_raid_ld $RAID_MODE "$GV_DATA_ALIAS"1"" 0
sleep 2

OLD_DEV=$(sg_map -i |grep "$SG_MAP_LD_NAME" |grep -vn 'V-LUN' |awk '{print $2}')
OLD_DEV=$(echo $OLD_DEV | sed 's/\/dev\///g')
for DEV in $OLD_DEV
do
    #  echo $DEV
    NEW_DEV=$DEV
done
DATA_DEV=$(echo $NEW_DEV|sed 's/ //g')

############################################################################
OS_LD=$(clitest -u administrator -p password -C logdrv |grep "$GV_OS_ALIAS" |awk '{print $1}')
DATA_LD=$(clitest -u administrator -p password -C logdrv |grep "$GV_DATA_ALIAS" |awk '{print $1}')

partition_os_ld

partition_data_ld