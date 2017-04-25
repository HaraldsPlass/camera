#!/usr/bin/python

# Šī (record.py) ir kustības sensora programma, kas analizē pikseļu izmaiņas attēlā,
# lai noteiktu kustību. Kustības gadījumā tiek ģenerēti attēli, izmantojot datumu un laiku JPG datnes nosaukumā.

progVer = "ver 1.0"

import os
mypath=os.path.abspath(__file__)       # atrod pilnu šīs programmas ceļu - atrašanās vietu
baseDir=mypath[0:mypath.rfind("/")+1]  # izvelk tikai ceļa atrašanās vietu (izņemot skripta nosaukumu)
baseFileName=mypath[mypath.rfind("/")+1:mypath.rfind(".")]
progName = os.path.basename(__file__)

# Pārbauda vai eksistē konfigurācijas datne un importē to, ja eksistē.
# Izvada kļūdas paziņojumu, ja neeksistēCheck
configFilePath = baseDir + "config.py"
if not os.path.exists(configFilePath):
    msgStr = "ERROR - Missing config.py file - Could not find Configuration file %s" % (configFilePath)
    showMessage("readConfigFile", msgStr)
    quit()
else:
    # Nolasa konfigurācijas mainīgos no datnes config.py
    from config import *

if verbose:
    print("----------------------- Loading Python Libraries ----------------------------")
else:
    print("Note: verbose=False (Disabled) Set verbose=True to Display Detailed Messages.")

# importē pārējās python bibliotēkas, kas nepieciešamas tālāk programmas darbībai.
import sys
import glob
import time
import datetime
import picamera
import picamera.array
import numpy as np
import pyexiv2
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from fractions import Fraction
  
#==================================
#        Sistēmas mainīgie
# Nevajadzētu būt vajadzībai mainīt
#==================================

SECONDS2MICRO = 1000000    # Tiek izmantots, lai konvertētu sekundes uz mikrosekundēm
nightMaxShut = int(nightMaxShut * SECONDS2MICRO)  # default=5 sec 
nightMinShut = int(nightMinShut * SECONDS2MICRO)  # zemākais kameras slēgšana iestatījums pārejai no dienas uz nakti (vai otrādāk)
testWidth = 128            # rgb attēlu straumes platums, ko izmanto kustības sensora un dienas / nakts izmaiņām
testHeight = 80            # rgb attēlu straumes augstums, ko izmanto kustības sensora un dienas / nakts izmaiņām
daymode = False            # default - pēc noklusējuma vienmēr vajadzētu būt False
progNameVer = "%s %s" %(progName, progVer)
motionPath = baseDir + motionDir  # Šajā direktorijā tiks saglabāti attēli pēc kustības
motionNumPath = baseDir + motionPrefix + baseFileName + ".dat"  # datne *.dat, lai saglabātu mainīgā currentCount lielumu
timelapsePath = baseDir + timelapseDir  # Šajā direktorijā paredzēts glabāt Time Lapse (laika sprīža) attēlus pēc kustības
timelapseNumPath = baseDir + timelapsePrefix + baseFileName + ".dat"  # datne *.dat, lai saglabātu mainīgā currentCount lielumu
lockFilePath = baseDir + baseFileName + ".sync"
 
#------------------------------------------------------------------------------------------
def shut2Sec (shutspeed):
    shutspeedSec = shutspeed/float(SECONDS2MICRO)
    shutstring = str("%.3f sec") % ( shutspeedSec )
    return shutstring
    
#------------------------------------------------------------------------------------------   
def showTime():
    rightNow = datetime.datetime.now()
    currentTime = "%04d%02d%02d_%02d:%02d:%02d" % (rightNow.year, rightNow.month, rightNow.day, rightNow.hour, rightNow.minute, rightNow.second)
    return currentTime    
    
#------------------------------------------------------------------------------------------
def showMessage(functionName, messageStr):
    if verbose:
        now = showTime()
        print ("%s %s - %s " % (now, functionName, messageStr))
    return
    
