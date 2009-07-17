#!/usr/bin/python -u

"""
To generate the word list:
- download the aspell package for the proper language
- decompress the word list and convert to utf-8:
    prezip-bin -d < aspell6-it-2.2_20050523-0/it.cwl | iconv -f ISO8859-15 -t UTF-8 - > it.wl
- put proper words in another file:
    awk '/^[[:upper:]]/{ print $0 }' it.wl > it-proper.wl
    sed -rni '/^[[:lower:]]/p' it.wl
- expand the words, put them one per line, remove part of word before ' and sort (3/4 minutes and lot of RAM):
    aspell expand < it.wl | tr ' ' '\n' | sed -r "s/^[^']+'//" | tr 'A-Z' 'a-z' | sort -u > words.italian.full
    aspell expand < it-proper.wl | tr ' ' '\n' | sed -r "s/^[^']+'//" | tr 'A-Z' 'a-z' | sort -u > words.italian-proper.full

"""

import sys,random,time,codecs,re

#D = "/usr/share/dict/words"
D = "/home/matteo/bin/words.italian.full"

def norm(w):
    return "".join(sorted( w.lower() ))

import unicodedata
normre = re.compile("[^a-z]")
def normchr(c):
    return normre.sub( "", unicodedata.normalize("NFKD",c).lower() )

WORDS = {}
def init():
    t = time.time()
    print ">>> loading words...",

    for w in codecs.open(D,encoding="UTF-8"):
        w = w.rstrip()

        #if w == "aneto":
        #    break

        ws = norm(w)
        l = WORDS.get(ws)
        if not l:
            l = []
            WORDS[ws] = l
        l.append(w)

    #calcscoring()

    print "%.1fs" % (time.time()-t)

    random.seed()


def an(w):
    ws = norm(w)
    if ws in WORDS:
        return WORDS[ws]
    return []

randomwordcache = {}
def randomword(wordlen=0,minan=0):
    target = randomwordcache.get((wordlen,minan))
    if not target:
        target = WORDS
        if wordlen > 0:
            target = dict([ (k,v) for k,v in target.items() if len(k) == wordlen ])
        if minan > 0:
            target = dict([ (k,v) for k,v in target.items() if len(v) >= minan ])
        randomwordcache[(wordlen,minan)] = target
    ltarget = len(target)
    k = target.keys()[ random.randrange(ltarget) ]
    return k,target[k]

def suban(w,ans):
    for i in range(3,N):
        comb = set([ "".join(l) for l in xcombinations(list(w),i) ])
        for k in WORDS:
            if len(k) != i:
                continue
            if k in comb:
                ans.extend( WORDS[k] )

def xcombinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in xcombinations(items[:i]+items[i+1:],n-1):
                yield [items[i]]+cc

## SCRABBLE like scoring
SCORES = {}
def calcscoring():
    global SCORES
    for w in WORDS:
        for c in w:
            if c == "'":
                print "PLEXO",w
            if not SCORES.get(c):
                SCORES[c] = 0
            SCORES[c] += 1

    tmp = SCORES
    SCORES = {}
    for k in tmp:
        nk = normchr(k)
        v = SCORES.get(nk)
        if v:
            SCORES[nk] += tmp[k]
        else:
            SCORES[nk] = tmp[k]

    m = max( SCORES.values() )

    for k in SCORES:
        SCORES[k] = 10-int(9./m*SCORES[k])
        print k, SCORES[k]



##################### WORD CHALLENGE
N = 6

init()

t = time.time()
print ">>> loading random words cache...",
randomword(wordlen=N,minan=2)
print "%.1fs" % (time.time()-t)

#### CLI
if False:
    for i in range(10):
        w,ans = randomword(wordlen=N,minan=2)
        suban(w,ans)

        while True:
            lens = {}
            print ">>>",
            for i in range(3,N+1):
                n = 0
                for an in ans:
                    if len(an) == i:
                        n += 1
                print "%d:%d" % (i,n),
            print
            print ">>> [%s]:" % w,
            s = raw_input().decode("UTF-8").lower()
            slen = len(s)
            if s == "":
                l = list(w)
                random.shuffle(l)
                w = "".join(l)
            elif s == "n":
                break
            elif not 3 <= slen <= N:
                print ">>> wrong anagram size!"
            elif s in ans:
                print ">>> great!"
                del ans[ ans.index(s) ]
            else:
                print ">>> not an anagram!"

        print ">>> anagrams:", " ".join(ans)



#### CURSES
import locale
# set locale to UTF-8
locale.setlocale( locale.LC_ALL, (locale.getdefaultlocale()[0],"UTF-8") )

# instantiate an incremental decoder
incdec = codecs.getincrementaldecoder('utf-8')()

import curses

stdscr = curses.initscr()
curses.noecho()
#curses.cbreak()
curses.raw()
stdscr.keypad(1)

