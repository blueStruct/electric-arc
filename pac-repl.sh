#!/bin/sh


### Constants #################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'


### Functions #################################################################

msg() {
    # $1 text
    printf "${GREEN}$1${NC}\n"
}


input() {
    # $1 variable (as string) to put answer into
    # read -r -p $(printf "${GREEN}> ${NC}") $1
    read -r $1
}

is_true() {
    # $1 variable to check
    if { test $1 = 'true' || test $1 = 'yes' || test $1 = 'y'; }
    then return 0
    else return 1
    fi
}


### Main Loop #################################################################

while true
do {
    msg "What do you want to do?"
    input answer
    case $answer in
        exit | quit | q | e | x) break ;;
        search | s | Ss | f | info) echo; yay -Slq | fzf | yay -Si - ;;
        query | Q | Qs | Qi) echo; pacman -Qq | fzf | pacman -Qi - ;;
        delete | d | R | Rsn) echo; pacman -Qq | fzf | sudo pacman -Rs - ;;
        install | i | S)
            echo;
            package=$(yay -Slq | fzf)
            if ! { pacman -Ssq $package | grep -q "^$package\$"; }
            then
                msg "WARNING: This is a package from AUR, do you really want to install it?"
                input go_ahead
                if { is_true $go_ahead; }
                then echo; yay --needed -S $package
                fi
            else sudo pacman --needed -S $package
            fi
        ;;
    esac
    echo
}
done

