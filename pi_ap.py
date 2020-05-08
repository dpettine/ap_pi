from flask import (Flask,  render_template, jsonify, request, current_app)
import time
import subprocess
import threading


# Init a lock for threading
#lock = threading.Lock()

# Initialize the HTTP Client app
app = Flask(__name__)


# Init configuration parameters
app.config.from_pyfile('static/wifi-ini.py', silent=True)


@app.route('/wifi')
def maintenance():
    active_ssid = get_active_wifi(retry=False)

    cells = get_networks()

    return render_template('maintenance.html', networks=render_networks(cells), ssid=active_ssid)


def signal_stregth( power ):
    if power in range(-1000, -85):
        return 'poor'
    if power in range(-85, -75):
        return 'low'
    if power in range(-75, -60):
        return 'fair'
    if power in range(-60, -50):
        return 'good'
    if power in range(-50, 1):
        return 'excellent'


def signal_quality( quality ):
    if quality in range(10):
        return 'unusable'
    if quality in range(10, 35):
        return 'low'
    if quality in range(35, 50):
        return 'medium'
    if quality in range(50, 75):
        return 'good'
    if quality in range(75, 101):
        return 'high'


def render_networks(cells):
    networks = []
    ssids = []

    i = 1

    for cell in cells:

        #print("Wifi Net: ", cell['essid'], " Strength ", cell['signal'])

        if cell['essid'] not in ssids:
            quality_num = cell['quality'].split("/")
            quality_score = int(int(quality_num[0]) / int(quality_num[1]) * 100)

            networks.append({
                'id': i,
                'SSID': cell['essid'],
                'signal': signal_stregth(int(cell['signal'])) + " (" + str(cell['signal']) + "db)",
                'quality': signal_quality(quality_score) + " (" + str(quality_score) + "%)",
                'encrypted': cell['encryption'],
                'encryption_type': cell['enc_type'],
            })
            ssids.append(cell['essid'])
            i += 1

    return networks


