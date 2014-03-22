setenv bootargs rootfstype=ext4,ext3,ext2
ext2load mmc 0 0x43000000 script.bin
ext2load mmc 0 0x48000000 uImage
bootm 0x48000000
