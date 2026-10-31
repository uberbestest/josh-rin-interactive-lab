#!/usr/bin/env python3
"""Original code-drawn artwork for Josh & Rin's Lab; no third-party image assets.
Decorative fiction, never experiment evidence. Deterministic SVG, standard library.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'assets' / 'lab'
P.mkdir(parents=True, exist_ok=True)
svg = ['''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 440" role="img" aria-labelledby="title desc" shape-rendering="crispEdges"><title id="title">A Halloween evening in Josh and Rin's lab</title><desc id="desc">An original pixel-style workshop: Pumpkin Rin at the computer, Puddle the duck on the desk, Mote glowing overhead, two candy-counting goblins, shelves of instruments, and a moonlit window. Decorative artwork, not experimental data.</desc><defs><pattern id="bricks" width="120" height="60" patternUnits="userSpaceOnUse"><path d="M0 0H120V60H0Z" fill="#171d30"/><path d="M0 0H120M0 30H120M60 0V30M0 30V60M120 30V60" stroke="#22283b" stroke-width="2"/></pattern><pattern id="floor" width="130" height="38" patternUnits="userSpaceOnUse"><path d="M0 0H130V38H0Z" fill="#242032"/><path d="M0 0H130M65 0V38" stroke="#352638" stroke-width="3"/></pattern></defs><rect width="1200" height="440" fill="url(#bricks)"/><path d="M0 0H1200V18H0ZM0 0H20V440H0ZM1180 0H1200V440H1180Z" fill="#30263a"/><path d="M0 358H1200V440H0Z" fill="url(#floor)"/>
<!-- Moonlit window -->
<path d="M874 66H1140V310H874Z" fill="#121a37"/><path d="M882 74H1132V300H882Z" fill="#253a66"/><path d="M882 214H923V193H963V220H1004V206H1048V178H1090V203H1132V300H882Z" fill="#293651"/><path d="M882 254H942V231H998V252H1046V217H1091V242H1132V300H882Z" fill="#19263f"/><path d="M1020 89H1068V97H1076V137H1068V145H1020V137H1012V97H1020Z" fill="#cdd5f6"/><path d="M1056 96H1068V106H1075V132H1066V141H1045V134H1056Z" fill="#aab6e2"/><path d="M1030 103H1038V111H1030ZM1022 121H1034V129H1022ZM1050 115H1058V123H1050Z" fill="#b9c3ea"/><path d="M926 100H930V112H926ZM922 104H934V108H922ZM1105 161H1109V173H1105ZM1101 165H1113V169H1101ZM952 163H956V175H952ZM948 167H960V171H948Z" fill="#ebdcaa"/><path d="M864 56H1150V68H864ZM864 56H878V313H864ZM1136 56H1150V313H1136ZM864 303H1150V321H864ZM998 62H1008V310H998ZM870 183H1144V193H870Z" fill="#46334b"/><path d="M852 320H1164V331H852Z" fill="#745066"/>
<!-- Shelves, books and bottles -->
<path d="M34 56H278V71H34ZM40 60H51V302H40ZM260 60H272V302H260ZM34 156H278V169H34ZM34 254H278V268H34Z" fill="#785044"/><path d="M44 72H268V81H44ZM44 170H268V179H44ZM44 268H268V279H44Z" fill="#3e2e38"/><path d="M63 101H81V147H63ZM86 91H99V147H86ZM102 108H125V147H102ZM128 97H145V147H128ZM204 114H219V147H204ZM223 95H238V147H223Z" fill="#9a755a"/><path d="M64 110H80V114H64ZM87 104H98V108H87ZM104 119H124V123H104ZM130 111H144V115H130Z" fill="#dab18a"/><path d="M159 95H180V111H189V142H183V148H152V142H147V112H159Z" fill="#4b7070"/><path d="M152 121H184V140H152Z" fill="#8cb697"/><path d="M157 91H182V99H157Z" fill="#d6ae7c"/><path d="M71 190H91V205H101V240H95V247H65V240H60V205H71Z" fill="#6d596d"/><path d="M65 218H96V239H65Z" fill="#c19de0"/><path d="M68 186H94V193H68Z" fill="#a67a55"/><path d="M116 209H144V245H116ZM120 201H140V211H120Z" fill="#4e6d74"/><path d="M120 218H140V239H120Z" fill="#8bc6be"/><path d="M169 190H183V212H194V239H187V246H164V239H156V212H169Z" fill="#8b674c"/><path d="M164 222H188V240H164Z" fill="#e8b570"/><path d="M215 192H235V246H215ZM242 208H252V246H242Z" fill="#6c8191"/>
<!-- Decorative chalkboard: not a data graph -->
<path d="M310 68H572V206H310Z" fill="#775447"/><path d="M320 78H562V196H320Z" fill="#193238"/><path d="M352 109H408V151H461V112H526M408 151L352 175M461 151L518 175" fill="none" stroke="#8cbdad" stroke-width="3"/><g fill="#c8dec4"><rect x="346" y="103" width="12" height="12"/><rect x="402" y="145" width="12" height="12"/><rect x="455" y="106" width="12" height="12"/><rect x="520" y="106" width="12" height="12"/><rect x="346" y="169" width="12" height="12"/><rect x="512" y="169" width="12" height="12"/></g><rect x="340" y="198" width="28" height="3" fill="#e0d4b2"/><path d="M44 29L230 45L440 28L637 47L831 28L1014 43L1168 28" fill="none" stroke="#574355" stroke-width="4"/>
''']

def rect(x, y, w, h, color, opacity=None):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"' + (f' opacity="{opacity}"' if opacity else '') + '/>')

for x, y in [(82,32),(222,44),(372,33),(514,36),(652,46),(798,32),(962,39),(1122,32)]:
    rect(x-8,y,25,33,'#ebb574','.07')
    rect(x,y,8,10,'#b89b76')
    rect(x-3,y+10,14,13,'#e7ac58')
    rect(x+1,y+13,6,7,'#fff0b1')

svg.append('''<path d="M262 316H1043V333H262Z" fill="#b27b58"/><path d="M262 333H1043V346H262Z" fill="#684250"/><path d="M288 346H315V426H288ZM995 346H1022V426H995Z" fill="#684250"/><path d="M307 375H1006V387H307Z" fill="#513542"/><path d="M569 222H729V300H569Z" fill="#776789"/><path d="M575 229H722V292H575Z" fill="#1b2440"/><path d="M626 301H672V310H626ZM552 310H745V316H552Z" fill="#9584a0"/><path d="M595 251H646V256H595ZM595 264H678V269H595ZM595 277H630V282H595Z" fill="#91c8be"/><path d="M692 248H708V252H692ZM696 244H704V259H696Z" fill="#e2b16b"/><path d="M804 301H858V311H804ZM808 293H862V303H808Z" fill="#c8b0a0"/><path d="M812 295H854V297H812ZM812 299H844V301H812Z" fill="#745568"/><path d="M351 304H415V312H351ZM358 295H418V304H358Z" fill="#a28579"/><path d="M352 306H409V309H352Z" fill="#ead6ae"/><path d="M744 286H767V308H744ZM767 291H775V303H767Z" fill="#c88950"/><rect x="749" y="290" width="13" height="14" fill="#f4bf73"/>
''')
palette={'.':None,'k':'#262237','w':'#f0dfb3','l':'#fff3ca','y':'#e9b554','o':'#ec944c','b':'#593846','p':'#8b6aaf','q':'#b292cf','g':'#85b578','h':'#b0cb8b','d':'#4d7659','r':'#d38a78','t':'#9acbc2','s':'#c1d6c9'}

def sprite(rows, x, y, scale):
    for yy, row in enumerate(rows):
        start=0
        while start<len(row):
            char=row[start]
            end=start+1
            while end<len(row) and row[end]==char:
                end+=1
            if palette.get(char):
                rect(x+start*scale,y+yy*scale,(end-start)*scale,scale,palette[char])
            start=end

# Puddle: original duck sprite.
sprite(['........kkkk.......','.......kwwwwk......','......kwwlwwwk.....','......kwkwwwwkoooo.','......kwwwwwwkoooo.','.......kwwwwk......','.......kwwwwk......','..kk..kwwwwwk......','.kwwkkwwwwwwwk.....','kwwwwwwwwwwwwk.....','kwwwwwwllwwwwk.....','.kwwwwlwwwwwk......','..kwwwwwwwwk.......','...kkkkkkkk........','.....yy.yy.........'],319,229,4)
# Pumpkin Rin: original seasonal assistant character, not a likeness.
sprite(['..........pp.......','.........ppkp......','........ppppkp.....','.......ppppppkp....','......ppppppppkp...','.....kkkkkkkkkkkk..','....oooooooooooo...','...ooooyyyyyyoooo..','...ooookoookooooo..','...ooooooooyooooo..','....oookkkkooooo...','.....ooooooooo.....','......ppppppp......','....qpppppppppq....','...qpppqqqqppppq...','...ppppqqqqppppp...','...ppppppppppppp...','....ppppppppppp....','.....kkkkkkkkk.....'],435,217,5)
rows=['.....kkkkkkkk......','....kppppppppk.....','...kppppppppppk....','..kkkkkkkkkkkkkk...','gggghhhhhhhhhgggg..','.ggghhkhhkhhhggg...','..gghhhhhhhhhhgg...','...gghhkkkkhhgg....','....gghhhhhgg......','.....dpppppd.......','....ddpppppdd......','...ggdpppppdgg.....','...ggdpppppdgg.....','.....ddddddd.......','.....kk...kk.......']
sprite(rows,785,242,4)
sprite(rows,1026,277,4)
sprite(['.......dd......','......ddd......','...ooooooooo...','..ooyyyyooooo..','.ooooyyyoooooo.','.ookooookooooo.','.ooooooooooooo.','.ooookkkkooooo.','..ooooooooooo..','...ooooooooo...'],117,318,5)
for x,y in [(918,301),(938,307),(961,303),(237,324)]:
    svg.append(f'<path d="M{x} {y-10}h5v7h7v5h-7v7h-5v-7h-7v-5h7Z" fill="#ecc570"/>')
# Mote: original lantern moth sprite.
for size,opacity in [(62,'.035'),(45,'.05'),(30,'.07')]:
    rect(672-size,111-size,2*size,2*size,'#edc875',opacity)
sprite(['...yy........yy...','..ylly......ylly..','.ylllly....ylllly.','ylllllyykkyyllllly','.ylllllykkyllllly.','..yyyyykkkkyyyyy..','....yyylkkyyy.....','...ylllkkkllly....','....yyykkkyyy.....','.......yy.........'],637,89,4)
svg.append('''<path d="M28 20H40V42H52V57H64V76H54V61H43V48H28Z" fill="#416957"/><path d="M37 51H55V59H37ZM56 71H73V82H56ZM21 36H38V44H21ZM1119 43H1131V62H1146V90H1136V70H1123Z" fill="#73936b"/><path d="M377 403H896V428H377Z" fill="#343445"/><path d="M397 409H877V413H397ZM397 421H877V425H397Z" fill="#69526b"/><path d="M45 345H101V355H45ZM51 334H107V345H51ZM1045 383H1124V396H1045ZM1037 396H1117V407H1037Z" fill="#867e8b"/><path d="M49 349H99V352H49ZM1041 400H1113V403H1041Z" fill="#d8bf94"/>
</svg>''')
(P/'halloween-workshop.svg').write_text(''.join(svg),encoding='utf-8')
print('Built original workshop SVG:',P/'halloween-workshop.svg')