#------------------------------------------------------------------------------------------
def showDots(dotcnt):
    if motionOn and verbose:
        dotcnt += 1
        if dotcnt > motionMaxDots + 2:
            print("")
            dotcnt = 0
        elif dotcnt > motionMaxDots:
            print("")        
            stime = showTime() + " ."
            sys.stdout.write(stime) 
            sys.stdout.flush()
            dotcnt = 0
        else:            
            sys.stdout.write('.')
            sys.stdout.flush()
    return dotcnt
    
#------------------------------------------------------------------------------------------
def checkConfig():
    if not motionOn and not timelapseOn:
        msgStr = "Warning - Both Motion and Timelapse are turned OFF - motionOn=%s timelapseOn=%s"
        showMessage("checkConfig", msgStr)
    return 
    
#------------------------------------------------------------------------------------------
def logToFile(dataToAppend):
    if logDataToFile:
        logFilePath = baseDir + baseFileName + ".log"
        if not os.path.exists(logFilePath):
            open(logFilePath, 'w').close()
            msgStr = "Create New Data Log File %s" % logFilePath
            showMessage("  logToFile", msgStr)
        filecontents = dataToAppend
        f = open(logFilePath, 'a')
        f.write(filecontents)
        f.close()
    return
     
#------------------------------------------------------------------------------------------
def displayInfo(motioncount, timelapsecount):
    if verbose:
        print("")
        print("Note: To Send Full Output to File Use command -   python -u ./%s | tee -a log.txt" % progName)
        print("      Set logDataToFile=True to Send checkIfDay Data to File %s.log" % progName)
        print("")
        print("%s" % progNameVer)     
        print("-------------------------------------- Settings ----------------------------------------------")
        print("Config File .. Title=%s" % configTitle)
        print("               config-template filename=%s" % configName)
        print("Image Info ... Size=%ix%i   Prefix=%s   VFlip=%s   HFlip=%s   Preview=%s" % (imageWidth, imageHeight, imageNamePrefix, imageVFlip, imageHFlip, imagePreview))
        shutStr = shut2Sec(nightMaxShut)
        print("    Low Light. twilightThreshold=%i  nightMaxShut=%s  nightMaxISO=%i   nightSleepSec=%i sec" % (twilightThreshold, shutStr, nightMaxISO, nightSleepSec))
        print("    No Shots . noNightShots=%s   noDayShots=%s" % (noNightShots, noDayShots))       
        print("Motion ....... On=%s  Prefix=%s  threshold=%i(How Much)  sensitivity=%i(How Many)"  % (motionOn, motionPrefix, threshold, sensitivity))
        print("               forceTimer=%i min(If No Motion)"  % (motionForce/60))
        print("               Number of previous images to use to check for motion =%i"  % (motionAverage))
        print("               Use video port for motion image capture? %s"  % (useVideoPort))
        print("               motionPath=%s" % (motionPath))
        if motionQuickTLOn:
            print("    Quick TL . motionQuickTLOn=%s   motionQuickTLTimer=%i sec  motionQuickTLInterval=%i sec (0=fastest)" % (motionQuickTLOn, motionQuickTLTimer, motionQuickTLInterval))
        else:
            print("    Quick TL . motionQuickTLOn=%s  Quick Time Lapse Disabled" % (motionQuickTLOn))                   
        print("Time Lapse ... On=%s  Prefix=%s   Timer=%i sec   timeLapseExit=%i sec (0=Continuous)" % (timelapseOn, timelapsePrefix, timelapseTimer, timelapseExit)) 
        print("               timelapsePath=%s" % (timelapsePath))
        if createLockFile:
            print("gdrive Sync .. On=%s  Path=%s  Note: syncs for motion images only." % (createLockFile, lockFilePath))  
        print("Logging ...... verbose=%s (Details to Console)    logDataToFile=%s" % ( verbose, logDataToFile ))
        print("               logfilePath=%s" % ( baseDir + baseFileName + ".log" ))
        print("------------------------------------ Log Activity --------------------------------------------")
    checkConfig()        
    return            
    
