#!/bin/bash

SCRIPT_DIR=$(dirname $0)
SCRIPT_DIR=$(realpath $SCRIPT_DIR)
PKG_DIR=$SCRIPT_DIR

######################################################################

OPF_DISTRIBUTION=%OPF_DISTRIBUTION%
KERNEL_VERSION=%KERNEL_VERSION%
KERNEL_PKG=linux-image-$KERNEL_VERSION.deb
FW_PKG_DIR=VA3340-FW-$OPF_DISTRIBUTION
FW_PKG=$FW_PKG_DIR.tar.gz
THIRD_PARTY_PKG_DIR=VA3340-3P-$OPF_DISTRIBUTION
THIRD_PARTY_PKG=$THIRD_PARTY_PKG_DIR.tar.gz
SW_PKG_DIR=VA3340-SW-$OPF_DISTRIBUTION
SW_PKG=$SW_PKG_DIR.tar.gz
UTILS_PKG_DIR=VA3340-UTILS-$OPF_DISTRIBUTION
UTILS_PKG=$UTILS_PKG_DIR.tar.gz

PROC_MOUNTED=0

######################################################################

clean_up() {
    if [ $PROC_MOUNTED -ne 0 ]; then
        umount_proc
    fi
}

# check execution results
check_result() {
    RESULT=$1
    FAIL_MSG=$2

    if [ x"$RESULT" != "x0" ]; then
        echo "*** $FAIL_MSG ***"
        clean_up
        exit 1
    fi
}

mount_proc() {
    [ -d $TGT_ROOT/proc ] || mkdir -p $TGT_ROOT/proc
    mount --bind /proc $TGT_ROOT/proc
    check_result $? "Failed to mount $TGT_ROOT/proc"
    [ -d $TGT_ROOT/dev ] || mkdir -p $TGT_ROOT/dev
    mount --bind /dev $TGT_ROOT/dev
    check_result $? "Failed to mount $TGT_ROOT/dev"
    [ -d $TGT_ROOT/sys ] || mkdir -p $TGT_ROOT/sys
    mount --bind /sys $TGT_ROOT/sys
    check_result $? "Failed to mount $TGT_ROOT/sys"
    PROC_MOUNTED=1
}

umount_proc() {
    mount | grep -q "$TGT_ROOT/proc" && umount $TGT_ROOT/proc
    mount | grep -q "$TGT_ROOT/dev" && umount $TGT_ROOT/dev
    mount | grep -q "$TGT_ROOT/sys/fs/fuse/connections" && umount $TGT_ROOT/sys/fs/fuse/connections
    mount | grep -q "$TGT_ROOT/sys" && umount $TGT_ROOT/sys
    PROC_MOUNTED=0
}

install_kernel() {
    cp $PKG_DIR/$KERNEL_PKG $TGT_ROOT/ && \
    chroot $TGT_ROOT dpkg -i $KERNEL_PKG
    check_result $? "Failed to install kernel!"
    rm -rf $TGT_ROOT/$KERNEL_PKG
}

install_fw() {
    tar xzf $PKG_DIR/$FW_PKG -C $TGT_ROOT && \
    chroot $TGT_ROOT /$FW_PKG_DIR/install.sh
    check_result $? "Failed to install FW!"
    chroot $TGT_ROOT /$FW_PKG_DIR/setup_evtlog_conf.sh $TGT_DEV
    check_result $? "Failed to setup evtlog config!"
    rm -rf $TGT_ROOT/$FW_PKG_DIR
}

setup_grub_cfg() {
    cp $PKG_DIR/grub.cfg $TGT_ROOT/boot/grub/
    check_result $? "Failed to setup $TGT_ROOT/boot/grub/grub.cfg"
}

install_sw() {
    tar xzf $PKG_DIR/$THIRD_PARTY_PKG -C $TGT_ROOT && \
    chroot $TGT_ROOT /$THIRD_PARTY_PKG_DIR/install.sh
    check_result $? "Failed to install 3rd Party packages!"
    rm -rf $TGT_ROOT/$THIRD_PARTY_PKG_DIR

    tar xzf $PKG_DIR/$SW_PKG -C $TGT_ROOT && \
    chroot $TGT_ROOT /$SW_PKG_DIR/install.sh 1
    check_result $? "Failed to install SW!"
    rm -rf $TGT_ROOT/$SW_PKG_DIR

    tar xzf $PKG_DIR/$UTILS_PKG -C $TGT_ROOT && \
    chroot $TGT_ROOT /$UTILS_PKG_DIR/install.sh
    check_result $? "Failed to install utils!"
    rm -rf $TGT_ROOT/$UTILS_PKG_DIR
}

