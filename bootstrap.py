#!/usr/bin/python

## Files/Folders that will be used
## packages = list of non-aur-packages to install
## packages.aur = list of aur-packages to install
## services = list of services to enable and start
## custom-systemd-units = folder with custom systemd unit files


from threading import Thread
from queue import Queue
from enum import Enum
import subprocess
import os
# import os.path

### Enums #####################################################################

class Color(Enum):
    NC = 1
    G = 2
    R = 3


### Functions #################################################################

def set_color(c):
    if c == Color.NC:
        print('\033[0m')
    elif c == Color.G:
        print('\033[0;32m')
    elif c == Color.R:
        print('\033[0;31m')

def msg(m):
    set_color(Color.G)
    print(m)
    set_color(Color.NC)


def err(m):
    set_color(Color.R)
    print(m)
    set_color(Color.NC)


def inputp():
    set_color(Color.G)
    input('> ')
    set_color(Color.NC)


def run(p):
    subprocess.run(p, shell=True)


def password_input(): #TODO
    pass


def is_true(v):
    if v in ('true', 'yes', 'y'):
        return True
    else:
        return False


def check_installed(pack):
    if run('pacman -Qq {} 2> /dev/null'.format(pack)).returncode:
        return True
    else:
        return False


#TODO can't run makepkg as root
def install_aur_helper():
    msg('installing $aur_helper...')
    run((
        'cd /tmp;'
        'git clone https://aur.archlinux.org/$aur_helper.git;'
        'cd $aur_helper;'
        'makepkg -si'
        'cd /root'
    ))


def install_pck(prog, pack):
    # $1 installer; $2 package
    msg('installing {}...'.format(pack))
    run('{} --noconfirm --needed -S {}'.format(prog, pack))


def batch_install(prog, packages):
    run('cat {} | {} --noconfirm --needed -S -'.format(packages, prog))


def setup_system():
    pass #TODO


def change_system_configs():
    pass #TODO


def place_systemd_units():
    run((
        'for i in custom-systemd-units/*;'
        'do cp -i $i /etc/systemd/system;'
        'done'
    ))


def setup_lan_pacman_cache():
    msg('setting up LAN Pacman Cache')
    install_pck('powerpill', 'darkhttpd')
    run('ln -s /var/lib/pacman/sync/*.db /var/cache/pacman/pkg')
    # placing/enabling the unit file along with the others
    # in custom-systemd-units


def enable_services():
    # systemd units provided by upstream
    if os.path.exists('services'):
        run((
            'for i in $(cat services);'
            'do systemctl --now enable $i;'
            'done'
        ))

    # custom systemd unit
    run((
        'for i in custom-systemd-units/*;'
        'do systemctl --now enable $i;'
        'done'
    ))


def test():
    run('notify-send test')



### Script ####################################################################

msg('Let\'s setup your user account')

msg('username?')
username = input()

msg('For your password entry: Do you want to see asterisks?')
hide_pw = inputp()

while True:
    msg('password?')
    password = (password_inputp() if is_true(hide_pw) else inputp())

    msg('please type your password again')
    password_verify = (password_inputp() if is_true(hide_pw) else inputp())

    if password == password_verify:
        break
    err('Password did not match. Try again')

msg('Should this user account have sudo access?')
sudo_access = inputp()

msg('Which shell do you want to use?')
shell = inputp()

msg('Do you want your system to provide a pacman cache on your LAN?')
lan_pacman_cache = inputp()

if is_true(lan_pacman_cache):
    msg((
        'You should choose a fixed IP address on your LAN, so the clients can easily'
        'reach your pacman cache. Do you want a fixed IP address?'
    ))
    fixed_ip = inputp()

    if run('grep -q \'^ufw\$\' packages').returncode:
        msg('Do you want ufw to allow access from your LAN, so your cache can be reached?')
        lan_access = inputp()



# install aur-helper
msg('Which AUR-helper do you want?')
aur_helper = inputp()

pacman_queue = Queue()
def pacman_run():


pacman_thread = Thread
{
    # use all cores when compiling with makepkg
    sed -i 's/^#MAKEFLAGS/MAKEFLAGS/;/^MAKEFLAGS/s/-j2/-j$(nproc)/' /etc/makepkg.conf
    sync_pacman_database
    # AUR-helper
    install_aur_helper
} &

# install powerpill
msg('Do you want to use Powerpill?')
wants_powerpill = inputp()
if { is_true wants_powerpill; }
then {
    wait $!
    install_pck $aur_helper powerpill
} &
fi

pid=$!

## install packages




# install and use reflector to get fast mirrors
install_pck pacman reflector
msg('generating new mirrorlist...')
reflector --save /etc/pacman.d/mirrorlist --threads $(nproc) -c Germany -c France --score 20 --sort rate



if is_true wants_powerpill
then batch_install powerpill packages
else batch_install pacman packages
fi

batch_install $aur_helper packages.aur


# system-level/root configuration

setup_system
change_system_configs
place_systemd_units

if is_true lan_pacman_cache
then setup_lan_pacman_cache
fi

enable_services

if check_installed ufw
then
    ufw enable
    if is_true lan_access
    then ufw allow from 192.168.2.1/24 #TODO use awk to avoid hardcoded ip range
fi

timedatectl set-ntp true
chsh -s /usr/bin/$shell


# user-level configuration

useradd -m -s /usr/bin/$shell $username


# rust development setup

if check_installed('rustup'):
    run((
        'sudo -u {} rustup toolchain install nightly'
        'sudo -u {} rustup toolchain install stable'
        'sudo -u {} rustup default stable'
        'sudo -u {} rustup component add clippy'
        'sudo -u {} rustup component add rustfmt'
        'sudo -u {} cargo install sccache'
    ).format(username))