#------------------------------------------------------------------------------------------
def checkImagePath():
    # Pārbauda attēlu direktorijas un izveido tās, ja tās jau neeksitē
    if motionOn:
        if not os.path.isdir(motionPath):
            msgStr = "Creating Image Motion Detection Storage Folder" + motionPath
            showMessage ("checkImagePath", msgStr)
            os.makedirs(motionPath)
    if timelapseOn:
        if not os.path.isdir(timelapsePath):
            msgStr = "Creating Time Lapse Image Storage Folder" + timelapsePath
            showMessage ("checkImagePath", msgStr)
            os.makedirs(timelapsePath)
    return
    
#------------------------------------------------------------------------------------------
def getCurrentCount(numberpath, numberstart):
    # Izveido datni *.dat, lai saglabātu mainīgo currentCount vai nolasītu datni, ja tā jau eksistē
    # Izveido numberPath datni, ja tā neeksistē
    if not os.path.exists(numberpath):
        msgStr = "Creating New File " + numberpath + " numberstart=" + str(numberstart)
        showMessage("getCurrentCount", msgStr)   
        open(numberpath, 'w').close()
        f = open(numberpath, 'w+')
        f.write(str(numberstart))
        f.close()
    # Nolasa numberPath datni, lai iegūtu pēdējo ciparu pēc kārtas
    with open(numberpath, 'r') as f:
        writeCount = f.read()
        f.closed
        try:
            numbercounter = int(writeCount)
        except ValueError:   # Atrasta bojāta datne *.dat, jo nevar konvertēt uz integer
            # Mēģina noteikt, vai šī ir kustība vai timelapse (laika sprīdis pēc noklusējuma konfigurācijas datnē netiek izmantots)
            if numberpath.find(motionPrefix) > 0:
                filePath = motionPath + "/*.jpg"
                fprefix = motionPath + motionPrefix + imageNamePrefix
            else:
                filePath = timelapsePath + "/*.jpg"
                fprefix = timelapsePath + timelapsePrefix + imageNamePrefix
            try:
               # Skenē visjaunāko datni attēlu direktorijā un mēģina iegūt numbercounter
                newest = max(glob.iglob(filePath), key=os.path.getctime)
                writeCount = newest[len(fprefix)+1:newest.find(".jpg")]
            except:
                writeCount = numberstart
            try:
                numbercounter = int(writeCount)+1
            except ValueError:
                numbercounter = numberstart
            msgStr = "Invalid Data in File " + numberpath + " Reset numbercounter to " + str(numbercounter)
            showMessage("getCurrentCount", msgStr)
        f = open(numberpath, 'w+')
        f.write(str(numbercounter))
        f.close()
        f = open(numberpath, 'r')
        writeCount = f.read()
        f.closed
        numbercounter = int(writeCount)
    return numbercounter
    
#------------------------------------------------------------------------------------------
def postImageProcessing(filename):
    # Šo izmanto, ja ir nepieciešams parādīt laika tekstu tieši uz attēla
    rightNow = datetime.datetime.now()
    if createLockFile and motionOn:
        createSyncLockFile(filename)
    
#------------------------------------------------------------------------------------------
def getImageName(path, prefix):
    # veido attēlu datņu nosaukumus, izmantojot datetime yyyymmdd-hhmmss formātā
    rightNow = datetime.datetime.now()
    filename = "%s/%s%04d%02d%02d-%02d%02d%02d.jpg" % ( path, prefix ,rightNow.year, rightNow.month, rightNow.day, rightNow.hour, rightNow.minute, rightNow.second)     
    return filename    
    
#------------------------------------------------------------------------------------------
def takeDayImage(filename):
    # Uzņem dienas attēlu, izmantojot exp=auto un awb=auto
    with picamera.PiCamera() as camera:
        camera.resolution = (imageWidth, imageHeight) 
        time.sleep(0.1)   # iemieg uz īsu brīdi, lai kamera varētu iegūt korekcijas iestatījumus
        if imagePreview:
            camera.start_preview()
        camera.vflip = imageVFlip
        camera.hflip = imageHFlip
        camera.rotation = imageRotation # Labāk lietot mainīgos imageVFlip un imageHFlip
        # dienas Automātiskais režīms
        camera.exposure_mode = 'auto'
        camera.awb_mode = 'auto'
        camera.capture(filename, use_video_port=useVideoPort)
    msgStr = "Size=%ix%i exp=auto awb=auto %s"  % (imageWidth, imageHeight, filename)
    dataToLog = showTime() + " takeDayImage " + msgStr + "\n"
    logToFile(dataToLog)
    showMessage("  takeDayImage", msgStr)
    return
     
