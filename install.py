#! /usr/bin/env python3

import locale
import sys, os, os.path, time, string, subprocess, logging, threading
from dialog import Dialog


# This is almost always a good thing to do at the beginning of your programs.
locale.setlocale(locale.LC_ALL, '')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='install.log', level=logging.DEBUG)


flashDir="/flash"
diskDir="/disk"

SG_MAP_INSTALL_USB_NAME="opf-installer"

GV_FLASH_P1_LABEL="Prom_fp1"
GV_FLASH_P2_LABEL="Prom_sys"
GV_FLASH_P3_LABEL="Prom_log"
GV_BACKUP_LABEL="Prom_backup"
GV_OS_LABEL=GV_FLASH_P2_LABEL
GV_DATA_LABEL="Prom_data"

MSG_NO_DOM="Please insert one DOM (Media) for installation"
GV_USB_INSTALL_PART=""
GV_USB_INSTALL_DEV=""
DD_FLASH_DEV=""
GV_NUMBER_OF_HDD=0
SELECTED_RAID_MODE="KEEP_DATA"
INSTALL_DEVICE=1
STATUS_ISSUCCESS=True
FAIL_PROGRESS=""

SCRIPT_PARTITION_RENAME="cd /prom-pkg/ ; ./partition_rename.sh "
SCRIPT_CREATE_FLASH_PARTITION="cd /prom-pkg/ ; ./create_flash_partition.sh "
SCRIPT_WAIT_I2="cd /prom-pkg/ ; ./wait_i2.sh "
SCRIPT_MOUNT_ROOTFS="cd /prom-pkg/ ; ./mount_rootfs.sh "
SCRIPT_COPY_ROOTFS="cd /prom-pkg/ ; ./copy_rootfs.sh "
SCRIPT_GRUB_INSTALL="cd /prom-pkg/ ; ./grub_install.sh "
SCRIPT_CLEAR_ALL_DRIVE="cd /prom-pkg/ ; ./clear_all_drive.sh "
SCRIPT_CREATE_NO_RAID_HDD_PARTITION="cd /prom-pkg/ ; ./create_no_raid_hdd_partition.sh "
SCRIPT_CREATE_RAID_HDD_PARTITION="cd /prom-pkg/ ; ./create_raid_hdd_partition.sh "
SCRIPT_CREATE_GRUB_FLASH_PARTITION="cd /prom-pkg/ ; ./create_grub_flash_partition.sh "
SCRIPT_CREATE_NO_RAID_DATA_PARTITION="cd /prom-pkg/ ; ./create_no_raid_data_partition.sh "
SCRIPT_CREATE_RAID_DATA_PARTITION="cd /prom-pkg/ ; ./create_raid_data_partition.sh "
progress_list=[["partition_rename", 7], ["create_flash_partition", 7], ["clear_all_drive", 7], ["hdd_partition", 7], ["mount_disk", 7], ["copy_rootfs", 7], ["grub_install", 7]]

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
      if tags == "1" and check_number_of_hdd() > 0:
        get_raid_mode_table(d, tags)
      if tags == "2":
        if check_number_of_hdd() == 0:
          d.msgbox("Please insert HDD for install OS", width=80)
          continue
        get_raid_mode_table(d, tags)
      if handle_exit_code(d, code):
        break
  return tags

def full_install_confirm(d):
  if d.yesno("Clean All and Full Install") == d.OK:
    if INSTALL_DEVICE == "2":
      if d.yesno("All of Data in HDD will be replaced.") == d.OK:
        return True
      else:
        return False
    return True
  else:
    return False

def get_raid_mode_table(d, device_tags):
  while 1:
    RMT_COUNT="PD_COUNT="+str(GV_NUMBER_OF_HDD)
    no=0
    LIST_MODE_RESULT=[]
    LIST_DEFAULT=False
    global SELECTED_RAID_MODE 
    cmd="cat /prom-pkg/raid_mode_table | grep {0} | ".format(RMT_COUNT)
    cmd=cmd+"awk '{print $2}' | sed 's/DF=//g'"
    output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
    if device_tags != "1":
      DF_RAID_MODE=output.stdout.rstrip()
    else:
      DF_RAID_MODE="KEEP_DATA"

    cmd="cat /prom-pkg/raid_mode_table | grep {0} | ".format(RMT_COUNT)
    cmd=cmd+"awk '{print $3}' | sed 's/,/ /g'"
    output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
    LIST_RAID_MODE=output.stdout.rstrip()
    LIST_RAID_MODE=LIST_RAID_MODE.split(" ")
    message="Select RAID Mode in 20s \n\nDefault: {0} \n\nPress Enter to use Default Configuration\n\nPress Cancel to Select RAID Mode".format(DF_RAID_MODE)

    if d.pause(message, seconds=20) == d.CANCEL:
      if device_tags=="1":
        LIST_MODE_RESULT.append([str(0), "KEEP_DATA", True])
      for mode in LIST_RAID_MODE:
        no+=1
        if(no == 1):
          LIST_DEFAULT = True
        else:
          LIST_DEFAULT = False
        LIST_MODE_RESULT.append([str(no), mode, LIST_DEFAULT])
              
      SELECTED_RAID_MODE = radio_list_raid_mode(d, LIST_MODE_RESULT)
      if d.yesno("Did you select "+ SELECTED_RAID_MODE) == d.OK:
        break
    else:
      SELECTED_RAID_MODE = DF_RAID_MODE
      if d.yesno("Did you select "+ SELECTED_RAID_MODE) == d.OK:
        break



