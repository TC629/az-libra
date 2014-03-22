# Este script es utilizado por Buildroot.
# Las rutas son relativas al directorio "util/buildroot".

IMAGEDIR=$1

# Este paso es temporal mientras se arregla el archivo pcduino.fex
# en el repositorio https://github.com/linux-sunxi/sunxi-boards
# Una vez que se arregle se puede habilitar la opcion de Buildroot
# en Target packages -> Hardware handling -> Firmware -> sunxi script.bin board file

../sunxi-tools/fex2bin ../sunxi-extras/pcduino.fex $IMAGEDIR/script.bin

# Generamos boot.src con configuraciones extra para uboot.
mkimage -C none -A arm -T script -d ../../boot.cmd $IMAGEDIR/boot.src 

exit 0

