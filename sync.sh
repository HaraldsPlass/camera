#!/bin/bash
echo "--------------------------------------"
# -------------------------------------------
# Šis skripts veic šādas darbības:
# 1) palaiž gdrive tikai tad, ja tas jau nedarbojas
# 2) kontrolē record.sync datni, ko ir izveidojusi record.py programma gadījumā, ja:
# (1) ir izveidojušies jauni sinhronizējami faili un (2) ja parametrs CHECK_FOR_SYNC_FILE=true
# Iznīcina gdrive procesu, ja tas darbojas pārāk ilgi (pēc noklusējuma > 4000 sekundes vai 67 minūtes)
# Ieteicams izpildīt šo skriptu no crontab, piemēram, ik pēc 5 minūtēm, pēc komandas 'sudo crontab -e' pievienojot crontab šādu rindu:
# */5 * * * * /home/pi/record/sync.sh >/dev/nul
# --------------------------------------------------------------------
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" # šī skripta direktorija

# -------------  Mainīgie -------------
SYNC_DIR=mo1                     # sinhronizējamā direktorija, kas atrodas šī skripta direktorijā
PROC_DIR=processed               # direktorija uz kuru pārvietot OpenALPR un gdrive apstrādātās attēlu datnes
FILES_TO_SYNC='*csv'             # apstrādājamo datņu veidi (* - visi)
CHECK_FOR_SYNC_FILE=true         # true, ja ir nepieciešama sync datnes pārbaude, savādāk uzstādīt false
SYNC_FILE_PATH=$DIR/record.sync  # record programmas inicializētas sinhronizācijas apturēšanas datne
FORCE_REBOOT=false               # true, lai restartētu, ja record programma nedarbojas, savādāk uzstādīt false
WATCH_APP='record.py'            # monitorējamā programma priekš FORCE_REBOOT (ja tā nedarbojas)
# -------------------------------------