def radio_list_raid_mode(d, Raid_MODE):
  while 1:
    code, tag=d.radiolist("Please select the raid mode",
                          width = 65,
                          choices=Raid_MODE)
  
    if handle_exit_code(d, code):
      break
  if Raid_MODE[0][0] == "0":
    logging.debug(Raid_MODE)
    logging.debug(Raid_MODE[int(tag)][1]) 
    return Raid_MODE[int(tag)][1]
  else:
    logging.debug(Raid_MODE)
    logging.debug(Raid_MODE[int(tag)-1][1]) 
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
  if os.path.exists("progress.txt") == True:
    os.remove("progress.txt")


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
  logging.debug("-------------------------Global Variable--------------------")
  logging.debug("SG_MAP_INSTALL_USB_NAME="+SG_MAP_INSTALL_USB_NAME)
  logging.debug("GV_FLASH_P1_LABEL="+GV_FLASH_P1_LABEL)
  logging.debug("GV_FLASH_P2_LABEL="+GV_FLASH_P2_LABEL)
  logging.debug("GV_BACKUP_LABEL="+GV_BACKUP_LABEL)
  logging.debug("GV_OS_LABEL="+GV_OS_LABEL)
  logging.debug("GV_DATA_LABEL="+GV_DATA_LABEL)
  logging.debug("GV_USB_INSTALL_PART="+GV_USB_INSTALL_PART)
  logging.debug("GV_USB_INSTALL_DEV="+GV_USB_INSTALL_DEV)
  logging.debug("DD_FLASH_DEV="+DD_FLASH_DEV)
  logging.debug("GV_NUMBER_OF_HDD="+str(GV_NUMBER_OF_HDD))
  logging.debug("SELECTED_RAID_MODE="+SELECTED_RAID_MODE)
  logging.debug("INSTALL_DEVICE="+INSTALL_DEVICE)
  logging.debug("-------------------------SCRIPT FILE NAME--------------------")
  logging.debug("SCRIPT_PARTITION_RENAME="+SCRIPT_PARTITION_RENAME)
  logging.debug("SCRIPT_CREATE_FLASH_PARTITION="+SCRIPT_CREATE_FLASH_PARTITION)
  logging.debug("SCRIPT_WAIT_I2="+SCRIPT_WAIT_I2)
  logging.debug("SCRIPT_MOUNT_ROOTFS="+SCRIPT_MOUNT_ROOTFS)
  logging.debug("SCRIPT_COPY_ROOTFS="+SCRIPT_COPY_ROOTFS)
  logging.debug("SCRIPT_GRUB_INSTALL="+SCRIPT_GRUB_INSTALL)
  logging.debug("SCRIPT_CLEAR_ALL_DRIVE="+SCRIPT_CLEAR_ALL_DRIVE)
  logging.debug("SCRIPT_CREATE_NO_RAID_HDD_PARTITION="+SCRIPT_CREATE_NO_RAID_HDD_PARTITION)
  logging.debug("SCRIPT_CREATE_RAID_HDD_PARTITION="+SCRIPT_CREATE_RAID_HDD_PARTITION)
  logging.debug("SCRIPT_CREATE_GRUB_FLASH_PARTITION="+SCRIPT_CREATE_GRUB_FLASH_PARTITION)
  logging.debug("------------------------- End --------------------")

def poweroff_msg(d, msg):
  d.msgbox("{0}\n\nPress 'OK' to Shutdown".format(msg),
        width=80)
  os.system("shutdown now -h")

