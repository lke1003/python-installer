#!/bin/bash

GV_OS_LABEL=$1
GV_DATA_LABEL=$2
RESULT=0
SG_MAP_LD_NAME="Promise"
GV_DATA_ALIAS="DATA_Drive"

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

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

echo "################# Create HDD Partition ########################" >> fullinstall.log
PHY_TMP=""
PHY=$(clitest -u administrator -p password -C phydrv | grep Unconfigured | awk '{print $1}')
PHY_OPST=$(clitest -u administrator -p password -C phydrv | grep OK | awk '{print $1}')
for PHY_UNCF in $PHY
do
    for PHY_OK in $PHY_OPST
    do
        if [ "$PHY_UNCF" == "$PHY_OK" ]; then
            PHY_TMP="$PHY_TMP $PHY_OK"
        fi
    done
done
PHY="$PHY_TMP"
GV_PHY_COUNT=0
for PHYS in $PHY
do
    GV_PHY_COUNT=$(( $GV_PHY_COUNT + 1 ))
done

PHY_LIST=$(echo $PHY | sed 's/,/ /g')

PHY_LIST=$(echo $PHY_LIST |sed 's/,/ /g')

COUNT_I=1
for PHY in $PHY_LIST
do
    OLD_DEV=$(sg_map -i |grep "$SG_MAP_LD_NAME" |grep -vn 'V-LUN' |awk '{print $2}')
    NO_RAID_LDA=""$GV_DATA_ALIAS""$(( $COUNT_I -1 ))""
    clitest -u administrator -p password -C array -a add -p $PHY -l \"raid=0,alias=$NO_RAID_LDA\"
    func_check_error $? "Can not create no raid."
    func_wait_for_ld_init_to_finish

    NEW_DEV=$(sg_map -i |grep "$SG_MAP_LD_NAME" |grep -vn 'V-LUN' |awk '{print $2}')
    OLD_DEV=$(echo $OLD_DEV | sed 's/\/dev\///g')
    NEW_DEV=$(echo $NEW_DEV | sed 's/\/dev\///g')
    for DEV in $OLD_DEV
    do
        NEW_DEV=$(echo $NEW_DEV|sed 's/'$DEV'//g')
    done

    NO_RAID_DEV[$COUNT_I]=$(echo $NEW_DEV|sed 's/ //g')
    COUNT_I=$(( $COUNT_I + 1 ))
done

#------------------------- partition ----------------------------

DATA_DRV_COUNT=1 
for (( COUNT_I=1; COUNT_I<=$GV_PHY_COUNT; COUNT_I=COUNT_I+1 ))
do
    NO_RAID_LABEL=""$GV_DATA_LABEL""$DATA_DRV_COUNT""
    if [ "$COUNT_I" == "1" ]; then
        OS_DEV=${NO_RAID_DEV[$COUNT_I]}
        OS_DEV="/dev/"$OS_DEV""
        
fdisk $OS_DEV >/dev/null 2>&1 <<EOF
n
p
1

            
            
w


EOF

        sleep 1
        OS_ROOTFS_DEV=""$OS_DEV"1"
        echo $OS_ROOTFS_DEV > OS_DEV.txt
        mkfs.ext4 -L "$GV_OS_LABEL" $OS_ROOTFS_DEV >/dev/null 2>&1
        func_check_error $? "Can not create os filesystem."
        sleep 1
    else
        DATA_DEV=${NO_RAID_DEV[$COUNT_I]}
        DATA_DEV="/dev/"$DATA_DEV""
fdisk $DATA_DEV >/dev/null 2>&1 <<EOF
n
p
1

            
            
w


EOF
        sleep 1
        DATA_DEV=""$DATA_DEV"1"
        mkfs.ext4 -L "$NO_RAID_LABEL" $DATA_DEV >/dev/null 2>&1
        func_check_error $? "Can not create data filesystem."
        sleep 1
        DATA_DRV_COUNT=$DATA_DRV_COUNT+1 
    fi
done

exit $RESULT