# Nomainīt direktoriju, kas sakrīt ar google drive saknes direktoriju (nepieciešams crontab)
cd $DIR
function do_gdrive_sync()
{
    # Pārbauda, vai eksistē SYNC_DIR direktorija
    if [ ! -d "$DIR/$SYNC_DIR" ] ; then
        echo "ERROR   - Local Folder $DIR/$SYNC_DIR Does Not Exist"
        echo "          Please Check SYNC_DIR variable and/or Local Folder PATH"
        exit 1
    fi

    # Pārbauda, vai ir sinhronizējamas datnes SYNC direktorijā
    ls -1 $DIR/$SYNC_DIR/$FILES_TO_SYNC > /dev/null 2>&1
    if [ ! "$?" = "0" ] ; then
        echo "ERROR   - No Matching $FILES_TO_SYNC Files Found in $DIR/$SYNC_DIR"
        exit 1
    fi

    # Pārbaude vai eksistē attiecīga attālinātā direktorija google drive
    # un, ja nē, tad izveido to
    echo "STATUS  - Check if Remote Folder /$SYNC_DIR Exists"
    echo "------------------------------------------"
    /usr/local/bin/gdrive file-id $SYNC_DIR
    if [ ! $? -eq 0 ] ; then
        echo "------------------------------------------"
        echo "STATUS  - Creating Remote Folder /$SYNC_DIR"
        echo "------------------------------------------"
        /usr/local/bin/gdrive new --folder $SYNC_DIR
        /usr/local/bin/gdrive file-id $SYNC_DIR
        if [ $? -eq 0 ] ; then
            echo "------------------------------------------"
            echo "STATUS  - Successfully Created Remote Folder /$SYNC_DIR"
        else
            echo "------------------------------------------"
            echo "ERROR   - Problem Creating Remote Folder $SYNC_DIR"
            echo "          Please Investigate Problem"
            exit 1
        fi
    fi
    echo "------------------------------------------"
    echo "STATUS  - Start gdrive Sync ...."
    echo "STATUS  - Local Source Folder - $DIR/$SYNC_DIR"
    echo "STATUS  - Remote Destn Folder - /$SYNC_DIR"
    echo "STATUS  - Files $FILES_TO_SYNC"
    echo "STATUS  - Running  This May Take Some Time ....."
    echo "STATUS  - sudo /usr/local/bin/gdrive push -no-prompt -ignore-conflict $SYNC_DIR/$FILES_TO_SYNC"
    echo "------------------------------------------"
    date
    START=$(date +%s)
    sudo /usr/local/bin/gdrive push -no-prompt -ignore-conflict $SYNC_DIR/$FILES_TO_SYNC
    if [ $? -ne 0 ] ;  then
        # Pārbauda, vai gdrive sync process ir bijis veiksmīgs
        date
        echo "------------------------------------------"
        echo "ERROR   - gdrive Sync Failed."
        echo "          Possible Cause - See gdrive Error Message Above"
        echo "          Please Investigate Problem and Try Again"
    else
        # Ja veiksmīgs, tad parāda laiku un izdzēš sync datni, iesāk OpenALPR procesu un datubāzes datnes izveidi
        date
        END=$(date +%s)
        DIFF=$((END - START))
        echo "------------------------------------------"
        echo "STATUS  - $0 Completed Successfully"
        echo "STATUS  - Processing Took $DIFF seconds"
        if [ -e $SYNC_FILE_PATH ] ; then
            echo "STATUS  - Deleting Sync Lock File $SYNC_FILE_PATH"
            rm -f $SYNC_FILE_PATH
			# inicializē automašīnas numura atpazīšanu (OpenALPR) katrai attēla datnei direktorijā
			for file in "$DIR/$SYNC_DIR/"*.jpg; do
				# iegūst datnes nosaukumu bez paplašinājuma un ieraksta mainīgajā full_fn
				full_fn=${file##*/}
				# igūst tikai datnes nosaukumu bez paplašinājuma un ceļa uz datni, ieraksta mainīgajā fn
				fn=${full_fn%.*}
				# atpazīst automašīnas numuru attēlā un ieraksta rezultātu *.txt datnē
				alpr -c eu $file > $DIR/$SYNC_DIR/$fn.txt
				# izgriež datus par auto numuru no OpenALPR izvaddatnes *.txt 2 rindas
				car_num=$(sed -r 's|.*- (.*)confidence.*|\1|' $DIR/$SYNC_DIR/$fn.txt | sed '2q;d')
				# izveido datni log.csv, izmantojot šodienas datumu kā prefiksu formātā Y-M-D 
				# (>, ja tāda neeksistē) un ievada/pievieno (>>, ja eksistē) datus par atpazīto auto numuru
				nowdt=$(date +"%Y-%m-%d_%H-%M-%S")
				now=$(date +"%Y-%m-%d")
				log_file="$now"_log.csv
				if [ ! -e $DIR/$SYNC_DIR/$log_file ]; then
					echo $fn,$car_num > $DIR/$SYNC_DIR/$log_file
				else
					echo $fn,$car_num >> $DIR/$SYNC_DIR/$log_file
				fi
				# pārvieto apstrādāto attēla failu un auto numura atpazīšanas izvaddatus *.txt uz direktoriju $PROC_DIR
				mv $file $DIR/$PROC_DIR/
				mv $DIR/$SYNC_DIR/$fn.txt $DIR/$PROC_DIR/
			done		
        fi
    fi
}

# pārbauda, vai gdrive jau darbojas, lai izvairītos no vairākām instancēm
if [ -z "$(pgrep -f gdrive)" ] ; then
    if [ $CHECK_FOR_SYNC_FILE ] ; then
        echo "STATUS  - Script Variable Setting CHECK_FOR_SYNC_FILE=true"
        if [ -e $SYNC_FILE_PATH ] ; then
            # Palaiž gdrive datnēm, kas atrodas direktorijā $SYNC_DIR
            echo "STATUS  - Found File $SYNC_FILE_PATH"
            do_gdrive_sync
        else
            echo "STATUS  - File Not Found $SYNC_FILE_PATH"
            echo "STATUS  - No Files to Sync at this Time."
        fi
    else
        echo "STATUS  - Script Variable Setting CHECK_FOR_SYNC_FILE=false"
        echo "WARNING - No Sync Lock File $SYNC_FILE_PATH Required"
        do_gdrive_sync
    fi
else
    # ja gdrive jau darbojas, tad pārbauda, cik ilgi un iznīcina procesu, ja ir sasniegts laika limits
    GDRIVEPID=$(pgrep gdrive)
    if [ -z "$(sudo ps axh -O etimes | grep gdrive | grep -v grep | sed 's/^ *//'| awk '{if ($2 >= 4000) print $1}')" ]
    then
        RUNTIME=$(sudo ps axh -O etimes | grep gdrive | grep -v grep | sed 's/^ *//' | awk '{if ($2 > 0) print $2}' | head -1)
        echo "STATUS  - Another sync.sh has run for "$RUNTIME" seconds."
        echo "STATUS  - Will kill if greater than 4000 seconds."
        echo "STATUS  - gdrive PID is $GDRIVEPID"
    else
        echo "WARNING - gdrive has run longer than 4000 seconds so kill PID $GDRIVEPID"
        echo "          Killing $GDRIVEPID in 5 seconds"
        sleep 5
        sudo kill $GDRIVEPID
    fi
fi

if $FORCE_REBOOT ; then  # pārbauda, vai ir nepieciešana restartēšana
    echo "------------------------------------------"
    echo "STATUS  - Check $WATCH_APP Run Status ..."
    if [ -z "$(pgrep -f $WATCH_APP)" ] ; then
        echo "STATUS  - $WATCH_APP is NOT Running so reboot"
        echo "WARNING - Reboot in 15 seconds Waiting ...."
        echo "          ctrl-c to Abort Reboot."
        sleep 10
        echo "WARNING - Rebooting in 5 seconds"
        sleep 5
        sudo reboot
    else
        APP_PID=$(pgrep -f $WATCH_APP)
        echo "STATUS  - $WATCH_APP is Running PID is $APP_PID"
    fi
fi
echo ""
echo "Done ..."
exit