#!/usr/bin/env python

# LoadOneColumnOfPrescales.py
# Main file for parsing python configs in a CMSSW release and
# loading templates to the Conf DB.
# 
# Jonathan Hollar LLNL Nov. 3, 2008

import os, string, sys, posix, tokenize, array, getopt
from pkgutil import extend_path
#import ConfdbOracleModuleLoader
sys.path.append("./")
import cx_Oracle
import FWCore.ParameterSet.Config as cms
import re

def main(argv):
    # Get information from the environment

    confdbjob = LoadOneColumnOfPrescales()
    confdbjob.BeginJob()

class LoadOneColumnOfPrescales:
    def __init__(self):

        self.dbname = "CMS_ORCOFF_PROD"
        self.dbuser = "CMS_HLTDEV"
        self.dbpwd = ""
        self.dbhost = "CMS_ORCOFF_PROD"
        self.verbose = 1
        self.cmsswrel = "CMSSW_4_2_0_HLT20"
        #        self.configname = "/users/jjhollar/July73E33MenuValidation/CMSSW_4_2_0_HLT20_Master_V752_PrescalesV1/V1"
        #        self.prescalefile = "hltprescales_3E33_July7.txt"
        self.configname = "/users/jjhollar/July73E33MenuValidation/CMSSW_4_2_0_HLT20_Master_V752_PrescalesV1/V9"
        self.prescalefile = "hltprescales_5E33_July7.txt"
        self.clilumi = "5e33"
        self.cliupdate = 0
        self.addtorelease = ""
        self.comparetorelease = ""
        self.doallcolumns = 1

        self.hltpathsinmenu = []
        self.newhltprescaledict = {}
               
	# Get a Conf DB connection here. Only need to do this once at the 
	# beginning of a job.
        self.dbcursor = self.ConfdbOracleConnect(self.dbname,self.dbuser,self.dbpwd,self.dbhost)

        # Read command line options
        opts, args = getopt.getopt(sys.argv[1:], "ul:p:c:", ["update","lumi=","prescalefile=","configuration="])

        for o, a in opts:
            if o in ("-u","update="):
                self.cliupdate = 1
            if o in ("-l","lumi="):
                self.clilumi = str(a)
            if o in ("-c","configuration="):
                self.configname = str(a)
            if o in ("-p","prescalefile="):
                self.prescalefile = str(a)
                
    def BeginJob(self):

        #########################################
        # Read the text file of new HLT prescales
        #########################################

        prescaletablefile = open(self.prescalefile)
        prescalelines = prescaletablefile.readlines()
        for prescaleline in prescalelines:
            tokens = prescaleline.split()
            if(len(tokens) < 1):
                continue
            if(tokens[0] == "Path"):
               continue
            trigger = (tokens[0]).rstrip().lstrip()
            tmpprescales = ((prescaleline.split(trigger))[1]).split()
            self.newhltprescaledict[trigger] = tmpprescales

        ###########################################################################
        # ConfDB stuff - get the relevant PrescaleService information for this menu
        ###########################################################################
               
        # Get the menu
        self.dbcursor.execute("SELECT Configurations.configId FROM Configurations WHERE (configDescriptor = '" + self.configname + "')")
        tmprelid = (self.dbcursor.fetchone())[0]

        # Get a list of all HLT paths in the menu
        self.dbcursor.execute("SELECT Paths.name FROM Paths JOIN ConfigurationPathAssoc ON Paths.pathId = ConfigurationPathAssoc.pathId WHERE ConfigurationPathAssoc.configId = " + str(tmprelid))
        dbhltpaths = (self.dbcursor.fetchall())
        for dbhltpath in dbhltpaths:
            self.hltpathsinmenu.append(dbhltpath[0])

        # Get the PrescaleService 
        self.dbcursor.execute("SELECT Services.superId FROM Services JOIN ServiceTemplates ON Services.templateId = ServiceTemplates.superId JOIN ConfigurationServiceAssoc ON ConfigurationServiceAssoc.serviceId = Services.superId WHERE ServiceTemplates.name = 'PrescaleService' AND ConfigurationServiceAssoc.configId = " + str(tmprelid))
        presid = (self.dbcursor.fetchone())[0]

        # Get the Prescale Table VPSet
        self.dbcursor.execute("SELECT VecParameterSets.superId FROM VecParameterSets JOIN SuperIdVecParamSetAssoc ON VecParameterSets.superId = SuperIdVecParamSetAssoc.vpsetId WHERE VecParameterSets.name = 'prescaleTable' AND SuperIdVecParamSetAssoc.superId = " + str(presid))
        pretableid = (self.dbcursor.fetchone())[0]

        # Get the PSet for each trigger 
        self.dbcursor.execute("SELECT ParameterSets.superId FROM ParameterSets JOIN SuperIdParamSetAssoc ON SuperIdParamSetAssoc.psetId = ParameterSets.superId JOIN VecParameterSets ON VecParameterSets.superId = SuperIdParamSetAssoc.superId WHERE VecParameterSets.superId = " + str(pretableid))
        pretablepsetids = (self.dbcursor.fetchall())

        # Get the trigger name
        self.dbcursor.execute("SELECT StringParamValues.value FROM StringParamValues JOIN SuperIdParameterAssoc ON SuperIdParameterAssoc.paramId = StringParamValues.paramId WHERE SuperIdParameterAssoc.superId = " + str(presid))
        defaultlabel = (self.dbcursor.fetchone())[0]

        # Get the Prescale set 
        self.dbcursor.execute("SELECT VStringParamValues.value FROM VStringParamValues JOIN SuperIdParameterAssoc ON SuperIdParameterAssoc.paramId = VStringParamValues.paramId WHERE SuperIdParameterAssoc.superId = " + str(presid))
        lvl1labels = (self.dbcursor.fetchall())

        # Indices of PrescaleService entries, for ConfDB Sequence number bookkeeping
        self.dbcursor.execute("SELECT SuperIdParamSetAssoc.sequenceNb FROM SuperIdParamSetAssoc JOIN VecParameterSets ON VecParameterSets.superId = SuperIdParamSetAssoc.superId WHERE VecParameterSets.superId = " + str(pretableid))
        psetsequencenbs = (self.dbcursor.fetchall())
        j = (max(psetsequencenbs))[0]
        k = 0
            
        
        ###########################################################################
        # Now begin updating/entering the prescales
        ###########################################################################
                                    
        # Loop over all paths in the configuration
        for hltpath in self.hltpathsinmenu:
            if(hltpath.find("HLTriggerFirstPath") != -1 or hltpath.find("HLTriggerFinalPath") != -1):
                continue

            foundtrigger = False
            unversionedpath = ""
            unversionedpath = re.sub("_v([0-9])([0-9])", "", hltpath)
            if(unversionedpath.find("_v") != -1):
                unversionedpath = re.sub("_v([0-9])", "", hltpath)
                unversionedpath = unversionedpath.lstrip('"').rstrip('"')

            # See if a prescale is defined in the text file for this path  
            if(not (unversionedpath in self.newhltprescaledict)):
                continue


            # See if an entry already exists for this trigger in the DB 
            for pretablepsetidpair in pretablepsetids:
                pretablepsetid = pretablepsetidpair[0]
                self.dbcursor.execute("SELECT StringParamValues.value FROM StringParamValues JOIN SuperIdParameterAssoc ON SuperIdParameterAssoc.paramId = StringParamValues.paramId WHERE SuperIdParameterAssoc.superId = " + str(pretablepsetid))
                trigname = (self.dbcursor.fetchone())[0]
                tmptrigname = (re.sub("_v([0-9])([0-9])", "", trigname)).lstrip('"').rstrip('"')
                if(tmptrigname.find("_v") != -1):
                    tmptrigname = (re.sub("_v([0-9])", "", trigname)).lstrip('"').rstrip('"')
            
                self.dbcursor.execute("SELECT VUInt32ParamValues.paramId FROM VUInt32ParamValues JOIN SuperIdParameterAssoc ON SuperIdParameterAssoc.paramId = VUInt32ParamValues.paramId WHERE SuperIdParameterAssoc.superId = " + str(pretablepsetid))
                vectorparamid = (self.dbcursor.fetchone())[0]
            
                self.dbcursor.execute("SELECT VUInt32ParamValues.value FROM VUInt32ParamValues JOIN SuperIdParameterAssoc ON SuperIdParameterAssoc.paramId = VUInt32ParamValues.paramId WHERE SuperIdParameterAssoc.superId = " + str(pretablepsetid))
                prescales = (self.dbcursor.fetchall())
            
                if(not(tmptrigname == unversionedpath)):
                    continue

                foundtrigger = True

                # Iterator over prescale columns
                i = 0

                # The trigger exists, and already has an entry in the PrescaleService
                # So update it
                newprescales = self.newhltprescaledict[unversionedpath]
                for prescale in prescales: 
                    if(i == 0):
                        if(i < 1):
                            newprescale = newprescales[i]
                            print "\tChange " + str(lvl1labels[i][0]) + " prescale of " + str(trigname) + " from " + str(prescale[0]) + " to " + str(newprescale)
                            if(self.cliupdate == 1):
                                self.dbcursor.execute("UPDATE VUInt32ParamValues SET value='" + str(newprescale) + "' WHERE VUInt32ParamValues.sequenceNb = " + str(i) + " AND VUInt32ParamValues.paramId = " + str(vectorparamid)) 
                                print "\tChange applied"
                    i = i + 1

                # Count total number of existing PrescaleService entries
                j = j + 1

            # The trigger has prescales defined in the text file, but
            # has no entry in the PrescaleService in the DB. If it has 
            # non-trivial prescales in the text file (not 0 or 1), create 
            # a new entry 
            newprescales = self.newhltprescaledict[unversionedpath]
            maxprescale = max(newprescales)
            if((foundtrigger == False) and ((int(maxprescale) > 1) or (int(maxprescale) == 0))):
                print "Prescaled trigger " + str(hltpath) + " does not have a non-trivial prescale set - new entry needed!"

                # Add PSet to the PrescaleService VPSet, with correct Sequence number
                self.dbcursor.execute("INSERT INTO SuperIds VALUES('')")
                self.dbcursor.execute("SELECT SuperId_Sequence.currval from dual")
                newparamsetid = self.dbcursor.fetchone()[0]
                self.dbcursor.execute("INSERT INTO ParameterSets (superId, name, tracked) VALUES (" + str(newparamsetid) + ", '', " + str(1) + ")")
                self.dbcursor.execute("INSERT INTO SuperIdParamSetAssoc (superId, psetId, sequenceNb) VALUES (" + str(pretableid) + ", " + str(newparamsetid) + ", " + str(j+k) + ")")

                # Add String - be sure to use the correctly versioned name taken from the DB
                self.dbcursor.execute("INSERT INTO Parameters (paramTypeId, name, tracked) VALUES (" + str(8) + ", 'pathName', " + str(1) + ")")
                self.dbcursor.execute("SELECT ParamId_Sequence.currval from dual")
                newparamid = self.dbcursor.fetchone()[0]
                self.dbcursor.execute("INSERT INTO StringParamValues (paramId, value) VALUES (" + str(newparamid) + ", '" + str(hltpath) + "')")
                self.dbcursor.execute("INSERT INTO SuperIdParameterAssoc (superId, paramId, sequenceNb) VALUES (" + str(newparamsetid) + ", " + str(newparamid) + ", " + str(0) + ")")

                # Add Prescale set
                self.dbcursor.execute("INSERT INTO Parameters (paramTypeId, name, tracked) VALUES (" + str(5) + ", 'prescales', " + str(1) + ")")
                self.dbcursor.execute("SELECT ParamId_Sequence.currval from dual")
                newparamid = self.dbcursor.fetchone()[0]
                self.dbcursor.execute("INSERT INTO SuperIdParameterAssoc (superId, paramId, sequenceNb) VALUES (" + str(newparamsetid) + ", " + str(newparamid) + ", " + str(1) + ")")

                print "Added new Prescale vector with paramset id and paramid = " + str(newparamsetid) + ", " + str(newparamid)
                
                # Finally insert the prescale!

                # Iterator over prescale columns
                m = 0
                for prescale in prescales:
                    #                    if((lvl1labels[m][0]).find("Cosmics") == -1 and (lvl1labels[m][0] == "5e33")):
                    if(m == 0):
                        print "CLI target column # " + str(m)
                        if(m < 1):
                            newprescale = newprescales[m]
                            print "\tSet " + str(lvl1labels[m][0]) + " prescale of " + str(hltpath) + " to " + str(newprescale)
                            if(self.cliupdate == 1):
                                self.dbcursor.execute("INSERT INTO VUInt32ParamValues (paramId, sequenceNb, value) VALUES (" + str(newparamid) + ", " + str(m) + ", " + str(newprescale) + ")")
                                print "INSERT INTO VUInt32ParamValues (paramId, sequenceNb, value) VALUES (" + str(newparamid) + ", " + str(m) + ", " + str(newprescale) + ")"
                                print "\tChange applied"
                    else:
                        newprescale = 1
                        print "CLI non-target column # " + str(m)
                        print "\tSet " + str(lvl1labels[m][0]) + " prescale of " + str(hltpath) + " to " + str(newprescale)
                        if(self.cliupdate == 1):
                            self.dbcursor.execute("INSERT INTO VUInt32ParamValues (paramId, sequenceNb, value) VALUES (" + str(newparamid) + ", " + str(m) + ", " + str(newprescale) + ")")
                            print "\tChange applied"
                            print "INSERT INTO VUInt32ParamValues (paramId, sequenceNb, value) VALUES (" + str(newparamid) + ", " + str(m) + ",  " + str(newprescale) + ")"
                            

                    m = m + 1

                # Count number of newly added PrescaleService entries
                k = k + 1
                        
        self.ConfdbExitGracefully()

    # Get a connection
    def ConfdbOracleConnect(self,dbname,username,userpwd,userhost):
        self.connection = cx_Oracle.connect(username+"/"+userpwd+"@"+userhost)
        cursor = self.connection.cursor()
        return cursor

    # All done. Clean up and commit changes (necessary for INNODB engine)
    def ConfdbExitGracefully(self):
        self.connection.commit()
        self.connection.close()
                    
if __name__ == "__main__":
    main(sys.argv[1:])
    
