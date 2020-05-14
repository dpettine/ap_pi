# Flask PI configuration
DEBUG_MODE = False
HTTP_PORT = "8080"
HTTP_HOST = "0.0.0.0"

# WIFI CONFIGURATION

WIFI_COUNTRY_CODE = "IT"
WIFI_CONNECT_TIMEOUT = 30

# wifi interface used. By default this is 'wlan0'
INTERFACE = "wlan0"

# static ip address used by the wifi interface when in AP mode
WLAN0_STATIC_IP = "192.168.4.1"

# dhcp params: Starting-IP, Ending-IP, netmask for the leased network, lease interval in hours
DHCP_SERVER = '192.168.4.2,192.168.4.20,255.255.255.0,24h'