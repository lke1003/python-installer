GV_FLASH_P2_LABEL=$1

RENAME_DEV=$(blkid -s LABEL | grep "$GV_FLASH_P2_LABEL" |awk '{print $1}' |sed 's/://g' )
for RENAME in $RENAME_DEV
do
tune2fs -L "Prom" $RENAME 
done 

