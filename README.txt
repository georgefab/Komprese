P﻿oznámky k řešení
Pár poznámek k postupu úvah vkládám před vlastní README, protože když udělám samostatný soubor poznámky, tak si je možná nikdo nepřečte a chtěl bych pár věcí vysvětlit.
1) V zadání admin chce komprimovat v konkrétním adresáři. Když dnes potřebuje jeden, tak za měsíc bude potřebovat jiný, takže řešení dělám konfigurovatelné. Každý job bude mít vlastní konf soubor, který se předá jako jediný parametr skriptu
2) Když připustím více adresářů, tak se mění i každých 30 dní na libovolný počet dnů, protože každý adresář se bude plnit vlastním tempem.
3) Požadavek je komprimovat v jednom adresáři. Přidání rekurzivního procházení už není tolik práce navíc a pravděpodobně si tím ulehčím práci, protože to za měsíc nebudu muset dodělávat.
4) Vyloučení .gz souborů, které už jsou produktem dřívějších jobů je nezbytnost. Když umožním práci s libovolným adresářem, tak nemůžu nic předpokládat o jeho obsahu. Můžou tam jiné programy produkovat prakticky cokoli. Takže vynechání .gz je lepší řešit obecně jako vynechání všech přípon co si admin nadefinuje v configu.
5) Po kompresi původní file odstraním. Proto to děláme. Ale je velmi pravděpodobná situace, že nějaký program generuje svůj log nebo jiný file se stále stejným názvem. Když mu ho odstraním, tak ho zase založí. Ten pak při nové kompresi přepíše starý .gz, pokud nebudou nějak rozlišené. Nejjednodušší je označit je suffixem z data komprese. Ale nechci to adminovy vnucovat, takže v konfiguráku si sám nastaví, jestli přidávat suffix k původnímu názvu.
6) Po skončení jobu je volitelně zaslána notifikace adminovy. Zřídil jsem pro testovací účely účet na seznamu (viz konfigurační soubor). Defaultně je notifikace zapnuta, ale v případě třeba blokace portu ji vypněte.
7) cron neumí splnit požadavek každých 30 dní. Přesněji umí dvě věci
-- spustit úlohu každý 30-tý den v měsíci  0 0 30 * * 
Toto řešení by selhalo v únoru, který má méně dnů než 30
-- dále umí každý N-tý interval ve spojení s rozsahem např. každý 5-tý den v měsíci by byl 0 0 */5 * *
Ale každý 30-tý den v měsíci by vlastně přešel do předchozího způsobu a opět by se to únoru pokazilo
-- Takže závěr je, že si to musí program sám hlídat, aby komprimoval vždy více než 30 dní po předchozí komprimaci. Píši více, protože je potřeba pamatovat i na situaci, kdy v přesně 30-tý den bude server nefunkční. Potom je potřeba udělat to v nejbližším možném termínu po znovuspuštění.
8) Časová známka se dělá až po skončení celého jobu. Takže pokud spadne server upřestřed práce skriptu, tak po restartu se dodělá.
9) Všechny testy jsou uložené v jednom souboru. Zasloužili by si rozdělit do více, ale nechtěl jsem to komplikovat tomu kdo to bude prohlížet.
10) Testy si uklízejí prostředí adresáře, kde se komprimuje a protože neběží popořadě, tak i když dojde skutečně ke kompresi, tak další testy soubory opět smažou. Měřitkem je tedy pouze to, jestli test prošel, nikoli, že by tam komprimované soubory byly vidět po skončení testů. Jedině při explicitním spuštění jediného testu test_compression tam zůstane všechno zachované.

POZOR protože se při testech uklízí a job1.conf je nastaven na /var/log ,tak při spuštění dojde k vymazání obsahu!!! Pokud toto nechcete, tak zkopírujte job1.conf na job2.conf a v něm nastavte jiný počáteční adresář 
a proveďte testy v něm

11) Předpokládám, že testy budou spouštěny z adresáře, ve kterém se nechází skript a testy, takže nejsou řešeny cesty nijak. Naopak při spuštění z cronu je přepnutí do pracovního adresáře skriptu vyřešeno.
12) Neznám firemní kulturu, jestli pracujete v angličtině nebo češtině. Takže jsem zvolil kompromis. Programování je angličtině a readme se mi nechtělo překládat, takže v češtině. 
----------------------------------
README

Compressor je třída, která provádí komprimaci souborů do formátu gzip v zadaném adresáři resp. i jeho podadresářích, pokud je to požadováno.

INSTALACE
Do libovolného adresáře umístit soubor compressor.py, notification.py a jeho konfigurační soubor job1.conf .
Přístupová práva je potřeba nastavit podle konkrétního adresáře, který se bude zpracovávat.
Pro /var/log protože jsou zde logy usera root, tak jediná volba je nastavit vlastnictví taky pro uživatele root, aby skript měl možnost odstranit zkomprimované soubory.
Přepněte se do uživatele root a nastavte práva a vlastníka a skupinu
chmod 550 compressor.py
chmod 550 notification.py
chmod 660 job1.conf
sudo chown root compressor.py
sudo chown root notification.conf
sudo chown root job1.conf
sudo chgrp root compressor.py
sudo chgrp root notification.py
sudo chgrp root job1.conf


V případě vytváření dalšího jobu zkopírujte job1.conf jako job[N].conf
Soubor upravte podle potřeb viz. sekce užití

UŽITÍ

1) Uživateli root nastavte crontab
crontab -e root

Zadejte každodenní spouštění úlohy v požadovaný čas. (Skript si sám zjistí, jestli uběhla doba dle konfigurace od poslední komprese.)
 0 1 * * * python3 /full_absolute_path_to_script/compressor.py job1.conf

2) Úprava konfigurace
Každá úloha má samostatný konfigurační soubor. Název souboru je libovolný, ale doporučuji pro přehlednost formát nazev_ulohy[number_ulohy].conf

parametr "job_name": 
libovolný řetězec vyjadřující nazev úlohy např. "job1"
každá úloha má jedinečný název
k tomuto názvu se potom váže automaticky vytvořený log [job_name].log
a také časová známka v souboru [job_name]timestanm.log
(oboje vzikne po prvnim sputštění v adresáři skriptu)

parametr "job_days_step": 
počet dní od poslední komprese, aby se opět komprimovalo (dle zadání 30)

parametr "direcrory"
adresář, ve kterém se má začít hledání souborů (dle zadání /var/log)

parametr "recursive": 
určuje zda procházet podadresáře
povolené hodnoty true nebo false

parametr "exclude_ext": [".gz", ".Z", ".gzip"]
určuje přípony souborů, které se NEMAJI komprimovat
povinně zachovejte .gz

parametr "add_date_suffix":
určuje zda přidávat na konec názvu souboru, ještě před .gz suffix ve tvaru -YYYY-mm-dd
např. ahoj.txt je po kompresi ahoj.txt-2019-11-26.gz
povolené hodnoty true nebo false  
pokud není důvod ke změně, tak doporučuji ponechat true 

parametr "inform_owner": 
Určuje, jestli admin chce dostávat email
povolené hodnoty true nebo false

Pro účely testování je založený demo účet na seznamu. 
Parametry jsou samovysvětlující.
parametr "sender_email": "test123comp@seznam.cz",

parametr "email_passwd": "abdtrewiuo",

parametr "receiver_email": "test123comp@seznam.cz",

parametr "ssl_port":465,

parametr "smtp_server": "smtp.seznam.cz"
  