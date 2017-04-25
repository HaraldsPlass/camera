# Lietotāja Konfigurācija: mainīgo iestatījumi attēliem un programmas record.py darbībai
# Mērķis: Kustības Noteikšanas Kamera - Kustības Sensors
# Izveidots: 20-Feb-2017
# Autors: Haralds Plass, izmantojot atvērto kodu, ko publicējis Clude Pageau (https://github.com/pageauc/pi-timolo)
 
configTitle = "shoot default configuration motion and timelapse 720p images"
configName = "shoot-default-config"

# Šiem iestatījumiem ir jābūt False, ja skriptu darbina fonā, izmantojot /etc/init.d dēmonu
verbose = True             # Nosūta izvērstu programmas darbības informāciju uz konsoli. Iestata uz False, ja skriptu darbina, izmantojot dēmonu
logDataToFile = True       # reģistrē disgnostikas datus diska datnē vēlākai pārskatīšanai. Pēc noklusējuma (default) = False
debug=False                # Ieliek atkļūdošanas režīmā, atgriež pikseļu vidējos datus noskaņošanai

# Attēlu Iestatījumi
imageNamePrefix = ''  	   # Visu attēlu datņu priekšējais prefikss, piemēram, 'mo1-'
imageWidth = 1024          # Pilna izmēra attēla platums pikseļos, default=1024
imageHeight = 768          # Pilna izmēra attēla augstums pikseļos, default=768
imageVFlip = False         # Sagriezt attēlu Vertikāli, default=False
imageHFlip = False         # Sagriezt attēlu Horizontāli, default=False
imageRotation=90           # Sagriezt/Rotēt attēlu. Iespējamās vērtības: 0, 90, 180 & 270. Default=0. Uzstādījums 90 uzlikts dēļ CCTV kameras izgriezuma cauruma.
imagePreview = False       # Attēla parādīšana uz Raspberry Pi pieslēgta monitora. default=False
noNightShots = False       # Neuzņemt attēlus naktī. default=False
noDayShots = False         # Neuzņemt attēlus dienā. default=False  

# Vāja apgaismojuma Iestatījumi
nightMaxShut = 5.5         # default=5.5 sec Lielākais kameras slēgšanas ekspozīcijas laiks.
                           # SVARĪGI, ka 6 sec darbojas dažreiz, bet reizēm var bloķēt RPI tā, ka būs nepieciešama restartēšana un attīrīšana
nightMinShut = .001        # default=.002 sec Mazākais kameras slēgšanas ekspozīcijas laiks, lai pārietu no dienas uz nakti vai otrādāk
nightMaxISO = 800          # default=800  Maksimālais kameras ISO nakts iestatījums
nightMinISO = 100          # mazākais kameras ISO iestatījums, lai pārietu no dienas uz nakti vai otrādāk
nightSleepSec = 10         # default=10 sekundes - Laika periods, lai ļautu kamerai aprēķināt vājas gaismas AWB
twilightThreshold = 40     # default=40 Gaismas līmenis, lai darbinātu dienas / nakts pāreju pie krēslas

# web lapas iestatījumi
webDir = "/home/pi/web/"   # direktorija, kur glabājas web lapas skripts
webImageDir = "/home/pi/web/images/" # direktorija, kur glabājas attēli
webImageFileName = "live.jpg" # attēla datnes nosaukums aktuālajam kameras uzņemtajam attēlam
webImage = "/home/pi/web/images/live.jpg" # direktorija un aktuālā attēla nosaukums kopā

# Kustības Noteikšanas Iestatījumi
motionOn = True            # True = kustības noteikšana ir ieslēgta.  False = nenoteikt kustību
motionPrefix = ""          # Kustības Noteikšanas ģenerēto attēlu prefikss
motionDir = "mo1"          # Direktorija, kurā tiks glabāti attēli
threshold = 50             # Cik daudz pikseļiem ir jāizmainās, lai būtu ieskaitīta kustība. default=10 (1-200). set=20, 200 bija par daudz
sensitivity = 700          # Izmainījušos pikseļu skaits, lai sāktu darboties kustības sensors - attēlu ģenerēšana. default=300 set=300, 3000 bija par daudz (nebija kustības)
motionAverage = 1          # Attēlu skaits, kas vidēji jāpārbauda, lai noteiktu kustību: 1 = vienkārši izmanto pēdējo attēlu. Default=100
useVideoPort = False       # Izmanto video portu, lai uzņemtu attēlus - ātrāk nekā attēlu ports. Default=False
motionQuickTLOn = False    # Ja uzstāda True, tad uzņem ātros time lapse secības attēlus viena attēla vietā (pārraksta motionVideoOn)
motionQuickTLTimer = 1     # Ilgums sekundēs, kas nepieciešams, lai uzņemtu ātros time lapse secības attēlus pēc sākotnējās kustības noteikšanas. default=10
motionQuickTLInterval = 0  # Laiks starp katru Quick Time lapse laika plūduma attēlu. 0 ir cik ātri vien iespējams
motionForce = 60 * 60      # Piespiež uzņemt vienu kustības attēlu, ja nav noteikta kustība norādītajās sekundēs. default=60*60
motionNumOn = False        # True=On (datņu nosaukumu pēc kārtas). Neizmantojam, jo izmantojam datums-laiks datnes nosaukumā. default=False
motionMaxDots = 100        # Kustības punktu skaits pirms jaunas rindas sākšanas
createLockFile = True      # default=False. Ja True, tad sync.sh izsauks gdrive, lai sinhronizētu datnes ar google drive tikai tad, ja eksistēs .sync datne
                           # Lock File tiek izmantots, lai noteiktu, vai ir uzģenerēti kustības attēli. Tas sync.sh var sinhronizēties fonā caur sudo crontab -e

# Time Lapse (laika sprīža) Iestatījumi
timelapseOn = False        # Ieslēdz timelapse. True=On  False=Off
timelapseTimer = 5 * 60    # Sekundes starp timelapse attēliem. default=5*60
timelapseDir = "tl4"       # Direktorija, kurā tiks glabāti Time Lapse attēli
timelapsePrefix = ""       # Timelapse attēlu prefikss
timelapseExit = 0 * 60     # Aizvērs programmu pēc noteiktām sekundēm. 0=Continuous  default=0
timelapseNumOn = False     # True=On (datņu nosaukumi, veidoti no cipara pēc kārtas). Neizmantojam, jo izmantojam datums-laiks datnes nosaukumā. default=False.

