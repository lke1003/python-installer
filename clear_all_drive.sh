#!/bin/bash

RESULT=0
export SW_CONF_PATH=/opt/flash/sw/confusr
export OEM_PATH=/opt/flash/sw/oem

export PATH=$PATH:/opt/flash/sw/bin
echo 3 > /proc/sys/kernel/printk

func_check_error()
{
    if [ $1 != 0 ]; then
        echo $2 >> fullinstall.log
        RESULT=1
    fi
}

echo "################# Clear all Drive ########################" >> fullinstall.log
ivconfig -ca >/dev/null 2>&1 
func_check_error $? "Del array error."
sleep 1

SPARE_LD=$(clitest -u administrator -p password -C spare | awk '{print $1}'|grep '[0-9]')

if [ "$SPARE_LD" != "" ]; then
    for SLD in $SPARE_LD
    do
        clitest -u administrator -p password -C spare -a del -i $SLD >/dev/null 2>&1
        func_check_error $? "Del spare error."
    done
fi
sleep 2

STALE_PD=$(clitest -u administrator -p password -C phydrv |grep Stale |awk '{print $1}')

if [ "$STALE_PD" != "" ]; then
    for SPD in $STALE_PD
    do
        clitest -u administrator -p password -C phydrv -a clear -t staleconfig -p $SPD >/dev/null 2>&1
        func_check_error $? "Del staleconf error."
    done
fi
sleep 2

PFA_PD=$(clitest -u administrator -p password -C phydrv |grep "PFA" |grep -v "Not usable"|awk '{print $1}')

if [ "$PFA_PD" != "" ]; then
    for PFAPD in $PFA_PD
    do
        clitest -u administrator -p password -C phydrv -a clear -t pfa -p $PFAPD >/dev/null 2>&1
        func_check_error $? "Del pfa error."
    done
fi
sleep 2

ivconfig -ca >/dev/null 2>&1
func_check_error $? "Del array error."
sleep 4

exit $RESULT