#------------------------------------------------------------------------------------------
def takeNightImage(filename):
    dayStream = getStreamImage(True)
    dayPixAve = getStreamPixAve(dayStream)
    currentShut, currentISO = getNightCamSettings(dayPixAve)
    # Uzņemt vājas gaismas - nakts attēlu (ieskaitot krēslas zonas)
    with picamera.PiCamera() as camera:
        # Uzņemt Zemas Gaismas Attēlu
        # Uzstādīt framerate 1/6 fps, pēc tam iestatīt aizveri
        camera.resolution = (imageWidth, imageHeight)
        if imagePreview:
            camera.start_preview()
        camera.vflip = imageVFlip
        camera.hflip = imageHFlip
        camera.rotation = imageRotation # Labāk lietot mainīgos imageVFlip un imageHFlip
        camera.framerate = Fraction(1, 6)
        camera.shutter_speed = currentShut
        camera.exposure_mode = 'off'
        camera.iso = currentISO
        # Dodiet kameram pietiekami ilgu laiku, lai nomērītu AWB
        # (tā vietā var arī lietot fiksētu AWB)
        time.sleep(nightSleepSec)
        camera.capture(filename)
    shutSec = shut2Sec(currentShut)
    msgStr = "Size=%ix%i dayPixAve=%i ISO=%i shut=%s %s"  %( imageWidth, imageHeight, dayPixAve, currentISO, shutSec, filename )
    dataToLog = showTime() + " takeNightImage " + msgStr + "\n"
    logToFile(dataToLog)
    showMessage("  takeNightImage", msgStr)
    return        

#------------------------------------------------------------------------------------------
def takeQuickTimeLapse(motionPath, imagePrefix, daymode, motionNumPath):
    msgStr = "motion Quick Time Lapse for %i sec every %i sec" % (motionQuickTLTimer, motionQuickTLInterval)
    showMessage("Main", msgStr)
    checkTimeLapseTimer = datetime.datetime.now()
    keepTakingImages = True
    filename = getImageName(motionPath, imagePrefix)
    while keepTakingImages:
        yield filename
        rightNow = datetime.datetime.now()
        timelapseDiff = (rightNow - checkTimeLapseTimer).total_seconds()
        if timelapseDiff > motionQuickTLTimer:
            keepTakingImages=False
        else:
            filename = getImageName(motionPath, imagePrefix)
            time.sleep(motionQuickTLInterval)

#------------------------------------------------------------------------------------------
def createSyncLockFile(imagefilename):
    # Ja nepieciešams, izveido bloķēšanas datni (lock file), lai norādītu apstrādāt nepieciešamās datnes
    if createLockFile:
        if not os.path.exists(lockFilePath):
            open(lockFilePath, 'w').close()
            msgStr = "Create gdrive sync.sh Lock File " + lockFilePath
            showMessage("  createSyncLockFile", msgStr)
        rightNow = datetime.datetime.now()
        now = "%04d%02d%02d-%02d%02d%02d" % ( rightNow.year, rightNow.month, rightNow.day, rightNow.hour, rightNow.minute, rightNow.second )
        filecontents = now + " createSyncLockFile - "  + imagefilename + " Ready to sync using sudo ./sync.sh command." 
        f = open(lockFilePath, 'w+')
        f.write(filecontents)
        f.close()
    return          
    
