#!/usr/bin/env python3

import os
import time
import subprocess

# Este script reinicia todos los dispositivos USB en sistemas Linux
# Requiere ejecución como root

USB_PATH = "/sys/bus/usb/devices"


def reset_usb_devices():
    for device in os.listdir(USB_PATH):
        device_path = os.path.join(USB_PATH, device)

        # Solo actuar sobre dispositivos USB reales
        if not os.path.isdir(device_path):
            continue

        authorized_path = os.path.join(device_path, "authorized")

        if os.path.exists(authorized_path):
            try:
                # Desautorizar el dispositivo
                with open(authorized_path, "w") as f:
                    f.write("0")

                time.sleep(0.5)

                # Volver a autorizar el dispositivo
                with open(authorized_path, "w") as f:
                    f.write("1")

            except PermissionError:
                print(f"Permiso denegado para {device}")
            except Exception as e:
                print(f"Error con {device}: {e}")


def reload_usb_modules():
    # Comentado: solo se ejecuta si quieres reiniciar el stack USB completo
    subprocess.run(["modprobe", "-r", "usb_storage"], check=False)
    time.sleep(1)
    subprocess.run(["modprobe", "usb_storage"], check=False)


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Este script debe ejecutarse como root (sudo).")
        exit(1)

    print("Reiniciando dispositivos USB...")
    reset_usb_devices()
    print("USB reiniciados correctamente.")
