#!/bin/sh
# Programmas record.py automātiskas palaišanas skripts palaišanai no komandrindas vai attiecīgu ierakstu /etc/rc.local datnē
# Varētu būt nepieciešams pamainīt sleep (iemigšanas) aizkavēšanās parametru, ja tas nedarbojas pareizi caur rc.local
# Jāpārliecinās, vai šis skripts ir izpildāms (ir izpildāmas datnes tiesības) vai jāuzstāda tās ar komandu:
# chmod +x run.sh
# Šis skripts aizsargā programmas record.py palaišanu vairākas reizes
# jo Raspberry Pi kamera nevar tikt darbināta vairākas reizes vienlaicīgi

progpath="/home/pi/record"
progname="record.py"
proglog="verbose.log"
progsleep=10

echo "$0 ver 1.1 written by Haralds Plass using initial script written by Claude Pageau"
echo "-----------------------------------------------"
cd $progpath

# Pārbauda, vai eksistē programma, kuras nosaukums uzstādīts mainīgajā 'progname'
if [ ! -e $progname ] ; then
  echo "ERROR - Could Not Find $progname"
  exit 1
fi

if [ -z "$( pgrep -f $progname )" ]; then
  if [ "$1" = "start" ]; then
    echo "Start $progpath/$progname in Background"
    # laiks sekundēs (uzstādīts mainīgajā 'progsleep'), par ko aizkavēt programmas palaišanu 
	#līdz iesāknējas pati iekārta Raspberry Pi Zero (ja darbina no /etc/rc.local)
    echo "Waiting $progsleep seconds ...."
    sleep $progsleep

    # nokomentēt līniju zemāk, ja nav nepieciešams ierakstīt konsoles izvaddatus
    $progpath/$progname  >/dev/null 2>&1 &
    # Piezīme: uzstādīt verbose = True datnē config.py
    # tad atkomentēt līniju zemāk, lai veidotos LOG datne
    # echo "Start $progpath/$progname with log to $progpath/$proglog"
    # python -u $progpath/$progname  > $progpath/$proglog &
  fi
else
  if [ "$1" = "stop" ]; then
    echo "Stopping $progname ...."
    progPID=$( pgrep -f $progname )
    sudo kill $progPID
  fi
fi

if [ -z "$( pgrep -f $progname )" ]; then
    echo "$progname is Not Running ..."
    echo "To Start $progname execute command below"
    echo "$0 start"
  else
    progPID=$(pgrep -f $progname)
    echo "$progname is Running ..."
    echo "PID is $progPID"
    echo "To Stop $progname execute command below"
    echo "$0 stop"
fi
echo "Good Bye Harald's camera record program!"