#------------------------------------------------------------------------------------------
def getStreamImage(isDay):
    # iegūst attēlu straumi atmiņā, balstoties uz dienas režīmu (daymode)
    with picamera.PiCamera() as camera:
        time.sleep(0.5)
        camera.resolution = (testWidth, testHeight)
        with picamera.array.PiRGBArray(camera) as stream:
            if isDay:
                camera.exposure_mode = 'auto'
                camera.awb_mode = 'auto' 
                camera.capture(stream, format='rgb', use_video_port=useVideoPort)
            else:
                # Uzņem zemas gaismas attēlu
                # Uzstāda kadrus sekundē uz 1/6fps, tad aizver slēģi
                # paātrina līdz 6s
                camera.framerate = Fraction(1, 6)
                camera.shutter_speed = nightMaxShut
                camera.exposure_mode = 'off'
                camera.iso = nightMaxISO
                # Dodiet kameram pietiekami ilgu laiku, lai nomērītu AWB
                # (tā vietā var arī lietot fiksētu AWB)
                time.sleep( nightSleepSec )
                camera.capture(stream, format='rgb')
            return stream.array
    
#------------------------------------------------------------------------------------------
def getStreamPixAve(streamData):
    # Aprēķināt vidējo pikseļu vērtības noteiktā plūsmā (izmanto, lai noteiktu dienas / nakts vai krēslas nosacījumus)
    pixAverage = int(np.average(streamData[...,1]))
    return pixAverage
    
#------------------------------------------------------------------------------------------
def getNightCamSettings(dayPixAve):
    # Aprēķināt attiecību starp slēdža un ISO vērtībām, pielāgojot tās
    if dayPixAve <= twilightThreshold:
        ratio = ((twilightThreshold - dayPixAve)/float(twilightThreshold)) 
        outShut = int(nightMaxShut * ratio)
        outISO  = int(nightMaxISO * ratio)
    else:
        ratio = 0.0
        outShut = nightMinShut
        outISO = nightMinISO 
    # veic dažas robežpārbaudes, lai izvairītos no iespējamām problēmām
    if outShut < nightMinShut:
        outShut = nightMinShut
    if outShut > nightMaxShut:
        outShut = nightMaxShut
    if outISO < nightMinISO:
        outISO = nightMinISO
    if outISO > nightMaxISO:
        outISO = nightMaxISO    
    msgStr = "dayPixAve=%i ratio=%.3f ISO=%i shut=%i %s" % ( dayPixAve, ratio, outISO, outShut, shut2Sec(outShut)) 
    showMessage("  getNightCamSettings", msgStr)
    return outShut, outISO
    
#------------------------------------------------------------------------------------------
def checkIfDay(currentDayMode, dataStream):
    # Mēģina noteikt, vai tā ir diena, nakts vai krēsla
    dayPixAverage = 0 
    if currentDayMode:
        dayPixAverage = getStreamPixAve(dataStream)
    else:
        dayStream = getStreamImage(True)
        dayPixAverage = getStreamPixAve(dayStream) 
        
    if dayPixAverage > twilightThreshold:
        currentDayMode = True
    else:
        currentDayMode = False
    return currentDayMode
    
#------------------------------------------------------------------------------------------
def timeToSleep(currentDayMode):
    if noNightShots:
       if currentDayMode:
          sleepMode=False
       else:
          sleepMode=True
    elif noDayShots:
        if currentDayMode:
           sleepMode=True
        else:
           sleepMode=False
    else:
        sleepMode=False    
    return sleepMode
    
#------------------------------------------------------------------------------------------
def checkForTimelapse (timelapseStart):
    # Pārbauda, vai timelapse taimeris ir beidzies
    rightNow = datetime.datetime.now()
    timeDiff = ( rightNow - timelapseStart).total_seconds()
    if timeDiff > timelapseTimer:
        timelapseStart = rightNow
        timelapseFound = True
    else:
        timelapseFound = False 
    return timelapseFound
    
#------------------------------------------------------------------------------------------
def checkForMotion(data1, data2):
    # Atrod kustību starp divām datu plūsmām, balstoties uz jutīguma (sensitivity) un sliekšņa (threshold) iestatījumiem
    motionDetected = False
    pixColor = 3 # red=0 green=1 blue=2 all=3  default=1
    if pixColor == 3:
        pixChanges = (np.absolute(data1-data2)>threshold).sum()/3
    else:
        pixChanges = (np.absolute(data1[...,pixColor]-data2[...,pixColor])>threshold).sum()
    if pixChanges > sensitivity:
        motionDetected = True
    if motionDetected:
        dotCount = showDots(motionMaxDots + 2)      # New Line        
        msgStr = "Found Motion - threshold=" + str(threshold) + " sensitivity=" + str(sensitivity) + " changes=" + str(pixChanges)
        showMessage("checkForMotion", msgStr)
    return motionDetected  
    
