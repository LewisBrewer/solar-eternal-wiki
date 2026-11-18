"""The battles whose wreckage stays in the system view, with the ships each side lost.

Each battle: (system, year, where, article slug, title, sides). `where` is a body index (1-based,
or [planet, moon]), a world's name, or 'pillai' for the jump limit. A side is
(name, style, hulls drawn as debris, losses as the article or the book gives them).
Monoliths are counted from the clans' roll (atlas/clans.py) and added to the Khanate's side
by the wreck that shares the battle's system and date.
Styles: human, conf (the Martian-Jovian Confederation), voor, maweer, alien, fev (tributary hulls)."""

COAL = 'Terrestrial Coalition'; CONF = 'Martian-Jovian Confederation'; UNE = 'United Nations of Earth'
USR = 'Unified Solar Republic'; VOOR = 'Voor Legion'; KH = 'Red Khanate'

BATTLES = [
    # ---- the Solar War, in the Sun's system
    ('sol', 2225.53, 4, 'battle-of-hellas-gate', 'Battle of Hellas Gate', [
        ('European Federation', 'human', 4, '1 cruiser and 2 frigates destroyed; 1 battleship crippled; 30 strike craft'),
        (CONF, 'conf', 1, 'The Marat and the Danton damaged; 1 Yugantar damaged')]),
    ('sol', 2226.38, 4, 'battle-of-eos-rift', 'Battle of Eos Rift', [
        ('United States', 'human', 1, 'The Hornet damaged, 60 dead aboard'),
        (CONF, 'conf', 14, '5 cruisers destroyed and 2 disabled; 9 Yugantars')]),
    ('sol', 2227.89, [3, 0], 'battle-of-farside', 'Battle of Farside', [
        (COAL, 'human', 4, '4 escorts; Farside Station, with 3,000 aboard'),
        (CONF, 'conf', 7, '1 cruiser and 6 Yugantars')]),
    ('sol', 2227.70, [3, 0], 'raid-on-delambre', 'Raid on Delambre', [
        (COAL, 'human', 26, 'Delambre\'s security squadron of 22 cruisers and frigates; 4 hulls in dock'),
        (CONF, 'conf', 7, '2 cruisers, 4 corvettes and 1 dropship')]),
    ('sol', 2227.78, [3, 0], 'battle-of-procellarum', 'Battle of Procellarum', [
        ('United States', 'human', 3, '2 cruisers destroyed; 1 battleship crippled'),
        (CONF, 'conf', 3, '2 cruisers destroyed and 3 damaged')]),
    ('sol', 2230.00, 3, 'battle-of-the-tethers', 'Battle of the Tethers', [
        (COAL, 'human', 60, '23 capital ships; about 120 lesser hulls; 90 grid platforms; 5 tethers'),
        (CONF, 'conf', 40, '11 capital ships; about 80 lesser hulls')]),
    ('sol', 2232.18, [3, 0], 'battle-for-lunar-orbit', 'Battle for Lunar Orbit', [
        (COAL, 'human', 40, '11 capital ships; 40 escorts, six of them cruisers lost to mines on the first day'),
        (CONF, 'conf', 45, '8 Robespierre-class cruisers; 80 Yugantars')]),
    ('sol', 2239.28, 4, 'raid-on-bartolomeu', 'Raid on Bartolomeu', [
        (COAL, 'human', 26, '6 capital ships, the Enterprise and the Lexington among them; 20 escorts'),
        (CONF, 'conf', 40, 'The Daxian Ngata; 9 Robespierres; 40 Yugantars; 29 unfinished Daxians on the slips')]),
    ('sol', 2248.60, 5, 'himalia-raids', 'Himalia Raids', [
        (COAL, 'human', 16, '14 escorts and 2 cruisers'),
        (CONF, 'conf', 9, '9 Yugantars; most of the outer-moon depots and relays')]),
    ('sol', 2249.80, [5, 0], 'battle-for-io', 'Battle for Io', [
        (COAL, 'human', 30, 'The battleship Garibaldi; 2 Type 4 cruisers; 11 escorts; 50 dropships'),
        (CONF, 'conf', 30, '50 Yugantars')]),
    # ---- the Ciriban Gulf Conflict
    ('nomotar', 2333.57, 'pillai', 'ciriban-incident', 'Ciriban Incident', [
        (UNE, 'human', 1, 'The light cruiser Bactria; 40 strike craft'),
        (VOOR, 'voor', 3, 'One heavy cruiser and two destroyers (one towed home)')]),
    ('media', 2333.85, 'pillai', 'first-battle-of-media', 'First Battle of Media', [
        (UNE, 'human', 1, 'The corvette Focus; 2 frigates damaged; 300 strike craft'),
        (VOOR, 'voor', 9, '1 heavy cruiser; 8 destroyers')]),
    ('haedus', 2334.09, 'Indata Mog', 'battle-of-the-mog', 'Battle of the Mog', [
        (UNE, 'human', 13, '2 battleships, 1 light cruiser, 4 frigates, 6 corvettes; 900 strike craft'),
        (VOOR, 'voor', 40, '4 hearths, 14 heavy cruisers, 22 light cruisers, 70 destroyers')]),
    ('media', 2334.37, 'pillai', 'second-battle-of-media', 'Second Battle of Media', [
        (UNE, 'human', 40, 'The carrier Goliath; the light cruisers Evocati and Socii; 15 frigates; 31 corvettes; both platforms; the Oberon crippled'),
        (VOOR, 'voor', 40, '3 hearths, the Voor Aegis captured; 20 Harbingers; 60 destroyers')]),
    ('haedus', 2334.63, 'Indata Mog', 'fall-of-new-indata-mog', 'Fall of New Indata Mog', [
        (VOOR, 'voor', 1, 'The hearth Lethe, scuttled in orbit with 90,000 aboard')]),
    ('exedor', 2336.19, 'Hiverion', 'battle-of-exedor-2336', 'Battle of Exedor (2336)', [
        (UNE, 'human', 17, 'The battlecruiser Comet; the light cruiser Thorax; the frigate Celebes; the corvettes Churchill and Hood; 12 other escorts; 1,400 strike craft'),
        (VOOR, 'voor', 5, '5 hearths: the Avernus, Asphodel, Ember, Cinder and Pyre; the Hiverion holed along 2 kilometres')]),
    ('leesak', 2337.45, 'pillai', 'siege-of-hiverion', 'Leesak', [
        (UNE, 'human', 6, 'The corvette Firefly; 5 escorts; 600 strike craft'),
        (VOOR, 'voor', 4, '4 hearths')]),
    ('exedor', 2338.34, 'Hiverion', 'siege-of-hiverion', 'Fall of the Krakre', [
        (VOOR, 'voor', 5, 'The Hiverion and 4 hearths, with 130,000 aboard the Hiverion')]),
    # ---- the Red Khanate
    ('hwen', 2408.45, 'Hwen', None, 'The Dwaii fleet destroyed', [
        ('Dwaii', 'alien', 20, 'The Dwaii fleet, destroyed in a single engagement')]),
    ('aethos', 2422.45, 'Vur Duri', None, 'Fall of Vur Duri', [
        (VOOR, 'voor', 14, 'The last 14 hearths, destroyed or scattered on 9 June in the General\'s sortie; 200 platforms')]),
    ('exedor', 2427.62, 'Hiverion', 'hiverion', 'Fall of Hiverion', [
        (VOOR, 'voor', 7, 'The seven hearths that held Exedor\'s edge, the Vi Simni last, with the Council\'s presiding member aboard')]),
    ('myrum', 2428.50, 'pillai', None, 'Fall of Myrum', [
        (USR, 'human', 30, '60 hulls; three starforts')]),
    ('haedus', 2428.62, 'pillai', None, 'First Battle of Haedius', [
        (USR, 'human', 60, '220 of 520 hulls; the Vindications Vindication, Retribution and Resolve; 2 Ciribans; 7 of the ring\'s 11 stations; 7,000 strike craft'),
        (KH, 'fev', 30, '2 captured hearths; 14,000 tributary hulls; 3,000 prowlers')]),
    ('haedus', 2428.68, 'pillai', None, 'Second Battle of Haedius', [
        (USR, 'human', 12, 'Naval Station Paldron and its ring of stations')]),
    ('ciriban', 2429.30, 'pillai', 'siege-of-bounty', 'Bijou Nan Syèl La and Bounty', [
        (USR, 'human', 16, 'The Sector Council\'s relief convoy of 20 December 2429: 12 freighters and 4 frigates')]),
    ('saolea', 2434.20, 'pillai', 'saolea', 'Battle of Saolea', [
        (USR, 'human', 40, '140 hulls; the Vindications Endurance and Perseverance; 1 Ciriban; 3 forts; 120 platforms'),
        (KH, 'fev', 25, '1 captured hearth destroyed and 1 taken (The Hearth That Waits); 11,000 tributary hulls')]),
    ('talandra', 2441.35, 'pillai', 'talandra', 'First Battle of Talandra', [
        (USR, 'human', 60, '250 of 320 hulls: 10 Vindications, the Constancy last; 6 Ciribans; 40 battleships; 50 Sovereigns; 12,000 strike craft'),
        (KH, 'fev', 30, 'The last captured hearths; 20,000 tributary hulls')]),
    ('procyon', 2441.87, 'Landfall', 'battle-of-procyon-2441', 'Battle of Procyon (2441)', [
        (USR, 'human', 30, '80 hulls; 2 Vindications; every starfort and platform'),
        (KH, 'fev', 20, 'About 11,000 tributary hulls')]),
    ('yildun', 2444.44, 'Dauntless', 'battle-of-yildun', 'Battle of Yildun', [
        (USR, 'human', 40, '120 hulls; 7 of the 8 Vindications, the Defiance with Grand Admiral Kvoravich among them; all 3,000 platforms; 180 transports'),
        (KH, 'fev', 20, 'About 9,000 tributary hulls')]),
    ('sol', 2446.27, 5, None, 'Battle of Jupiter', [
        (USR, 'human', 40, '120 hulls; 2 Vindications; 1 Ciriban; the Bounty; 900 platforms; Callisto\'s fortress'),
        (KH, 'fev', 40, '80,000 tributary hulls; 200 hulks')]),
    ('sol', 2446.47, 'pillai', None, 'Vesta', [
        (USR, 'human', 10, '30 hulls in the raid on Vesta\'s surrendered drivers')]),
    ('sol', 2446.75, 4, None, 'Mars', [
        (USR, 'human', 20, 'The Resolute, with Fleet Admiral Draganić and the Command\'s staff; the Serenity mutineers\' hulls')]),
    ('sol', 2446.93, 3, None, 'Battle of Earth', [
        (USR, 'human', 50, 'The Valiant, the last Vindication; the Steadfast, scuttled into the Khan\'s mass; 60 hulls; 8,000 hulls of the Reserve Swarm; 500 platforms; the Hangzhou\'s forward half'),
        (KH, 'fev', 30, 'The Returning, which fell to the Pacific; 12,000 tributary hulls')]),
    ('alpha-centauri', 2447.80, 'Circumstance', None, 'Battle of Alpha Centauri', [
        (USR, 'human', 30, '90 hulls; the Retribution Landfall')]),
    ('procyon', 2448.35, 'Landfall', None, 'Second Battle of Procyon', [
        (USR, 'human', 30, '110 hulls; the Retribution Bounty')]),
    ('talandra', 2449.47, 'Talandra', None, 'Second Battle of Talandra', [
        (USR, 'human', 50, '220 hulls; 3 Retributions, the Circumstance and the Dauntless among them; 2 Ciribans'),
        (KH, 'fev', 30, 'The swarm of 40,000 tributary hulls')]),
    ('media', 2451.12, 'pillai', None, 'Media', [
        (USR, 'human', 20, '60 hulls; the Retribution Hualapai')]),
    ('haedus', 2451.36, 'Indata Mog', None, 'Third Battle of Haedius', [
        (USR, 'human', 16, '40 hulls; the Retribution Ijax')]),
    ('exedor', 2451.73, 'Hiverion', 'battle-of-exedor-2451', 'Battle of Exedor (2451)', [
        (USR, 'human', 25, '70 hulls; the Retributions Nomotar and Kastaba')]),
    ('aethos', 2453.60, 'Vur Duri', None, 'D\'Ashan\'s counterattack', [
        (USR, 'human', 16, 'The 40 hulls left to guard Vur Duri\'s freed yards')]),
    ('aethos', 2453.79, 'Vur Duri', None, 'Second Battle of Aethos', [
        (USR, 'human', 20, '50 hulls; the Retribution Leesak')]),
    ('fevallion', 2454.85, 'pillai', None, 'Battle of Fevallion', [
        (USR, 'human', 10, 'The Retribution Sedra, with 12,000 of her crew')]),
    ('dwaimar', 2456.40, 'Dwaimar', None, 'The Dwaii freed', [
        (USR, 'human', 20, '60 hulls in the Dwaii campaign; the Retribution Chalna')]),
    ('ossath', 2457.17, 'Ossath', None, 'Battle of Ossath', [
        (USR, 'human', 30, '90 hulls; 2 Retributions')]),
]
