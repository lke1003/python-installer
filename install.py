#! /usr/bin/env python3

import locale
import sys, os, os.path, time, string, subprocess, logging
from dialog import Dialog


# This is almost always a good thing to do at the beginning of your programs.
locale.setlocale(locale.LC_ALL, '')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='install.log', level=logging.DEBUG)


flashDir="/flash"
diskDir="/disk"

SG_MAP_INSTALL_USB_NAME="opf-installer"

GV_FLASH_P1_LABEL="Prom_fp1"
GV_FLASH_P2_LABEL="Prom_sys"

MSG_NO_DOM="Please insert one DOM (Media) for installation"
GV_USB_INSTALL_PART=""
GV_USB_INSTALL_DEV=""
DD_FLASH_DEV=""
GV_NUMBER_OF_HDD=0
SELECTED_RAID_MODE=""
INSTALL_DEVICE=1
SCRIPT_PARTITION_RENAME="./partition_rename.sh "
SCRIPT_CREATE_FLASH_PARTITION="./create_flash_partition.sh "
SCRIPT_CREATE_FLASH_FILESYSTEM="./create_flash_filesystem.sh "
SCRIPT_WAIT_I2="./wait_i2.sh "
SCRIPT_MOUNT_ROOTFS="./mount_rootfs.sh "


def handle_exit_code(d, code):
  if code in (d.DIALOG_CANCEL, d.DIALOG_ESC):
    if code == d.DIALOG_CANCEL:
        msg = "You chose cancel in the last dialog box. Do you want to " \
              "exit this installation?"
    else:
        msg = "You pressed ESC in the last dialog box. Do you want to " \
              "exit this installation?"
    # "No" or "ESC" will bring the user back to the demo.
    # DIALOG_ERROR is propagated as an exception and caught in main().
    # So we only need to handle OK here.
    if d.yesno(msg, width=100) == d.DIALOG_OK:
        sys.exit(0)
    return 0
  else:
    return 1
  
def device_menu(d):
  while 1: 
      code, tags=d.menu("Please choose a device to install OS.",
            width=80,
            choices=[("1", "Internal Flash. (default)"), 
                     ("2", " Hard Disk Drive.")])
      if tags == "2":
        if check_number_of_hdd() == 0:
          d.msgbox("Please insert HDD for install OS", width=80)
          continue
        get_raid_mode_table(d)
      if handle_exit_code(d, code):
        break
  return tags

def full_install_confirm(d):
  if d.yesno("Clean All and Full Install") == d.OK:
    if d.yesno("All of Data in HDD will be replaced.") == d.OK:
      return True
    else:
      return False
  else:
    return False

def get_raid_mode_table(d):
  #RMT_COUNT="PD_COUNT="+str(GV_NUMBER_OF_HDD)
  RMT_COUNT="PD_COUNT="+str(4)
  no=0
  LIST_MODE_RESULT=[]
  LIST_DEFAULT=False
  global SELECTED_RAID_MODE 
  cmd="cat raid_mode_table | grep {0}\":\" | ".format(RMT_COUNT)
  cmd=cmd+"awk '{print $2}' | sed 's/DF=//g'"
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  DF_RAID_MODE=output.stdout.rstrip()

  cmd="cat raid_mode_table | grep {0}\":\" | ".format(RMT_COUNT)
  cmd=cmd+"awk '{print $3}' | sed 's/,/ /g'"
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  LIST_RAID_MODE=output.stdout.rstrip()
  LIST_RAID_MODE=LIST_RAID_MODE.split(" ")
  for mode in LIST_RAID_MODE:
    no+=1
    if(no == 1):
      LIST_DEFAULT = True
    else:
      LIST_DEFAULT = False
    LIST_MODE_RESULT.append([str(no), mode, LIST_DEFAULT])

  while 1:               
    SELECTED_RAID_MODE = radio_list_raid_mode(d, LIST_MODE_RESULT)
    if d.yesno("Did you select "+ SELECTED_RAID_MODE) == d.OK:
      break


def radio_list_raid_mode(d, Raid_MODE):
  while 1:
    code, tag=d.radiolist("Please select the raid mode",
                          width = 65,
                          choices=Raid_MODE)
    if handle_exit_code(d, code):
      break
  return Raid_MODE[int(tag)-1][1]
  

#Check Directory exist or not, otherwise create for intaller
def check_dir(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs( dir_path, 0o755 )

def check_number_of_hdd():
  global GV_NUMBER_OF_HDD
  GV_NUMBER_OF_HDD=0
  cmd="clitest -u administrator -p password -C phydrv | grep Slot | awk '{print $1}'"
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)

  for no in output.stdout:
    if(no!="\n"):
      GV_NUMBER_OF_HDD += 1
  return GV_NUMBER_OF_HDD


