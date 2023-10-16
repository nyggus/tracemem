jaka=$1

function dupa() {
    kupa=$1
    if [[ $kupa = "" ]] ; then
        export ZUPKA="Pomidorowa"
    else
        export ZUPKA="Ogrowa"
    fi
}

function printuj() {
    echo $ZUPKA
}

dupa $jaka
printuj
dupa
printuj