adjust_os_install() {
    # disable "suspend/hibernate"
    cp $PKG_DIR/conf/org.freedesktop.login1.policy $TGT_ROOT/usr/share/polkit-1/actions/ && \
    chown root.root $TGT_ROOT/usr/share/polkit-1/actions/org.freedesktop.login1.policy && \
    chmod 644 $TGT_ROOT/usr/share/polkit-1/actions/org.freedesktop.login1.policy && \
    cp $PKG_DIR/conf/com.ubuntu.desktop.pkla $TGT_ROOT/var/lib/polkit-1/localauthority/10-vendor.d/ && \
    chown root.root $TGT_ROOT/var/lib/polkit-1/localauthority/10-vendor.d/com.ubuntu.desktop.pkla && \
    chmod 644 $TGT_ROOT/var/lib/polkit-1/localauthority/10-vendor.d/com.ubuntu.desktop.pkla
    check_result $? "Failed to disable suspend/hibernate!"

    # Adjust dhcp timeout
    sed -i "s/^timeout .*;$/timeout 10;/g" $TGT_ROOT/etc/dhcp/dhclient.conf
    check_result $? "Failed to change dhcp timeout!"

    # rename NICs
    MAC0=`cat /sys/class/net/*/address | sort | sed -n '2p'`
    MAC1=`cat /sys/class/net/*/address | sort | sed -n '$p'`

    [ x"$MAC0" != "x" ] && \
    [ x"$MAC1" != "x" ] && \
    cp $PKG_DIR/conf/60-net.rules $TGT_ROOT/etc/udev/rules.d/ && \
    chown root.root $TGT_ROOT/etc/udev/rules.d/60-net.rules && \
    chmod 644 $TGT_ROOT/etc/udev/rules.d/60-net.rules && \
    sed -i "s/MACADDR0/$MAC0/" $TGT_ROOT/etc/udev/rules.d/60-net.rules && \
    sed -i "s/MACADDR1/$MAC1/" $TGT_ROOT/etc/udev/rules.d/60-net.rules
    check_result $? "Failed to rename NICs!"

    # Default network setup
    cp $PKG_DIR/conf/interfaces $TGT_ROOT/etc/network/ && \
    chown root.root $TGT_ROOT/etc/network/interfaces && \
    chmod 644 $TGT_ROOT/etc/network/interfaces
    check_result $? "Failed to copy interfaces to /etc/network/!"

    # copy build_ver.h to $TGT_ROOT/opt/flash/version
    cp $PKG_DIR/build_ver.h $TGT_ROOT/opt/flash/version/
    check_result $? "Failed to copy build_ver.h!"

    # disable ubuntu auto update
    cp $PKG_DIR/conf/apt.conf.d/10periodic $TGT_ROOT/etc/apt/apt.conf.d/ && \
    cp $PKG_DIR/conf/apt.conf.d/20auto-upgrades $TGT_ROOT/etc/apt/apt.conf.d/ && \
    cp $PKG_DIR/conf/apt.conf.d/99update-notifier $TGT_ROOT/etc/apt/apt.conf.d/ && \
    chown -R root.root $TGT_ROOT/etc/apt/apt.conf.d && \
    chmod -R 644 $TGT_ROOT/etc/apt/apt.conf.d && \
    chroot $TGT_ROOT /usr/bin/dbus-launch --exit-with-session /usr/bin/gsettings set com.ubuntu.update-notifier no-show-notifications true
    check_result $? "Failed to disable ubuntu auto update!"

    # copy manual, icon and shortcut link
    cp -r $PKG_DIR/conf/manual $TGT_ROOT/opt/flash/
    check_result $? "Failed to copy manual!"

    cp -r $PKG_DIR/conf/icon $TGT_ROOT/opt/flash/sw/
    check_result $? "Failed to copy icon!"

    cp -r $PKG_DIR/conf/shortcut/. $TGT_ROOT/home/administrator/Desktop
    check_result $? "Failed to copy shortcut!"

    [ -d $TGT_ROOT/etc/skel/Desktop ] || mkdir -p $TGT_ROOT/etc/skel/Desktop
    cp -r $PKG_DIR/conf/shortcut/. $TGT_ROOT/etc/skel/Desktop
    check_result $? "Failed to copy shortcut to global Desktop for all user"
}

######################################################################

if [ $# -lt 2 ]; then
    echo "Usage: $0 TARGET_ROOT TARGET_DEV"
    exit 1
fi
TGT_ROOT=$1
TGT_DEV=$2

if [ ! -d $TGT_ROOT ]; then
    echo "$TGT_ROOT is not a valid target!"
    exit 1
fi

echo "*** Mount proc, dev and sys ***"
mount_proc

echo "*** Install kernel ***"
install_kernel

echo "*** Install FW ***"
install_fw

echo "*** Setup grub.cfg ***"
setup_grub_cfg

echo "*** Install SW ***"
install_sw

echo "*** Adjust OS installation ***"
adjust_os_install

echo "*** Umount proc, dev and sys ***"
umount_proc
