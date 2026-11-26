#!/usr/bin/env python3

# Icon generator and tester
icons = {
    "Teams": '''
      <circle cx="270" cy="182" r="10"/>
      <path d="M252 216 c0 -12 8 -18 18 -18 s18 6 18 18"/>
      <circle cx="248" cy="186" r="8"/>
      <path d="M234 216 c0 -9 6 -14 14 -14"/>
      <circle cx="292" cy="186" r="8"/>
      <path d="M306 216 c0 -9 -6 -14 -14 -14"/>
    ''',
    "Node health feed": '''
      <rect x="776" y="162" width="48" height="34" rx="4"/>
      <path d="M782 179 h8 l5 -10 l6 18 l5 -12 l4 4 h8"/>
      <path d="M794 196 v5 h12 v-5"/>
    ''',
    "Queue and fair share": '''
      <path d="M270 405 v34 M256 439 h28"/>
      <path d="M246 414 h48"/>
      <path d="M246 414 l-7 14 M246 414 l7 14"/>
      <path d="M237 428 q9 6 18 0"/>
      <path d="M294 414 l-7 14 M294 414 l7 14"/>
      <path d="M285 428 q9 6 18 0"/>
      <circle cx="270" cy="414" r="3" fill="#207448"/>
    ''',
    "Topology-aware placer": '''
      <rect x="792" y="404" width="16" height="12" rx="2"/>
      <path d="M800 416 v6 M780 422 h40"/>
      <path d="M780 422 v6 M820 422 v6"/>
      <circle cx="780" cy="431" r="4"/>
      <circle cx="820" cy="431" r="4"/>
      <path d="M780 435 v5 M820 435 v5"/>
      <path d="M772 440 h16 M812 440 h16"/>
      <path d="M772 440 v4 M788 440 v4 M812 440 v4 M828 440 v4"/>
      <circle cx="772" cy="446" r="2.5" fill="#207448"/>
      <circle cx="788" cy="446" r="2.5" fill="#207448"/>
      <circle cx="812" cy="446" r="2.5" fill="#207448"/>
      <circle cx="828" cy="446" r="2.5" fill="#207448"/>
    ''',
    "Nodes in fabric blocks": '''
      <rect x="1308" y="405" width="44" height="14" rx="3"/>
      <line x1="1316" y1="412" x2="1324" y2="412"/>
      <line x1="1328" y1="412" x2="1336" y2="412"/>
      <circle cx="1344" cy="412" r="2" fill="#207448"/>
      <rect x="1308" y="429" width="44" height="14" rx="3"/>
      <line x1="1316" y1="436" x2="1324" y2="436"/>
      <line x1="1328" y1="436" x2="1336" y2="436"/>
      <circle cx="1344" cy="436" r="2" fill="#207448"/>
      <line x1="1318" y1="419" x2="1318" y2="429"/>
      <line x1="1342" y1="419" x2="1342" y2="429"/>
      <line x1="1318" y1="419" x2="1342" y2="429"/>
    ''',
    "Checkpoint store": '''
      <ellipse cx="1330" cy="668" rx="22" ry="7"/>
      <path d="M1308 668 v24 c0 8 44 8 44 0 v-24"/>
      <path d="M1308 680 c0 8 44 8 44 0"/>
      <path d="M1308 692 c0 8 44 8 44 0"/>
      <circle cx="1342" cy="682" r="1.5" fill="#207448"/>
      <circle cx="1342" cy="694" r="1.5" fill="#207448"/>
    '''
}

print("Icons configured!")
