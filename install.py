#! /usr/bin/env python3

import locale
import sys, os, os.path, time, string, subprocess
from dialog import Dialog

# This is almost always a good thing to do at the beginning of your programs.
locale.setlocale(locale.LC_ALL, '')
flashDir="/flash"
diskDir="/disk"

SG_MAP_INSTALL_USB_NAME="opf-installer"

GV_FLASH_P1_LABEL="Prom_fp1"
GV_FLASH_P2_LABEL="Prom_fp2"
GV_FLASH_P3_LABEL="Prom_sys"

MSG_NO_DOM="Please insert one DOM (Media) for installation"
GV_USB_INSTALL_PART=""
GV_USB_INSTALL_DEV=""
DD_FLASH_DEV=""

# You may want to use 'autowidgetsize=True' here (requires pythondialog >= 3.1)

# For older versions, you can use:
#   d.add_persistent_args(["--backtitle", "My little program"])

# In pythondialog 3.x, you can compare the return code to d.OK, Dialog.OK or
# "ok" (same object). In pythondialog 2.x, you have to use d.DIALOG_OK, which
# is deprecated since version 3.0.0.
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
        if check_no_hdd() != 0:
          d.msgbox("Please insert HDD for install OS", width=80)
          continue
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


#Check Directory exist or not, otherwise create for intaller
def check_dir(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs( dir_path, 0o755 )

def check_no_hdd():
  no_hdd=0
  cmd="clitest -u administrator -p password -C phydrv | grep Slot | awk '{print $1}'"
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)

  for no in output.stdout:
    if(no!="\n"):
      no_hdd += 1
  return no_hdd


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
  check_dir(flashDir)
  check_dir(diskDir)

def check_dom_is_exist():
  cmd="sg_map -i | grep -E -v \"{0}|/dev/sr|Promise\" | wc -l".format(GV_USB_INSTALL_DEV)
  output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
  if output.stdout.rstrip() == "0" :
    return False
  else:
    cmd="sg_map -i | grep -E -v \"{0}|/dev/sr|Promise\"".format(GV_USB_INSTALL_DEV)
    cmd=cmd+"| awk '{print $2}'"
    output = subprocess.run(cmd, shell=True,  stdout=subprocess.PIPE, universal_newlines=True)
    global DD_FLASH_DEV
    DD_FLASH_DEV=output.stdout.rstrip()
    return True

def poweroff_msg(d, msg):
  d.msgbox("{0}\n\nPress 'OK' to Shutdown".format(msg),
        width=80,)
  #os.system("shutdown now -h")

  
def main():
  d = Dialog(dialog="dialog")
  d.set_background_title("Welcome to Promise Storage Appliance target installation version: 1.0")
  set_param()
  if check_dom_is_exist() != True:
    poweroff_msg(d, MSG_NO_DOM)
  install_device=device_menu(d)  # 1 = install on flash, 2 = install on HDD
  if full_install_confirm(d) == True:
    d.msgbox("True")
  else:
    if d.yesno("Shutdown?") == d.OK:
      poweroff_msg(d, "")
    else:
      main()

if __name__ == '__main__':
  main()