def full_install():
  global STATUS_ISSUCCESS
  if partition_rename() == False:
    STATUS_ISSUCCESS = False
    return
  time.sleep(3) 
  if create_flash_partition() == False:
    STATUS_ISSUCCESS = False
    return
  time.sleep(3) 
  if SELECTED_RAID_MODE != "KEEP_DATA":   #Create DATA Drive in RAID
    if clear_all_drive() == False:
      STATUS_ISSUCCESS = False
      return
    time.sleep(5) 
    if SELECTED_RAID_MODE == "NO_RAID":
      if create_no_raid_data_partition() == False:
        STATUS_ISSUCCESS = False
        return
    else:
      if create_raid_data_partition() == False:
        STATUS_ISSUCCESS = False
        return
    time.sleep(3) 
  if mount_disk() == False:
    STATUS_ISSUCCESS = False
    return
  time.sleep(3)
  if copy_rootfs() == False:
    STATUS_ISSUCCESS = False
    return
  if grub_install() == False:
    STATUS_ISSUCCESS = False
    return


def full_install_HDD():
  global STATUS_ISSUCCESS
  if partition_rename() == False:
    STATUS_ISSUCCESS = False
    return
  time.sleep(3)
  if create_grub_flash_partition() == False:
    STATUS_ISSUCCESS = False
    return
  time.sleep(3) 
  if clear_all_drive() == False:
    STATUS_ISSUCCESS = False
    return
  if SELECTED_RAID_MODE=="NO_RAID":
    if create_no_raid_hdd_partition() == False:
      STATUS_ISSUCCESS = False
      return
  else:
    if create_raid_hdd_partition() == False:
      STATUS_ISSUCCESS = False
      return
  if mount_disk() == False:
    STATUS_ISSUCCESS = False
    return
  time.sleep(3)
  if copy_rootfs() == False:
    STATUS_ISSUCCESS = False
    return
  if grub_install() == False:
    STATUS_ISSUCCESS = False
    return

def write_progress(task, status):
  f=open("progress.txt","a+")
  line="{0} {1} \n".format(task, status) 
  f.write(line)
  f.close()

def partition_rename():
  logging.info("---------------------Flash Partition Rename---------------------")
  cmd=SCRIPT_PARTITION_RENAME + GV_FLASH_P2_LABEL
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("partition_rename", "Fail")
    return False
  else:
    write_progress("partition_rename", "done")
    return True

def create_flash_partition():
  logging.info("---------------------Create Flash Partition---------------------")
  cmd=SCRIPT_CREATE_FLASH_PARTITION + GV_FLASH_P1_LABEL + " " + GV_FLASH_P2_LABEL + " " + GV_FLASH_P3_LABEL +" " + DD_FLASH_DEV 
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("create_flash_partition", "Fail")
    return False
  else:
    write_progress("create_flash_partition", "done")
    return True


def mount_disk():
  logging.info("---------------------Mount Disk---------------------")
  if INSTALL_DEVICE == "1":
    OS_ROOTFS_DEV=DD_FLASH_DEV + "2"
    OS_VAR_DEV=DD_FLASH_DEV + "3"
  elif INSTALL_DEVICE == "2":
    #Get correct OS dev name
    fd=open("/prom-pkg/OS_DEV.txt")
    OS_ROOTFS_DEV=fd.readline().rstrip()
    fd.close()
    OS_VAR_DEV=DD_FLASH_DEV + "2"
  cmd=SCRIPT_MOUNT_ROOTFS + DD_FLASH_DEV + " " + OS_ROOTFS_DEV + " " + OS_VAR_DEV + " " + GV_USB_INSTALL_PART + " " + diskDir
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if os.path.exists("/prom-pkg/OS_DEV.txt"):
    os.remove("/prom-pkg/OS_DEV.txt")
  if output != 0:
    write_progress("mount_disk", "Fail")
    return False
  else:
    write_progress("mount_disk", "done")
    return True

def copy_rootfs():
  logging.info("---------------------Copy Rootfs---------------------")
  cmd=SCRIPT_COPY_ROOTFS + diskDir + " " + DD_FLASH_DEV + " " + GV_OS_LABEL + " " + GV_BACKUP_LABEL + " " + GV_FLASH_P1_LABEL + " " + GV_FLASH_P3_LABEL
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("copy_rootfs", "Fail")
    return False
  else:
    write_progress("copy_rootfs", "done")
    return True

def grub_install():
  logging.info("---------------------Grub Install---------------------")
  cmd=SCRIPT_GRUB_INSTALL + DD_FLASH_DEV 
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("grub_install", "Fail")
    return False
  else:
    write_progress("grub_install", "done")
    return True