#------------------------------------------------------------------------------------------
def dataLogger():
    # Nomainiet main() ar šo funkciju, lai logotu dienas / nakts pixAve datnē
    # Tādā gadījumā mainīgajam logDataToFile ir jābūt True datnē config.py  
    # Var arī idzdzēst record.log datni, lai iztīrītu iepriekšējos log datus
    print("dataLogger - One Moment Please ....")
    while True:
        dayStream = getStreamImage(True)
        dayPixAverage = getStreamPixAve(dayStream)    
        nightStream = getStreamImage(False)
        nightPixAverage = getStreamPixAve(nightStream)
        logdata  = "nightPixAverage=%i dayPixAverage=%i twilightThreshold=%i  " % ( nightPixAverage, dayPixAverage, twilightThreshold )
        showMessage("dataLogger",logdata)
        now = showTime()        
        logdata = now + " " + logdata
        logToFile(logdata)
        time.sleep(1)
    return    
    
#------------------------------------------------------------------------------------------
def Main():
    # Galvenās programmas Main() inicializācijas un loģika cilpa
    dotCount = 0   # Skaitītājs priekš showDots() parādīšanas, ja nav atrasta kustība (sistēma strādā)
    checkImagePath()
    timelapseNumCount = 0
    motionNumCount = 0
    try:  # ja motionAverage nav iekļauta config datnē (lai tā darbojas ar iepriekšējām versijām)
        global motionAverage
        if motionAverage > 1:
            resetSensitivity = sensitivity*150   # nomainīto pikseļu skaits, lai izraisītu atiestatīšanu uz fona vidējo
            if resetSensitivity > testHeight*testWidth*2:
                resetSensitivity = testHeight*testWidth*2  # ierobežot resetSensitivity
        else:
            motionAverage = 1
    except NameError:
        motionAverage = 1
    try:
        global useVideoPort
        useVideoPort = useVideoPort
    except NameError:
        useVideoPort = False
    moCnt = "non"
    tlCnt = "non"
    if timelapseOn:
        if timelapseNumOn:
            timelapseNumCount = getCurrentCount(timelapseNumPath, timelapseNumStart)
            tlCnt = str(timelapseNumCount)
    displayInfo(moCnt, tlCnt)
    daymode = False
    data1 = getStreamImage(True).astype(float)  # Visām funkcijām ir jāstrādā ar float int vietā - vienkārši aizņem vairāk atmiņas
    daymode = checkIfDay(daymode, data1)
    data2 = getStreamImage(daymode)  # inicializē data2, lai lietotu to galvenajā (main) cilpā
    if not daymode:
        data1 = data2.astype(float)
    timelapseStart = datetime.datetime.now()
    checkDayTimer = timelapseStart
    checkMotionTimer = timelapseStart
    forceMotion = False   # Izmanto, lai piespiestu veidoties kustības attēlam, ja nav kustības priekš motionForce laiks pārsniegts
    msgStr = "Entering Loop for Time Lapse and/or Motion Detect  Please Wait ..."
    showMessage("Main", msgStr)
    dotCount = showDots(motionMaxDots)  # atiestata kustības punktiņus
    # Programmas galvenā cilpa (loop) sākas šeit. Izmantot Ctrl+C, lai izietu, ja programma tiek izpildīta no termināļa sesijas.
    while True:
        # izmanto data2, lai pārbaudītu daymode pret data1, kas var būt vidējais, kas mainās lēni, un data1 var neatjaunināties
        if daymode != checkIfDay(daymode, data2):  # ja daymode ir mainījusies, atiestata fonu, lai izvairītos no neesošas kustības (false motion trigger)
            daymode = not daymode
            data2 = getStreamImage(daymode)  # iegūst jaunu plūsmu
            data1 = data2.astype(float)    # atiestata (reset) fonu (background)
        else:
            data2 = getStreamImage(daymode)      # šis dabūt otro plūsmu kustības analīzei
        rightNow = datetime.datetime.now()   # atjauno rightNow laiku
        if not timeToSleep(daymode):  # Neuzņemt attēlus, ja noNightShots vai noDayShots iestatījums ir derīgs (validācija)
            if timelapseOn:
                takeTimeLapse = checkForTimelapse(timelapseStart)
                if takeTimeLapse:
                    timelapseStart = datetime.datetime.now()  # atiestata (reset) time lapse laiku
                    dotCount = showDots(motionMaxDots + 2)      # atiestata kustības punktus
                    msgStr = "Scheduled Time Lapse Image - daymode=" + str(daymode)
                    showMessage("Main", msgStr)    
                    imagePrefix = timelapsePrefix + imageNamePrefix            
                    filename = getImageName(timelapsePath, imagePrefix)
                    if daymode:
                        takeDayImage(filename)    
                    else:
                        takeNightImage(filename)
                    dotCount = showDots(motionMaxDots)                  
            if motionOn:
                # SVARĪGI: - Nakts kustības uztveršana var nedarboties ļoti labi
                # ņemot vērā ilgo ekspozīcijas laiku un vājo apgaismojumu (var mēģināt uzstādīt sarkanu zaļā vietā)
                # Tāpat var būt nepieciešams īpašs nakts slieksņa (threshold) un jutīguma (sensitivity) iestatījums (nepieciešama lielāka testēšana)
                motionFound = checkForMotion(data1, data2)
                if motionAverage > 1 and (np.absolute(data2-data1)>threshold).sum() > resetSensitivity:
                    data1 = data2.astype(float)
                else:
                    data1 = data1+(data2-data1)/motionAverage
                rightNow = datetime.datetime.now()
                timeDiff = (rightNow - checkMotionTimer).total_seconds()
                if timeDiff > motionForce:
                    dotCount = showDots(motionMaxDots + 2)      # Jauna Rinda   
                    msgStr = "No Motion Detected for " + str(motionForce / 60) + " minutes. Taking Forced Motion Image."
                    showMessage("Main", msgStr)
                    checkMotionTimer = rightNow
                    forceMotion = True
                if motionFound or forceMotion:
                    dotCount = showDots(motionMaxDots + 2)      # Jauna Rinda 
                    checkMotionTimer = rightNow
                    if forceMotion:
                        forceMotion = False            
                    imagePrefix = motionPrefix + imageNamePrefix 
                    # pārbauda, vai kustības Quick Time Lapse opcija ir ieslēgta (On). Šī opcija aizstāj motionVideoOn
                    if motionQuickTLOn and daymode:
                        filename = getImageName(motionPath, imagePrefix)      
                        with picamera.PiCamera() as camera:
                            camera.resolution = (imageWidth, imageHeight)
                            camera.vflip = imageVFlip
                            camera.hflip = imageHFlip
                            time.sleep(.1)
                            # izmanto pakāpienu, lai cilpotu laika sprīža (time lapse) secībā, bet tas nešķiet ātrāks, jo attēli tiek rakstīti
                            camera.capture_sequence(takeQuickTimeLapse(motionPath, imagePrefix, daymode, motionNumPath))
                            # motionNumCount = getCurrentCount(motionNumPath, motionNumStart)
                    else:                        
                        filename = getImageName(motionPath, imagePrefix)
                        if daymode:
                            takeDayImage(filename)
                        else:
                            takeNightImage(filename)
                        motionNumCount = postImageProcessing(filename)
                    if motionFound:
                        dotCount = showDots(motionMaxDots)           
                else:
                    dotCount = showDots(dotCount)  # parāda progresa punktus, ja nav noteikta kustība
    return
    
#------------------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        if debug:
            dataLogger()
        else:
            Main()
    finally:
        print("")
        print("+++++++++++++++++++++++++++++++++++")
        print("%s - Exiting Program" % progName)
        print("+++++++++++++++++++++++++++++++++++")
        print("")
