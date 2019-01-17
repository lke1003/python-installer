#! /usr/bin/env python3

import locale
import sys, os, os.path, time, string, subprocess
from dialog import Dialog

# This is almost always a good thing to do at the beginning of your programs.
locale.setlocale(locale.LC_ALL, '')
flashDir="/flash"
diskDir="/disk"

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
              "exit this demo?"
    else:
        msg = "You pressed ESC in the last dialog box. Do you want to " \
              "exit this demo?"
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
        if check_no_hdd == 0:
          d.msgbox("Please insert HDD for install OS", width=80)
          continue
      if handle_exit_code(d, code):
        break
  return tags

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



def main():
  check_dir(flashDir)
  check_dir(diskDir)
  d = Dialog(dialog="dialog")
  # Dialog.set_background_title() requires pythondialog 2.13 or later
  d.set_background_title("Welcome to Promise Storage Appliance target installation version: 1.0")
  install_device=device_menu(d)  # 1 = install on flash, 2 = install on HDD
  d.msgbox(install_device)

if __name__ == '__main__':
  main()
