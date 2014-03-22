# Este script es utilizado por Buildroot.
# Las rutas son relativas al directorio "util/buildroot".

TARGETDIR=$1

cp -ar ../../rootfs-additions/* $TARGETDIR/

# Cambiamos fstab para que se utilice ext4 en lugar de ext2.
sed -i 's/ext2/ext4/g' $TARGETDIR/etc/fstab

exit 0