def clear_all_drive():
  logging.info("---------------------Clear All Drive---------------------")
  cmd=SCRIPT_CLEAR_ALL_DRIVE
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("clear_all_drive", "Fail")
    return False
  else:
    write_progress("clear_all_drive", "done")
    return True

def create_no_raid_data_partition():
  logging.info("---------------------Create No Raid data Partition---------------------")
  cmd=SCRIPT_CREATE_NO_RAID_DATA_PARTITION + GV_DATA_LABEL
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("hdd_partition", "Fail")
    return False
  else:
    write_progress("hdd_partition", "done")
    return True

def create_no_raid_hdd_partition():
  logging.info("---------------------Create No Raid HDD Partition---------------------")
  cmd=SCRIPT_CREATE_NO_RAID_HDD_PARTITION + GV_OS_LABEL + " " + GV_DATA_LABEL 
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("hdd_partition", "Fail")
    return False
  else:
    write_progress("hdd_partition", "done")
    return True

def create_raid_hdd_partition():
  logging.info("---------------------Create Raid HDD Partition---------------------")
  cmd=SCRIPT_CREATE_RAID_HDD_PARTITION + SELECTED_RAID_MODE + " " + GV_OS_LABEL + " " + GV_DATA_LABEL
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("hdd_partition", "Fail")
    return False
  else:
    write_progress("hdd_partition", "done")
    return True

def create_raid_data_partition():
  logging.info("---------------------Create Raid Data Partition---------------------")
  cmd=SCRIPT_CREATE_RAID_DATA_PARTITION + SELECTED_RAID_MODE +  " " + GV_DATA_LABEL
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("hdd_partition", "Fail")
    return False
  else:
    write_progress("hdd_partition", "done")
    return True

def create_grub_flash_partition():
  logging.info("---------------------Create Grub Flash Partition---------------------")
  cmd=SCRIPT_CREATE_GRUB_FLASH_PARTITION + GV_FLASH_P1_LABEL + " " + GV_FLASH_P3_LABEL + " " + DD_FLASH_DEV 
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)
  if output != 0:
    write_progress("create_flash_partition", "Fail")
    return False
  else:
    write_progress("create_flash_partition", "done")
    return True

def wait_i2():
  logging.info("---------------------Wait I2--------------------")
  cmd=SCRIPT_WAIT_I2
  logging.debug(cmd)
  output = os.system(cmd)
  logging.debug(output)

def thread_install():
  if INSTALL_DEVICE == "1":
    full_install()
  elif INSTALL_DEVICE == "2":
    full_install_HDD()

def count_file():
  n = 0
  for r, d, files in os.walk('/disk'):
    n+= len(files)
  return n

def check_UI(d):
  global progress_list
  global FAIL_PROGRESS
  i=0
  total_file=121029
  rootfs_percent=0
  if SELECTED_RAID_MODE == "KEEP_DATA":
    progress_list[2][1] = 6 
    progress_list[3][1] = 6 
  while 1:
      if progress_list[i][1] == 7 or progress_list[i][1] <= 0:
          task=progress_list[i][0]
          if progress_list[i][0]=="copy_rootfs":
              number_files = count_file()
              rootfs_percent=number_files / total_file
              task_percent=round(rootfs_percent * 100)
              logging.debug(task_percent) 
              if int(task_percent) == 0:
                  task_percent = 1
              progress_list[i][1] = -min(task_percent, 99)
              logging.debug(progress_list) 
          cmd="cat progress.txt | grep {0} ".format(task)
          cmd=cmd+"|awk '{print $2}'"
          output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
          if output.stdout.rstrip()=="done":
              progress_list[i][1]=3
              i+=1
          elif output.stdout.rstrip()=="Fail":
              progress_list[i][1]=1
              i+=1
              FAIL_PROGRESS=progress_list[i][0]
              return
      elif progress_list[i][1] == 6:
          i+=1
      percentage = min(min(round( i * 3 + 80 * rootfs_percent), 98), 99)
      if i < 6:
         print_progress = progress_list[i][0]
      else:
         print_progress = "Finish"  
      d.mixedgauge(print_progress, title="Installing", percent=percentage, elements=progress_list)
      time.sleep(2)
      if progress_list[6][1] == 3 :
         return

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
    t = threading.Thread(target = thread_install)
    t.start()
    check_UI(d)
    t.join() 
    if STATUS_ISSUCCESS:
      poweroff_msg(d, "Finish Installation")
    else:
      message=FAIL_PROGRESS + " Fail"
      poweroff_msg(d, message)
  else:
    if d.yesno("Shutdown?") == d.OK:
      poweroff_msg(d, "")
    else:
      main()

if __name__ == '__main__':
  main()
