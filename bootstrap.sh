#!/bin/sh

## Files/Folders that will be used
## packages = list of non-aur-packages to install
## packages.aur = list of aur-packages to install
## services = list of services to enable and start
## custom-systemd-units = folder with custom systemd unit files


### Constants #################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'


### Functions #################################################################

msg() {
    # $1 text
    printf "${GREEN}$1${NC}\n"
}

err() {
    # $1 text
    printf "${RED}$1${NC}\n"
}

input() {
    # $1 variable (as string) to put answer into
    # read -r -p $(printf "${GREEN}> ${NC}") $1
    read -r $1
}

password_input() {
    # $1 variable (as string) to put answer into
    # read -r -p $(printf "${GREEN}>${NC}") $1 #TODO -s asterisks
    read -r $1
}

is_true() {
    # $1 variable to check
    if { test $1 = 'true' || test $1 = 'yes' || test $1 = 'y'; }
    then return 0
    else return 1
    fi
}

sync_pacman_database() {
    pacman -Syy
}

check_installed() {
    # $1 package
    if { pacman -Qq $1 2> /dev/null; }
    then return true
    else return false
    fi
}

install_aur_helper() {
    msg "installing $aur_helper..."
    cd /tmp
    git clone https://aur.archlinux.org/$aur_helper.git
    cd $aur_helper
    makepkg -si #TODO can't run makepkg as root
    cd /root
}

install_pck() {
    # $1 installer; $2 package
    msg "installing $2..."
    $1 --noconfirm --needed -S $2
}

batch_install() {
    # $1 installer; $2 file with package names
    cat $2 | $1 --noconfirm --needed -S -
}

prepare_install() {
}

setup_system() {
    sleep 0 #TODO
}

change_system_configs() {
    sleep 0 #TODO
}

place_systemd_units() {
    for i in custom-systemd-units/*
    do cp -i $i /etc/systemd/system
    done
}

setup_lan_pacman_cache() {
    msg 'setting up LAN Pacman Cache'
    install_pck powerpill darkhttpd
    ln -s /var/lib/pacman/sync/*.db /var/cache/pacman/pkg
    # placing/enabling the unit file along with the others
    # in custom-systemd-units
}

enable_services() {
    # systemd units provided by upstream
    if { test -e services; }
    then
        for i in $(cat services)
        do systemctl --now enable $i
        done
    fi

    # custom systemd unit
    for i in custom-systemd-units/*
    do systemctl --now enable $i
    done
}


### Script ####################################################################

msg "Let's setup your user account"
msg 'username?'
input username
msg 'For your password entry: Do you want to see asterisks?'
input hide_pw

while true
do
    if { is_true hide_pw; }
    then
        msg 'password'
        password_input  password
        msg 'please type your password again'
        password_input password_verify
    else
        msg 'password'
        input password
        msg 'please type your password again'
        input password_verify
    fi
    if { test $password = $password_verify; }; then break; fi
    err 'Password did not match. Try again'
done

msg 'Should this user account have sudo access?'
input sudo_access
msg 'Which shell do you want to use?'
input shell
msg 'Do you want your system to provide a pacman cache on your LAN?'
input lan_pacman_cache
if { is_true lan_pacman_cache; }
then {
    msg 'You should choose a fixed IP address on your LAN, so the clients can easily
         reach your pacman cache. Do you want a fixed IP address?'
    input fixed_ip
    if { grep -q "^ufw\$" packages; }
    then
        msg 'Do you want ufw to allow access from your LAN, so your cache can be reached?'
        input lan_access
    fi;
}
fi



# install aur-helper
msg 'Which AUR-helper do you want?'
input aur_helper
{
    # use all cores when compiling with makepkg
    sed -i 's/^#MAKEFLAGS/MAKEFLAGS/;/^MAKEFLAGS/s/-j2/-j$(nproc)/' /etc/makepkg.conf
    sync_pacman_database
    # AUR-helper
    install_aur_helper
} &

# install powerpill
msg 'Do you want to use Powerpill?'
input wants_powerpill
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
msg 'generating new mirrorlist...'
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

if check_installed rustup
then
    sudo -u $username rustup toolchain install nightly
    sudo -u $username rustup toolchain install stable
    sudo -u $username rustup default stable
    sudo -u $username rustup component add clippy
    sudo -u $username rustup component add rustfmt
    sudo -u $username cargo install sccache
fi