def get_networks():
    p = subprocess.run(["sudo", "iwlist", "wlan0", "scan"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       )

    output = p.stdout.decode('utf-8')

    record = False
    networks = []

    for line in output.splitlines():
        if line.find('ESSID') != -1:
            essid = line.split('ESSID:')[1].split('"')[1]
            # print("ESSID ", essid)

        if line.find('Quality') != -1:
            quality = line.split('Quality=')[1].split(' ')[0]
            # print("Quality ", quality)

        if line.find('Signal level') != -1:
            level = line.split('Signal level=')[1].split(' ')[0]
            # print("Signal level ", level)

        if line.find('Encryption key') != -1:
            encrypt = line.split('Encryption key:')[1]
            # print("Encryption ", encrypt)
            if encrypt != "on":
                record = True

        if line.find('IEEE 802.11i') != -1:
            enc_type = line.split('IEEE 802.11i/')[1]
            record = True
            # print("Encryption type", enc_type)

        if record:
            new_record = {"essid": essid, "quality": quality, "signal": level, "encryption": encrypt, "enc_type": enc_type}
            networks.append(new_record)
            # print("The new record ", new_record)
            record = False

    return networks


def get_active_wifi( retry = True ):
    timeout = time.time() + current_app.config['WIFI_CONNECT_TIMEOUT']

    active_ssid = None

    while time.time() < timeout:

        try:
            p = subprocess.run(['sudo', 'iwconfig', 'wlan0'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               )

            if p.returncode == 0:
                print('iwconfig returncode:', p.returncode)
                print('iwconfig output: ', p.stdout.decode('utf-8'))

                output = p.stdout.decode('utf-8')

                if output.find("Mode:Master") != -1:
                    active_ssid = "Mode:Master"
                    break

                elif output.find("Access Point: Not-Associated") == -1:
                    wifi = output.split('\n', 1)[0]
                    active_ssid = wifi.split("ESSID:")[1].split('"')[1::2][0]
                    break

                elif not retry:
                    active_ssid = "Not-Associated"
                    break

            if p.returncode == 1:
                print('iwconfig returncode:', p.returncode)
                print('iwconfig errors: ', p.stderr.decode('utf-8'))
                active_ssid = "Error"
                break

            time.sleep(2.5)

        except subprocess.CalledProcessError as e:
            print(time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime()),
                  ': wifi error:', e.output)

    return active_ssid


def get_service_status(service):
    if service == "":
        print("No service Passed")
        return False

    try:
        p = subprocess.run(
            ["sudo", "systemctl", "is-active", service],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print('get service status returncode:', p.returncode)
        print('get service stat output: ', p.stdout.decode('utf-8'))
        print('get service status  errors: ', p.stderr.decode('utf-8'))

        if len(p.stderr.decode('utf-8')) == 0:
            output = p.stdout.decode('utf-8').strip()
            return output

        else:
            return False

    except subprocess.CalledProcessError as e:
        print(time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime()),
              ': get service status thrown error:', e.output)
        return False


def create_local_supplicant(ssid,passkey):
    outfile = open('static/wpa_supplicant.conf', 'w')

    outfile.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
    outfile.write("update_config=1\n")
    outfile.write("country=" + current_app.config['WIFI_COUNTRY_CODE'] + "\n\n")
    outfile.write("network={\n")
    outfile.write("    ssid=\"" + ssid + "\"\n")
    outfile.write("    psk=\"" + passkey + "\"\n")
    outfile.write("}\n")

    outfile.close()


def wifi_rollback(old_ssid=None):
    try:
        if old_ssid == "Mode:Master":

            p = subprocess.run(
                ["sudo", "mv", "/etc/wpa_supplicant/wpa_supplicant.bck", "/etc/wpa_supplicant/wpa_supplicant.conf"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            p = subprocess.run(
                ["sudo", "ifconfig", "wlan0", current_app.config['WLAN0_PRIVATE_IP']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print('Rolling Back - ifconfig returncode:', p.returncode)
            print('Rolling Back - ifconfig output: ', p.stdout.decode('utf-8'))
            print('Rolling Back- ifconfig errors: ', p.stderr.decode('utf-8'))

            if p.returncode == 0:
                p = subprocess.run(["sudo", "service", "dhcpcd", "restart"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )

                print('Rolling Back - dhcp restart returncode:', p.returncode)
                print('Rolling Back - dhcp restart output: ', p.stdout.decode('utf-8'))
                print('Rolling Back - dhcp restart errors: ', p.stderr.decode('utf-8'))

                p = subprocess.run(["sudo", "systemctl", "start", "dnsmasq"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )

                print('Rolling Back - DNS restart returncode:', p.returncode)
                print('Rolling Back - DNS restart output: ', p.stdout.decode('utf-8'))
                print('Rolling Back- DNS restart errors: ', p.stderr.decode('utf-8'))

                p = subprocess.run(["sudo", "systemctl", "unmask", "hostapd"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )

                print('Rolling Back - HOSTAPAD unmask returncode:', p.returncode)
                print('Rolling Back - HOSTAPAD unmask output: ', p.stdout.decode('utf-8'))
                print('Rolling Back- HOSTAPAD unmask errors: ', p.stderr.decode('utf-8'))

                p = subprocess.run(["sudo", "systemctl", "enable", "hostapd"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )

                print('Rolling Back - HOSTAPAD enable returncode:', p.returncode)
                print('Rolling Back - HOSTAPAD enable output: ', p.stdout.decode('utf-8'))
                print('Rolling Back- HOSTAPAD enable errors: ', p.stderr.decode('utf-8'))

                p = subprocess.run(["sudo", "systemctl", "start", "hostapd"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )
                print('Rolling Back - HOSTAPAD restart returncode:', p.returncode)
                print('Rolling Back - HOSTAPAD restart output: ', p.stdout.decode('utf-8'))
                print('Rolling Back- HOSTAPAD restart errors: ', p.stderr.decode('utf-8'))

        else:
            p = subprocess.run(
                ["sudo", "cp", "/etc/wpa_supplicant/wpa_supplicant.bck", "/etc/wpa_supplicant/wpa_supplicant.conf"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            p = subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               )

            print('Rolling Back - Reconfigure returncode:', p.returncode)
            print('Rolling Back - Reconfigure output: ', p.stdout.decode('utf-8'))
            print('Rolling Back- Reconfigure errors: ', p.stderr.decode('utf-8'))

            p = subprocess.run(["sudo", "dhclient", "-r", "wlan0"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               )

            print('dhcp renew - returncode:', p.returncode)
            print('dhcp renew - output: ', p.stdout.decode('utf-8'))
            print('dhcp renew - errors: ', p.stderr.decode('utf-8'))

        return get_active_wifi()

    except subprocess.CalledProcessError as e:
        print(time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime()),
              ': wifi error:', e.output)


@app.route('/wifi/wifi-connect', methods=['POST'])
def wifi_connect(ssid=None, passkey=None):

    json = False

    if request:
        ssid = request.values['ssid']
        passkey = request.values['passphrase']
        json = True

    if ssid is None:
        response = {
            'connected': False,
            'ssid': '',
            'error': 'No ssid provided'
            }

    else:
        try:
            p = subprocess.run(
                ["sudo", "cp", "/etc/wpa_supplicant/wpa_supplicant.conf", "/etc/wpa_supplicant/wpa_supplicant.bck"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )

            create_local_supplicant(ssid, passkey)

            p = subprocess.run(
                ["sudo", "cp", "static/wpa_supplicant.conf", "/etc/wpa_supplicant/wpa_supplicant.conf"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                )

            if p.returncode == 0:

                starting_ssid = get_active_wifi(retry=False)

                if starting_ssid == "Mode:Master":

                    count = 0

                    while get_service_status(service="dnsmasq") != "inactive" and count < 5:
                        p = subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           )
                        print('Activate WiFi - STOP DNS returncode:', p.returncode)
                        print('Activate WiFi - STOP DNS output: ', p.stdout.decode('utf-8'))
                        print('Activate WiFi - STOP DNS errors: ', p.stderr.decode('utf-8'))
                        time.sleep(5)
                        count += 1

                    count = 0

                    while get_service_status(service="hostapd") != "inactive" and count < 5:
                        p = subprocess.run(["sudo", "systemctl", "stop", "hostapd"],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           )
                        print('Activate WiFi - STOP HOSTAPD returncode:', p.returncode)
                        print('Activate WiFi - STOP HOSTAPD output: ', p.stdout.decode('utf-8'))
                        print('Activate WiFi - STOP HOSTAPD errors: ', p.stderr.decode('utf-8'))
                        time.sleep(5)
                        count += 1

                    count = 0

                    while get_service_status(service="dhcpcd") != "inactive" and count < 5:
                        p = subprocess.run(["sudo", "service", "dhcpcd", "stop"],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           )
                        print('Activate WiFi - DHCP Restart returncode:', p.returncode)
                        print('Activate WiFi - DHCP Restart output: ', p.stdout.decode('utf-8'))
                        print('Activate WiFi -  DHCP Restart errors: ', p.stderr.decode('utf-8'))
                        time.sleep(5)
                        count += 1

                    count = 0

                    while get_service_status("dhcpcd") != "active" and count < 5:
                        p = subprocess.run(["sudo", "service", "dhcpcd", "start"],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           )
                        print('Activate WiFi - DHCP Restart returncode:', p.returncode)
                        print('Activate WiFi - DHCP Restart output: ', p.stdout.decode('utf-8'))
                        print('Activate WiFi -  DHCP Restart errors: ', p.stderr.decode('utf-8'))
                        time.sleep(5)
                        count += 1

                p = subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )

                print('WiFi activation - returncode:', p.returncode)
                print('WiFi activation - output: ', p.stdout.decode('utf-8'))
                print('WiFi activation - errors: ', p.stderr.decode('utf-8'))

                p = subprocess.run(["sudo", "dhclient", "-r", "wlan0"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )

                print('dhcp renew - returncode:', p.returncode)
                print('dhcp renew - output: ', p.stdout.decode('utf-8'))
                print('dhcp renew - errors: ', p.stderr.decode('utf-8'))

                sub_code = p.stdout.decode('utf-8')
                sub_err = p.stderr.decode('utf-8')

                if (p.returncode != 0) or (sub_code.find("FAIL") != -1) or (len(sub_err) > 0):

                    print("Can't complete new WiFi activation ")

                    rollback_ssid = wifi_rollback(starting_ssid)
                    response = {
                        'connected': False,
                        'ssid': rollback_ssid,
                        'error': "Couldn't connect to " + ssid + ". Please check credentials!"
                        }

                else:
                    active_ssid = get_active_wifi()

                    if active_ssid is None or active_ssid != ssid:
                        rollback_ssid = wifi_rollback(starting_ssid)
                        response = {
                            'connected': False,
                            'ssid': rollback_ssid,
                            'error': "Couldn't connect to " + ssid + ". Please check credentials!"
                            }

                    elif active_ssid == "Error":
                        rollback_ssid = wifi_rollback(starting_ssid)
                        response = {
                            'connected': False,
                            'ssid': rollback_ssid,
                            'error': "system error. Please contact the technical assistance. "
                                     "Error code: " + p.stderr.decode('utf-8')
                            }

                    else:
                        response = {
                            'connected': True,
                            'ssid': active_ssid,
                            'error': ''
                            }

            else:
                response = {
                    'connected': False,
                    'ssid': '',
                    'error': 'cannot create the new wifi config.'
                    }

        except subprocess.CalledProcessError as e:

            response = {
                'connected': False,
                'ssid': '',
                'error': 'exception'
                }

            print(time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime()),
                  ': wifi error:', e.output)

    if json:
        return jsonify(response)

    else:
        return response


def run_app():
    app.run(host=app.config['HTTP_HOST'], port=app.config['HTTP_PORT'], debug=app.config['DEBUG_MODE'], threaded=True, use_reloader=False)


# execute main function
if __name__ == "__main__":
    # Update defaults from DB
    print(time.strftime("%d-%m-%Y_%H-%M-%S", time.localtime()), ": starting wifi configuration http server ")
    run_app()

    # start a thread to run the flask app
    # t = threading.Thread(target=run_app, args=())
    # t.daemon = True
    # t.start()
