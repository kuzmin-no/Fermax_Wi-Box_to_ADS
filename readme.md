# Connecting Fermax Wi-Box to ADS system with differential video

The [Wifi Vds Call Divert Wi-Box](https://www.fermax.com/intl-en/single-products/f03266-wifi-vds-call-divert-wi-box) is designed for installation with the VDS system.
However, I own ADS monitor CityMax 2447 with respective outdoor panel.
After reviewing the technical guides provided by Fermax for both [ADS](https://www.adiglobal.cz/iiWWW/cz/Produkty110.nsf/wp/projektanti_prihlasen/%24file/ADS_trening_2008jan_en.pdf) and 
[VDS](https://doorentrydirect.com/acrobat/fermax/inst/9401/97508I_1_TECHNICAL_MANUAL_VDS_Sistem_V07_09.pdf) I couldn't find
definitive information on their compatibility. However, I did come across a successful integration attempt that inspired me to proceed.
Carlos Carbeal shared his experience on the [Developer Niku Opener](https://developer.nuki.io/t/nuki-opener-and-fermax-citymax-ads-1092/3940/33) forum,
where he described connecting the ADS terminal CityMax 2447 to the Wi-Box. He encountered an issue while programming the VDS address on the Wi-Box,
which he resolved by pressing the call button on the outdoor panel.

I followed the [Fermax Wi-Box installation gide](https://shop.fermaxaus.com.au/content/Fermax-VDS/Wi-Box%20Installation%20Quick%20Guide.pdf).
Unfortunately, in my case, neither programming the VDS address from the monitor nor pressing the call button on the outdoor panel resolved the issue.
I had to manually configure the VDS address on the Wi-Box via the command line. Additionally, I resolved a problem with the video, which in my
setup was differential and connected via AWG cabling, instead of the expected composite and coaxial cabling.

To get access the command line, it is necessary to connect the Wi-Box via UART. I found the repository by [David Girón](https://github.com/duhow/wibox),
extremely helpful; it contains all the required information and examples for modifying the Wi-Box firmware and adding MQTT functionality.

You can access the Wi-Box via UART by following the instructions provided in https://github.com/duhow/wibox/blob/main/INSTALL.md
To do so, connect a UART-USB or similar adapter and adjust the U-Boot settings to gain console access to Linux. Once the Wi-Box boots up, 
it launches the Sofia application, which has default login credentials: username: admin, password: admin.

For a detailed system description and a list of Sofia commands, refer to https://github.com/duhow/wibox/blob/main/docs/system.md
You can use "shell" command to gain root shell access.

After obtaining root access, you can test the functionality of the Wi-Box and attempt to establish a connection with the outdoor panel to open the door.
The following commands can be used:

```bash
# Open channel
echo -e '\xFB\x14\x01\x20' > /dev/ttySGK1
sleep 1
# Open door
echo -e '\xFB\x12\x01\x1E' > /dev/ttySGK1
sleep 1
# Close channel
echo -e '\xFB\x14\x00\x1F' > /dev/ttySGK1
```

You can find a comprehensive list of all UART codes, along with descriptions and the checksum algorithm [here](https://github.com/duhow/wibox/blob/main/docs/codes.md).

The Wi-Box uses either the programmed VDS address or the default one, which is `0xF0 (240)`.
To change or program the VDS address, follow these steps:
1. Determine the address assigned to your monitor. There are a few methods to do this:
  - Estimate it by counting your apartment button on the outdoor panel.
  - Use a Fermax sniffer connected to the L line, as described [here](https://github.com/kuzmin-no/Fermax_CityMax_ADS_2447)
  - Read the EEPROM of the microcontroller in your monitor, as mentioned [here](https://github.com/kuzmin-no/Fermax_CityMax_ADS_2447)
2. Reset the Wi-Box to factory defaults using [this video guide](https://www.youtube.com/watch?v=t7OitAPWH1Q)
3. Gain root access to the shell and program your VDS address into the Wi-Box microcontroller. The VDS address is `0x02` in the example below, you need to
replace it with your specific address and calculate the checksum as outlined [here](https://github.com/duhow/wibox/blob/main/docs/codes.md)

```bash
# save address
echo -e '\xFB\x18\x02\x25' > /dev/ttySGK1
# init address
echo -e '\xFB\x10\x02\x1D' > /dev/ttySGK1
```
4. Restart the Wi-Box and test it by calling your apartment from the outdoor panel.

If you don't see a video stream in the mobile application, or even a blue screen with the date and time, try enabling the video via the command line in the Sofia:

```bash
vionoff on
```

The Fermax Wi-Box and CityMax ADS 2447 monitor support only composite video signals. However, your installation may use AWG cabling
and differential video signals. If your monitor adapter board has labels like `Vi+` and `Vi-` instead of `V` and `M`, it indicates that your
adapter includes MAX436 `Wideband Transconductance Amplifier` on the back side of the board, which converts the differential video signal back to composite.

Photos:

- [Adapter board front](./img/Adapter_board_front.png)
- [Adapter board back](./img/Adapter_board_back.png)
- [MAX436](./img/MAX436.png)

You will need to connect `V`, `M` and `Ct` signals from the Wi-Box to the points shown at the following photo:

- [Connecting adapter board](./img/Adapter_board_connecting.png)

Using the modified software on the Wi-Box, as described below, allows for integration with your smart home system:
- https://github.com/duhow/wibox
- https://web.archive.org/web/20211128173119/https://linuch.pl/blog/fermax-wayfi-wideodomofon-hack-czesc-3

Additionally, it is possible to implement the following scenario:
- You arrive at the outdoor panel and press your apartment button.
- The composite video stream is captured by a USB video capture device, for example `EasyCap`.
- A [python script](https://www.tomshardware.com/how-to/raspberry-pi-facial-recognition) on `Raspberry Pi` or another device performs facial recognition, comparing the captured video/image with a pre-trained model's database.
- If the person is recognized and authorized, the script communicates with the Wi-Box to automatically unlock the entrance door.
The [link](./facial_recognition/facial_req.py) to example script from Caroline Dunn [facial_recognition](https://github.com/carolinedunn/facial_recognition) repo.

The security aspect is not addressed in this description. However, it's possible for someone to gain entry by following another person through the entrance door anyway.
With the proposed implementation, you would have photo or video evidence and a log of entry attempts.

To automatically capture video during calls, we can use [Motion Project](https://github.com/Motion-Project/motion). The only requirement for
both facial recognition and video capturing by Motion is to have two video devices with identical video streams. This can be easily implemented using
v4l2loopback and ffmpeg. For an example, refer to this [link](https://stackoverflow.com/questions/64751478/v4l2loopback-device-detected-by-chrome-not-seen-by-zoom-or-firefox) or follow the steps outlined below:

1. Install v4l2loopback

```bash
sudo apt upgrade v4l2loopback-dkms
```

2. Create file /etc/modprobe.d/v4l2loopback.conf with following content:

```
options v4l2loopback devices=2 exclusive_caps=1,1 video_nr=10,11 card_label="Motion Camera","OpenCV Camera"  
```

3. Load kernel module and ensure that virtual video devices are created:

```bash
sudo modprobe -r v4l2loopback

$ v4l2-ctl --list-devices

"Motion Camera" (platform:v4l2loopback-000):
        /dev/video10

"OpenCV Camera" (platform:v4l2loopback-001):
        /dev/video11

AV TO USB2.0 (usb-xhci-hcd.0-1):
        /dev/video0
        /dev/video1
        /dev/media3
```

4. Now, we need just start ffmpeg, which will duplicate video stream to two video devices:

```bash
sudo ffmpeg -f v4l2 -i /dev/video0 -f v4l2 /dev/video10 -f v4l2 /dev/video11 &
```