def set_param():
  global GV_USB_INSTALL_PART
  global GV_USB_INSTALL_DEV
  cmd="blkid | grep -E /dev/sd.*{0} ".format(SG_MAP_INSTALL_USB_NAME)
  cmd=cmd + "| awk '{print $1}' | sed 's/://g'"
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  GV_USB_INSTALL_PART = output.stdout.rstrip()
  cmd="echo {0} | sed 's/.$//g'".format(GV_USB_INSTALL_PART)
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  GV_USB_INSTALL_DEV=output.stdout.rstrip()
  global DD_FLASH_DEV
  DD_FLASH_DEV=get_flash_dev()
  check_dir(flashDir)
  check_dir(diskDir)

def check_dom_is_exist():
  cmd="sg_map -i | grep -E -v \"{0}|/dev/sr|Promise\" | wc -l".format(GV_USB_INSTALL_DEV)
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  if output.stdout.rstrip() == "0" :
    return False
  else:
    return True

def get_flash_dev():
  FLASH_DEV=""
  cmd="sg_map -i | grep -E -v \"{0}|/dev/sr|Promise\"".format(GV_USB_INSTALL_DEV)
  cmd=cmd+"| awk '{print $2}'"
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  FLASH_DEV=output.stdout.rstrip()
  return FLASH_DEV

def log_param():
  logging.debug("-------------------------Global Parameter--------------------")
  logging.debug("SG_MAP_INSTALL_USB_NAME="+SG_MAP_INSTALL_USB_NAME)
  logging.debug("GV_FLASH_P1_LABEL="+GV_FLASH_P1_LABEL)
  logging.debug("GV_FLASH_P2_LABEL="+GV_FLASH_P2_LABEL)
  logging.debug("GV_USB_INSTALL_PART="+GV_USB_INSTALL_PART)
  logging.debug("GV_USB_INSTALL_DEV="+GV_USB_INSTALL_DEV)
  logging.debug("DD_FLASH_DEV="+DD_FLASH_DEV)
  logging.debug("SELECTED_RAID_MODE="+SELECTED_RAID_MODE)
  logging.debug("SCRIPT_PARTITION_RENAME="+SCRIPT_PARTITION_RENAME)
  logging.debug("SCRIPT_CREATE_FLASH_PARTITION="+SCRIPT_CREATE_FLASH_PARTITION)
  logging.debug("SCRIPT_CREATE_FLASH_FILESYSTEM="+SCRIPT_CREATE_FLASH_FILESYSTEM)
  logging.debug("INSTALL_DEVICE="+INSTALL_DEVICE)
  logging.debug("-------------------------Global Parameter End--------------------")

def poweroff_msg(d, msg):
  d.msgbox("{0}\n\nPress 'OK' to Shutdown".format(msg),
        width=80,)
  #os.system("shutdown now -h")

def full_install(d):
  d.gauge_start("Flash Partition Rename", title="Starting Install")  
  partition_rename()
  time.sleep(3) 
  d.gauge_update(5, "Create Flash Partition", update_text=1)  
  create_flash_partition()
  time.sleep(3) 
  d.gauge_update(10, "Create Flash FileSystem", update_text=1) 
  create_flash_filesystem()
  time.sleep(3) 
  d.gauge_update(20, "Mount Disk", update_text=1) 
  mount_disk()
  d.gauge_stop() 

def partition_rename():
  logging.info("---------------------Flash Partition Rename---------------------")
  cmd=SCRIPT_PARTITION_RENAME + GV_FLASH_P2_LABEL
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)

def create_flash_partition():
  logging.info("---------------------Create Flash Partition---------------------")
  cmd=SCRIPT_CREATE_FLASH_PARTITION + DD_FLASH_DEV
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)

def create_flash_filesystem():
  logging.info("---------------------Create Flash FileSystem---------------------")
  if INSTALL_DEVICE == "1": 
    INSTALL_OS_TO_FLASH = " 0"
  else:
    INSTALL_OS_TO_FLASH = " 1"
  cmd=SCRIPT_CREATE_FLASH_FILESYSTEM + GV_FLASH_P1_LABEL + " " + GV_FLASH_P2_LABEL + " " + DD_FLASH_DEV + INSTALL_OS_TO_FLASH
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)

def mount_disk():
  logging.info("---------------------Mount Disk---------------------")
  cmd=SCRIPT_MOUNT_ROOTFS + DD_FLASH_DEV + " " + GV_USB_INSTALL_PART + " " + diskDir
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)

def wait_i2():
  logging.info("---------------------Wait I2--------------------")
  cmd=SCRIPT_WAIT_I2
  logging.debug(cmd)
  output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

def main():
  logging.info('Start Installer')
  wait_i2()
  d = Dialog(dialog="dialog")
  d.set_background_title("Welcome to Promise Storage Appliance target installation version: 1.0")
  set_param()
  if check_dom_is_exist() != True:
    poweroff_msg(d, MSG_NO_DOM)
  global INSTALL_DEVICE
  INSTALL_DEVICE=device_menu(d)  # 1 = install on flash, 2 = install on HDD
  if full_install_confirm(d) == True:
    log_param()
    full_install(d)
  else:
    if d.yesno("Shutdown?") == d.OK:
      poweroff_msg(d, "")
    else:
      main()

if __name__ == '__main__':
  main()
