sudo apt install liblo-dev
$ pip install pyliblo3

serial port config

sudo raspi-config
 ```
	3 Interface Options

	Would you like a login shell to be accessible over serial?   
	<No>

	Would you like the serial port hardware to be enabled?
	<yes>

 ```


Samba:

sudo apt install samba samba-common-bin


sudo nano /etc/samba/smb.conf


 ```
#======================= Share Definitions =======================

[home]
    comment = Pi Home
    path = /home/pi
    browseable = yes
    writeable = yes
    force create mode = 0777
    force directory mode = 0777
    public = yes

[homes]
   comment = Home Directories
   browseable = no

# By default, the home directories are exported read-only. Change the
# next parameter to 'no' if you want to be able to write to them.
   read only = no 

 # File creation mask is set to 0700 for security reasons. If you want to
# create files with group=rw permissions, set next parameter to 0775.
   create mask = 0775

# Directory creation mask is set to 0700 for security reasons. If you want to
# create dirs. with group=rw permissions, set next parameter to 0775.
   directory mask = 0775

 ```

cd /usr/bin
sudo ln -s ~/Documents/RainPots/rainpots_configure.py rainpots-config
sudo ln -s ~/Documents/RainPots/main.py rainpots


SystemD servevice
cd /lib/systemd/system

rainpots.service
 ```
[Unit]
  Description=RainPots Service
  After=multi-user.target
  StartLimitIntervalSec=500
  StartLimitBurst=5
  StartLimitInterval=0
  Wants=rnbooscquery.service
  After=rnbooscquery.service
  PartOf=rnbooscquery.service

[Service]
  Type=idle
  ExecStart=/usr/bin/rainpots
  KillSignal=SIGINT
  User=pi
  Group=audio
  Restart=on-failure
  RestartSec=5s
  StandardOutput=append:/home/pi/Documents/RainPots/log/rainpots.log
  StandardError=append:/home/pi/Documents/RainPots/log/rainpots-eror.log

[Install]
  WantedBy=multi-user.target
  Alias=rainpots

 ```
sudo systemctl daemon-reload

 sudo systemctl enable (startup at boot)
 
