#!/usr/bin/env python

# MergeL1Prescales.py
# Main file for parsing python configs in a CMSSW release and
# loading templates to the Conf DB.
# 
# Jonathan Hollar LLNL Nov. 3, 2008

import os, string, sys, posix, tokenize, array, getopt
from pkgutil import extend_path
import FWCore.ParameterSet.Config as cms
import re

def main(argv):
    prescalejob = MergeL1Prescales()
    prescalejob.BeginJob()

class MergeL1Prescales:
    def __init__(self):

        self.verbose = 1
        self.algofileold = "June9L1Algos.txt"
        self.algofilenew = "July7L1Algo.txt"
        self.techfileold = "June9L1Tech.txt"

        self.oldalgoprescales = {}
        self.newalgoprescales = {}
        self.oldtechprescales = {}
        self.oldalgotriggers = []
        self.newalgotriggers = []
        self.oldtechtriggers = []
        
    def BeginJob(self):

        oldl1techfile = open(self.techfileold)
        oldl1techlines = oldl1techfile.readlines()
        for oldl1techline in oldl1techlines:
            oldl1techlinetokens = oldl1techline.split()
            if(len(oldl1techlinetokens) > 1):
                if(not ((oldl1techlinetokens[0]).startswith("L1"))):
                    continue
                oldl1techtrigger = oldl1techlinetokens[0]
                tmpoldl1techprescales = ((oldl1techline.split(oldl1techtrigger))[1]).split()
                self.oldtechprescales[oldl1techtrigger] = tmpoldl1techprescales
                self.oldtechtriggers.append(oldl1techtrigger)

        oldl1algofile = open(self.algofileold)
        oldl1algolines = oldl1algofile.readlines()
        for oldl1algoline in oldl1algolines:
            oldl1algolinetokens = oldl1algoline.split()
            if(len(oldl1algolinetokens) > 1):
                if(not ((oldl1algolinetokens[0]).startswith("L1"))):
                    continue
                oldl1algotrigger = oldl1algolinetokens[0]
                tmpoldl1algoprescales = ((oldl1algoline.split(oldl1algotrigger))[1]).split()
                self.oldalgoprescales[oldl1algotrigger] = tmpoldl1algoprescales
                self.oldalgotriggers.append(oldl1algotrigger)

        newl1algofile = open(self.algofilenew)
        newl1algolines = newl1algofile.readlines()
        for newl1algoline in newl1algolines:
            newl1algolinetokens = newl1algoline.split()
            if(len(newl1algolinetokens) > 1):
                if(not ((newl1algolinetokens[0]).startswith("L1"))):
                    continue
                newl1algotrigger = newl1algolinetokens[0]
                tmpnewl1algoprescales = ((newl1algoline.split(newl1algotrigger))[1]).split()
                self.newalgoprescales[newl1algotrigger] = tmpnewl1algoprescales
                self.newalgotriggers.append(newl1algotrigger)

        # Print header
        print str("").ljust(50) + "\t5E33\t4E33\t3E33\t2.5E33\t2E33\t1.4E33\t1E33\t7E32\t5E32"
                                                                                                                
        for newalgotrigger in self.newalgotriggers:
            # Print 5E33-3E33
            print str(newalgotrigger).ljust(50),
            newprescales = self.newalgoprescales[newalgotrigger]
            tmpindex = 0
            for newprescale in newprescales:
                print "\t" + str(newprescale),
                tmpindex = tmpindex+1

            # Print 2.5E33-5E32 if it exists
            if(newalgotrigger in self.oldalgoprescales):
                oldprescales = self.oldalgoprescales[newalgotrigger]
                tmpindex = 0
                for oldprescale in oldprescales:
                    if(tmpindex >= 2):
                        print "\t" + str(oldprescale),
                    tmpindex = tmpindex+1
            else:
                if(int(newprescales[2]) == 1):
                    print "\t1\t1\t1\t1\t1\t1",
            print ""

        # Print tech triggers
        print "\n"
        for oldtechtrigger in self.oldtechtriggers:
            # Print 5E33-3E33
            print str(oldtechtrigger).ljust(50),
            oldtechprescales = self.oldtechprescales[oldtechtrigger]
            tmpindex = 0
            while tmpindex < 9:
                print "\t" + str(oldtechprescales[1]),
                tmpindex = tmpindex+1
            print ""
                
if __name__ == "__main__":
    main(sys.argv[1:])
    
