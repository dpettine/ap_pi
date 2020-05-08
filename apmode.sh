#!/bin/bash
DIR=$(dirname "$0")

W_IF=`sudo rfkill list | grep Wireless`
set -- $W_IF
IN=$1
IF_N="${IN:0:1}"

echo "WiFi interface is" $IF_N
W_SOFT=`sudo rfkill list $IF_N | grep Soft | grep yes`
W_HARD=`sudo rfkill list $IF_N | grep Hard | grep yes`

if [[ $W_SOFT != "" ]]; then 
	echo "WiFi is turned off enabling it"
	attmpt=1	
	while [ "$W_SOFT" != "" -a $attmpt -lt 4 ]
	do
		sudo rfkill unblock wifi
		W_SOFT=`sudo rfkill list $IF_N | grep Soft | grep yes`
		echo "enabling wifi. Attempt number" attmpt
		attmpt=$((attmpt+1))
	done
fi
W_SOFT=`sudo rfkill list $IF_N | grep Soft | grep yes`	
if [[ $W_SOFT == "" ]]; then
	echo "WiFi enabled"
else
	echo "Can't enable WiFi"
	exit
fi

if [[ $W_HARD == "" ]]; then
        echo "WiFi is switched on"
else
        echo "WiFi is switched off. Please turn hw on"
	exit
fi

DNS_STATUS=`sudo systemctl is-active dnsmasq`
#echo "DNS MASQ status is " $DNS_STATUS
attmpt=1
while [ $DNS_STATUS != "inactive" -a $attmpt -lt 4 ] 
do
        echo "stopping dnsmasq attempt" $attmpt
        sudo systemctl stop dnsmasq
	DNS_STATUS=`sudo systemctl is-active dnsmasq`
	attmpt=$((attmpt+1))
done
echo "DNS MASQ status is " $DNS_STATUS

HOSTAPD_STATUS=`sudo systemctl is-active hostapd`
#echo "hostapd service status is " $HOSTAPD_STATUS
attmpt=1
while [ $HOSTAPD_STATUS != "inactive" -a $attmpt -lt 4 ]
do
        echo "stopping hostapd attempt" $attmpt
        sudo systemctl stop hostapd
	HOSTAPD_STATUS=`sudo systemctl is-active hostapd`
	attmpt=$((attmpt+1))
done
echo "hostapd service status is " $HOSTAPD_STATUS

AP_STAT=`sudo iwconfig wlan0`
attmpt=1
while [ ${#AP_STAT} == 0 -a $attmpt -lt 10 ]
do
	echo "wlan0 isn't up yet waiting 10 seconds. Attempt" $attmpt
	sleep 10
	AP_STAT=`sudo iwconfig wlan0`
	attmpt=$((attmpt+1))
done
echo "Interface status "$AP_STAT

AP=`sudo iwconfig wlan0 | grep Not-Associated`
SSID_CONF=`cat /etc/wpa_supplicant/wpa_supplicant.conf | grep ssid`
IFS='\"' read -ra TOKS <<< "$SSID_CONF"
SSID="${TOKS[1]}"

if [[ $SSID != "" ]]; then
	echo "The configured network SSID is" $SSID
else
	echo "no WiFi network configured"
fi

if [[ $AP != "" ]] && [[ $SSID != "" ]]; then
	attmpt=1
	while [ $AP != "" -a $attmpt -lt 10 ]
	do
		echo "The configured WiFi with SSID" $SSID "is not associated yet. Giving some more time to connect the network. Attempt" $attmpt "out of 10"
		sleep 10
		AP=`sudo iwconfig wlan0 | grep Not-Associated`
		attmpt=$((attmpt+1))
	done	
fi

IP_WLAN=`cat $DIR/static/wifi-ini.py | grep WLAN0_PRIVATE_IP`
IFS='/"' read -ra TOKS <<< "$IP_WLAN"
IP="${TOKS[1]}"
echo "The configured static IP for wlan0 is "$IP

MODE=`sudo iwconfig wlan0 | grep Mode:Master`

if [[ $AP != "" ]] || [[ $MODE != "" ]]; then
	echo "Initialize AP Mode"

	sudo mv /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.bck

	IP_WLAN=`cat $DIR/static/wifi-ini.py | grep WLAN0_PRIVATE_IP`
	IFS='/"' read -ra TOKS <<< "$IP_WLAN"
	IP="${TOKS[1]}"
	echo "The configured static IP for wlan0 is "$IP

	echo "assign static IP to wlan0"
	sudo ifconfig wlan0 $IP
	INET=`sudo ifconfig -a wlan0 | grep inet`
	set -- $INET
	echo "wlan0 IP address is: " $2 
	if [[ $2 == $IP ]]; then
		attmpt=1
		DHCP_STATUS=`sudo systemctl is-active dhcpcd`
		while [ "$DHCP_STATUS" != "inactive" -a $attmpt -lt 4 ]
		do
			echo "stopping dhcp daemon. Attempt number " $attmpt " service status is "$DHCP_STATUS
			sudo service dhcpcd stop
			DHCP_STATUS=`sudo systemctl is-active dhcpcd`
			attmpt=$((attmpt+1))
		done
		if [[ $DHCP_STATUS == "inactive" ]]; then
                	echo "dhcp service stopped"
        	else
                	echo "Couldn't stop dhcp service"
			exit
        	fi
		# Start dhcp service
		attmpt=1
		DHCP_STATUS=`sudo systemctl is-active dhcpcd`
                while [ "$DHCP_STATUS" != "active" -a $attmpt -lt 4 ]
                do
                        echo "starting dhcp service. Attempt number " $attmpt " service status is "$DHCP_STATUS
                        sudo service dhcpcd start
			DHCP_STATUS=`sudo systemctl is-active dhcpcd`
                        attmpt=$((attmpt+1))
                done
                if [[ $DHCP_STATUS == "active" ]]; then
                        echo "dhcp service started"
                else
                        echo "Couldn't start dhcp service"
			exit
                fi      

		DNS_STATUS=`sudo systemctl is-active dnsmasq`
		while [ "$DNS_STATUS" != "active" -a $attmpt -lt 4 ]
                do
                        echo "starting dnsmasq service. Attempt number " $attmpt " service status is "$DNS_STATUS
                        sudo systemctl start dnsmasq
                        DNS_STATUS=`sudo systemctl is-active dnsmasq`
                        attmpt=$((attmpt+1))
                done
		if [[ $DNS_STATUS == "active" ]]; then
			echo "dnsmasq service started"
		else
			echo "Couldn't start dnsmasq service"
			exit
		fi

		sudo systemctl unmask hostapd
		sudo systemctl enable hostapd

		attmpt=1
		HOSTAPD_STATUS=`sudo systemctl is-active hostapd`
		
		while [ "$HOSTAPD_STATUS" != "active" -a $attmpt -lt 4 ]
                do
                        echo "starting hostapd service. Attempt number " $attmpt " service status is "$DHCP_STATUS
                        sudo systemctl start hostapd
                        HOSTAPD_STATUS=`sudo systemctl is-active hostapd`
                        attmpt=$((attmpt+1))
                done
                if [[ $HOSTAPD_STATUS == "active" ]]; then
                        echo "hostapd service started"
                else
                        echo "Couldn't start hostpd service"
			exit
                fi		
	else
		echo "can't assign static IP address to wlan0" 
	fi

else
	echo "Already associated"
fi
