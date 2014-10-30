#!/usr/bin/env python

# CalculatePrescaleColumns.py
# Main file for parsing python configs in a CMSSW release and
# loading templates to the Conf DB.
# 
# Jonathan Hollar LLNL Nov. 3, 2008

import os, string, sys, posix, tokenize, array, getopt
from pkgutil import extend_path
import FWCore.ParameterSet.Config as cms
import re

def main(argv):
    prescalejob = CalculatePrescaleColumns()
    prescalejob.BeginJob()

class CalculatePrescaleColumns:
    def __init__(self):

        self.verbose = 1
        self.twikifile = "HLT_3E33_July9.twiki"
        self.l1prescalefile = "L1_3E33_July9.txt"
        self.clilumi = "3e33"
        self.doallcolumns = 1
        self.printtotalprescales = 0
        self.columns = ["5e33","4e33","3e33","2.5e33","2e33","1.4e33","1e33","7e32","5e32"]
        #        self.columns = ["5e33"]

        self.newhltprescales = []
        self.hltpathsinmenu = []
        self.newl1seeddict = {}
        self.newl1prescales = []
        self.newl1prescaledict = {}
        self.newhltl1prescaledict = {}
        self.unknown = []
        self.killed1 = []
        self.killed2 = []
        self.nolumiscale = ["HLT_ZeroBias","HLT_Random","HLT_Physics","HLT_L1_Interbunch_BSC","HLT_L1_PreCollis
ions"]
        
        opts, args = getopt.getopt(sys.argv[1:], "c:t:l:o", ["targetcolumn","hlttwiki=","levelonefile=","overal
lprescales"])

        for o, a in opts:
            if o in ("-c","targetcolumn="):
                self.clilumi = str(a)
            if o in ("-t","hlttwiki="):
                self.twikifile = str(a)
            if o in ("-l","levelonefile="):
                self.l1prescalefile = str(a)
            if o in ("-o","overallprescales"):
                self.printtotalprescales = 1
                
    def BeginJob(self):

        l1file = open(self.l1prescalefile)
        l1lines = l1file.readlines()
        for l1line in l1lines:
            l1linetokens = l1line.split()
            if(len(l1linetokens) > 1):
                if(not ((l1linetokens[0]).startswith("L1"))):
                    continue
                l1trigger = l1linetokens[0]
                tmpl1prescales = ((l1line.split(l1trigger))[1]).split()
                self.newl1prescaledict[l1trigger] = tmpl1prescales
                                                                    

        oldfile = open(self.twikifile)
        twikilines = oldfile.readlines()
        for twikiline in twikilines:
            if(twikiline.find("|") != -1 and twikiline.find("Rate") == -1): 
                twikitoken = twikiline.split("|")
                twikitrigger = (twikitoken[1]).rstrip().lstrip().lstrip("!")
                twikihltprescale = twikitoken[4]
                twikil1seed = (twikitoken[2]).rstrip().lstrip().lstrip("!")
                self.newhltprescales.append((twikitrigger,twikihltprescale))
                self.newl1seeddict[twikitrigger] = twikil1seed;
                if(twikil1seed.find(" OR ") == -1 and twikil1seed.find(" AND ") == -1 and (twikil1seed != "")):
                    if(twikil1seed in self.newl1prescaledict):
                        self.newhltl1prescaledict[twikitrigger] = self.newl1prescaledict[twikil1seed]
                    else:
                        self.unknown.append((twikitrigger,twikihltprescale))
                else:
                    if(twikil1seed.find(" OR ") != -1 or twikil1seed.find(" AND ") != -1):
                        twikil1seed = "L1_Fake"
                        self.newhltl1prescaledict[twikitrigger] = self.newl1prescaledict[twikil1seed]
                    self.unknown.append((twikitrigger,twikihltprescale))


        print str("Path").ljust(75) + "\t\t",
        for column in self.columns:
            print str(column) + "\t",
        print ""
        
        for newtrigger, newprescale in self.newhltprescales:

            basecolumnprescale = -1
            basecolumntotalprescale = -1

            # Strip version and Open prefix
            newtmptrigname = newtrigger
            if(newtmptrigname.startswith("OpenHLT_")):
                newtmptrigname = string.replace(newtmptrigname,"OpenHLT_","HLT_")
            newtmptrigname = re.sub("_v([0-9])([0-9])", "", newtmptrigname)
            newtmptrigname = re.sub("_v([0-9])", "", newtmptrigname)
            newtmptrigname = newtmptrigname.lstrip('"').rstrip('"')
                        
            k = 0
            j = 0
            i = 0
            basecolumn = -1
            basecolumnlumi = (self.clilumi).lstrip('"').rstrip('"')

            newprescalesincolumns = []

            for column in self.columns:
                newprescalesincolumns.append(0)
                k = k + 1

            basecolumn = -1

            # First do the base column
            for column in self.columns: 
                thiscolumn = column.lstrip('"').rstrip('"')
                if(thiscolumn.find("Cosmics") != -1):
                    i = i + 1
                    continue

                if(thiscolumn.find(self.clilumi) != -1):
                    tmpl1prescale = 1
                    basecolumn = i
                    basecolumnprescale = int(newprescale)
                    if(newtrigger in self.newhltl1prescaledict):
                        tmpl1prescale = int((self.newhltl1prescaledict[newtrigger])[i])
                    totalprescale = int(tmpl1prescale) * int(newprescale)
                    basecolumntotalprescale = totalprescale
                    #                    print str(newtmptrigname).ljust(50) + "\t\t" + str(self.columns[i]).rj
ust(10) + str(newprescale).rjust(10) + str(tmpl1prescale).rjust(10) + str(totalprescale).rjust(10)
                    if(self.printtotalprescales == 0):
                        newprescalesincolumns[i] = newprescale
                    else:
                        newprescalesincolumns[i] = totalprescale
                        
                i = i + 1

                    
            # Now do all other columns
            i = 0 
            for column in self.columns:
                thiscolumn = column.lstrip('"').rstrip('"')
                if(thiscolumn.find("Cosmics") != -1):
                    i = i + 1
                    continue

                if(thiscolumn.find(self.clilumi) == -1):
                    iszeroed = 0
                    thiscolumn = (self.columns[i]).lstrip('"').rstrip('"')
                    ratio = float(thiscolumn)/float(basecolumnlumi)
                    newhltprescalescale = float(float(newprescale) * ratio) 

                    if(newhltprescalescale == 0):
                        iszeroed = 1

                    # Check the L1 prescale for this column and the base column
                    tmpl1prescale = 1
                    basecolumnl1prescale = 1
                    if(newtrigger in self.newhltl1prescaledict):
                        basecolumnl1prescale = int((self.newhltl1prescaledict[newtrigger])[basecolumn])
                        tmpl1prescale = int((self.newhltl1prescaledict[newtrigger])[i])
                        if(int(tmpl1prescale) == 0):
                            newhltprescalescale = 0;
                        if((tmpl1prescale != basecolumnl1prescale)):
                            # If L1 is prescaling, adjust the HLT prescale accordingly
                            if(int(tmpl1prescale) > 0):
                                newhltprescalescale = int(newhltprescalescale * float(basecolumnl1prescale) / f
loat(tmpl1prescale))
                        else:
                            newhltprescalescale = int(newhltprescalescale)
                    else:
                        newhltprescalescale = int(newhltprescalescale)
                        
                    # For now, don't automatically prescale unprescaled paths in higher columns
                    if((i < int(basecolumn)) and (newhltprescalescale == 2) and (basecolumnprescale == 1)):
                        newhltprescalescale = 1

                    if(newtmptrigname in self.nolumiscale):
                        newhltprescalescale = basecolumnprescale

                    # Integer prescaling only :)
                    if((newhltprescalescale < 1) and (iszeroed == 0)):
                        newhltprescalescale = 1

                    # Round numbers...
                    if(int(newhltprescalescale) >= 10 and int(newhltprescalescale) < 100):
                        if((newhltprescalescale % 10) > 0 and (newhltprescalescale % 10) > 7):
                            newhltprescalescale = (newhltprescalescale - (newhltprescalescale % 10)) + 10
                        if((newhltprescalescale % 10) > 0 and (newhltprescalescale % 10) < 8 and (newhltprescal
escale % 10) > 3):
                            newhltprescalescale = (newhltprescalescale - (newhltprescalescale % 10)) + 5
                        if((newhltprescalescale % 10) > 0 and (newhltprescalescale % 10) < 4):
                            newhltprescalescale = (newhltprescalescale - (newhltprescalescale % 10))
                    if(int(newhltprescalescale) >= 100 and int(newhltprescalescale) < 10000):
                        if((newhltprescalescale % 10) > 0):
                            newhltprescalescale = (newhltprescalescale - (newhltprescalescale % 10)) + 10
                    if(int(newhltprescalescale) >= 10000 and int(newhltprescalescale) <= 100000):
                        if((newhltprescalescale % 100) > 0):
                            newhltprescalescale = (newhltprescalescale - (newhltprescalescale % 100)) + 100
                    if(int(newhltprescalescale) >= 100000 and int(newhltprescalescale) <= 10000000):
                        if((newhltprescalescale % 10000) > 0):
                            newhltprescalescale = (newhltprescalescale - (newhltprescalescale % 10000)) + 10000
                            

                    # If the calculated prescale is almost the same as the base one, use the base
                    # one for consistency accross columns
                    if(basecolumnprescale>0):
                        if(abs(1.0*(basecolumnprescale - newhltprescalescale)/(1.0*basecolumnprescale)) < 0.2):
                            newhltprescalescale = basecolumnprescale

                    totalprescale = int(tmpl1prescale) * int(newhltprescalescale)

                    if(int(totalprescale) == 0 and int(basecolumnprescale) != 0 and self.printtotalprescales ==
 1):
                        self.killed1.append((newtmptrigname,totalprescale,i))

                    if(self.doallcolumns == 1):
                        #                        print str(newtmptrigname).ljust(50) + "\t\t" + str(self.column
s[i]).rjust(10) + str(newhltprescalescale).rjust(10) + str(tmpl1prescale).rjust(10) + str(totalprescale).rjust(
10)
                        if(self.printtotalprescales == 0):
                            newprescalesincolumns[i] = newhltprescalescale
                        else:
                            newprescalesincolumns[i] = totalprescale
                            
                i = i + 1

            j = j + 1
            i = 0
            print str(newtmptrigname).ljust(75) + "\t\t",
            #            print newprescalesincolumns
            for newprescalesincolumn in newprescalesincolumns:
                print str(newprescalesincolumn) + "\t",
                if(newprescalesincolumn > 1 and basecolumntotalprescale == 1 and self.printtotalprescales == 1)
:
                    self.killed2.append((newtmptrigname,newprescalesincolumn,i))
                i = i + 1
            print ""

        print "\n\n"
        print "----------------------------------------------------"
        print "Paths using L1's prescaled to 0 by in higher columns"
        print "----------------------------------------------------"
        for killedname, killedprescale, killedcolumn in self.killed1:
            print killedname.ljust(75) + " (p = " + str(killedprescale) + " in column " + str(killedcolumn) +")
"

        print "\n\n"
        print "--------------------------------------------------------"
        print "Unprescaled paths using prescaled L1's in higher columns"
        print "--------------------------------------------------------"
        for killedname, killedprescale, killedcolumn in self.killed2:
            print killedname.ljust(75) + " (p = " + str(killedprescale) + " in column " + str(killedcolumn) +")
"
                                                
                                        
        print "\n\n"
        print "-------------------------------------"
        print "Paths with OR'ed/AND'ed/unknown seeds" 
        print "-------------------------------------"
        
        for unknowns, unknownsprescale in self.unknown:
            print unknowns + "(" + str(unknownsprescale) +")"

                
if __name__ == "__main__":
    main(sys.argv[1:])
    