try:
    score = 0
    while True:
        #given = ["ano","anelo"] # given anagrams
        #w,ans = ("lotane","lato aneto ano eno etano anelo".split())
        given = []
        lastgiven = given
        w,ans = randomword(wordlen=N,minan=2)
        suban(w,ans)
        stdscr.addstr(1,1,w,curses.A_BOLD)

        givenX = [0,0,0,1,5,10,16]
        curs = (2,1)
        givenc = []
        myw = w
        curscore = 25
        next = False

        while True:
            lastgiven = set(given) - set(lastgiven)
            for i in range(3,N+1):
                y = 4
                x = givenX[i]
                for an in ans:
                    if len(an) == i:
                        if an in given:
                            if an in lastgiven:
                                stdscr.addstr(y,x,an,curses.A_UNDERLINE)
                            else:
                                stdscr.addstr(y,x,an,curses.A_NORMAL)
                        else:
                            stdscr.addstr(y,x,"-"*i)
                        y += 1
            lastgiven = given

            s = "SCORE: %d" % score
            stdscr.addstr(0,stdscr.getmaxyx()[1]-len(s),s)

            if set(ans) == set(given): # word completed!
                pass

            if next:
                stdscr.erase()
                break
                        
            stdscr.move(*curs)
            c = stdscr.getch()
            k = curses.keyname(c)
            #raise Exception(k)

            #stdscr.addstr(11,1,"c: "+str(c)+"    ")
            #stdscr.move(*curs)

            if c == ord(" "): # SHUFFLE
                l = list(w)
                random.shuffle(l)
                w = "".join(l)
                myw = w
                for c in givenc:
                    myw = myw.replace(c," ",1)
                stdscr.addstr(1,1,myw,curses.A_BOLD)

            elif c == curses.KEY_ENTER or c == 10:
                s = "".join(givenc)
                if s in given: # duplicate
                    stdscr.addstr(20,20,"DUPE!    ")
                elif s in ans: # hit
                    for i in range(len(s)):
                        score += curscore
                        curscore += 1
                    stdscr.addstr(20,20,"GOT IT!    ")
                    given.append(s)
                    givenc = []
                    curs = (2,1)
                    stdscr.addstr(curs[0],curs[1]," "*N)
                    myw = w
                    stdscr.addstr(1,1,myw,curses.A_BOLD)
                else:
                    stdscr.addstr(20,20,"NO WAY!   ")
                    pass # failure

            elif c == curses.KEY_BACKSPACE or c == 127:
                if not givenc:
                    continue
                givenc.pop()
                myw = w
                for c in givenc:
                    myw = myw.replace(c," ",1)
                stdscr.addstr(1,1,myw,curses.A_BOLD)
                curs = curs[0],curs[1]-1
                stdscr.addstr(curs[0],curs[1]," ")

            elif k.startswith("^"):
                c = k[-1].lower()
                if c == "s": # solve
                    given = ans
                if c == "q": # quit
                    raise Exception()
                if c == "n": # next
                    next = True

            elif 0 < c < 256:
                s = incdec.decode(chr(c))
                if not s:
                    continue
                incdec.reset()
                if s in myw:
                    stdscr.addstr(s.encode("UTF-8"))
                    givenc.append(s)
                    #stdscr.addstr(10,1,"givenc: "+str(givenc))
                    myw = w
                    for c in givenc:
                        myw = myw.replace(c," ",1)
                    stdscr.addstr(1,1,myw,curses.A_BOLD)
                    curs = curs[0],curs[1]+1

                



            #try:
            #s = unichr(c)
            #stdscr.addstr("%X %s" % (c,s.decode("UTF-8")))
            #stdscr.addstr("%X|%s" % (c,s.encode("UTF-8")))
            #stdscr.addstr("%X|%s" % (c,s))
            #stdscr.addstr(s.encode("ISO8859-15"))
            #except:
            #    pass

        

finally:
    curses.nocbreak(); curses.noraw(); stdscr.keypad(0); curses.echo()
    curses.endwin()

"""
           11111111112
  012345678901234567890
 0                          SCORE: 123
 1 aaplod
 2 palo
 3                      
 4 ___ ____ _____ ______
 5 ___ ____
 6 ___ ____
 7 ___
 8 ___
 9
10
"""






# for w in sys.argv[1:]:
#     print "Anagrams of %s: %s" % (w, ' '.join(an(w)))

# def findana (anagram):
#      sorted_anagram = sorted(anagram.lower())
#      len_anagram = len (anagram)
#      found = [ word for word in WORDS if len(word)==len_anagram and sorted(word)==sorted_anagram ]
#      print "Anagrams of %s: %s" % (anagram, ' '.join(found))
# 
# for i in sys.argv [1:]:
#      findana (i)

