#!/bin/env python

import os, sys, string, re, shutil, math, time, subprocess, json
from datetime import datetime as dt
from optparse import OptionParser, TitledHelpFormatter

#environment variables
PWD = str(os.environ.get('PWD'))
USER = str(os.environ.get('USER'))


# Get the options from the Help Menu
def _HelpMenu() :

    # set up the parser
    usage     = """ Replay Submission """
    formatter = TitledHelpFormatter( indent_increment=5, max_help_position=50, width=300, short_first=10 )
    parser    = OptionParser( formatter = formatter, usage = usage )

   
    parser.add_option("--outdir", dest="outdir", type="string", default="/pnfs/dune/scratch/users/%s/ReplayFiles"%USER, help="name of the top output directory [default: %default]")
    parser.add_option("--detector", dest="detector", type="string", default="ndlar_2x2", help="the detector configuration (ndlar_2x2,fd_hd_marley,fd_hd_anu,fd_vd_nu,fd_vd_anu) [default: %default]")
    parser.add_option("--nfiles", dest="nfiles", type=int, default=-1, help="the number of files to process [default: all]")
    parser.add_option("--start", dest="start", type=int, default=0, help="the start run number [default: %default]")
    parser.add_option("--updateTarFile", dest="updateTarFile", default=False, action="store_true", help="update the tar file currently on cvmfs")
    parser.add_option("--offsite", dest="offsite", default=False, action="store_true", help="Run only onsite")

    (opts, args) = parser.parse_args(sys.argv)
    opts = vars(opts)

    return opts



#  main block for processing the data
if __name__ == '__main__' :

   print( "Enter launch the replay jobs via jobsub\n" )

   opts = _HelpMenu()
 
   if opts['detector'] == None :
      sys.exit("Please see the help menu. The detector is required.")

   # container to store jobsub commands
   cmdlist = []

   # copy token to directory
   cmd  = "htdestroytoken; htgettoken -i dune -a htvaultprod.fnal.gov -r interactive"
   proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
   pipe = proc.communicate()[0].decode('ascii')

   uid  = os.getuid()
   shutil.copy(f"/run/user/{uid}/bt_u{uid}", "dune.token")
   os.chmod("dune.token",0o600)


   # set base name
   basename = ""
   if opts["detector"] == "ndlar_2x2":
      basename = "ndlar_2x2_charge_raw_run1_prod_f_official"
   elif opts["detector"] == "fd_hd_marley" :
      basename = "fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2"
   elif opts["detector"] == "fd_hd_anu" :
      basename = "fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6"
   elif opts["detector"] == "fd_vd_nu" :
      basename = "fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6"
   elif opts["detector"] == "fd_vd_anu" :
      basename = "fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6"
   else :
      sys.exit( "The detector [%s] has not been implemented." % opts["detector"] )

   cmdlist.append( "-e BASE_FILENAME=%s" % basename )

   print( "\tRunning with detector [%s,%s]" % (opts["detector"],basename) )

   # output directory
   topdir = opts["outdir"]
   subdir = dt.now().strftime("%Y-%m-%d-%H-%M-%S")
   outdir = "%s/%s/%s" % (topdir,opts["detector"],subdir)
   if not os.path.isdir(outdir) :
      os.makedirs(outdir,mode=0o777)

   cmdlist.append( "-e OUTPUT_DIR=%s" % outdir )
   #cmdlist.append( "-e LOGFILE_NAME=%s/%s.%s.log" % (outdir,basename,subdir) )


   # create tarball of directory
   make_tar_file = False
   outdir_tar = "/pnfs/dune/scratch/users/%s/ReplayTarDir" % USER
   if not os.path.isdir(outdir_tar) :
      os.umask(0)
      os.makedirs(outdir_tar,mode=0o777)

   datename = dt.now().strftime("%Y_%m_%d_%H")
   tarname  = "ReplayConfigDir_%s.tgz" % datename
   if os.path.isfile("%s/%s" % (outdir_tar,tarname)) :
      if opts['updateTarFile'] :
         os.remove("%s/%s" % (outdir_tar,tarname))
         make_tar_file = True   
   else :
      make_tar_file = True

   if make_tar_file :
      print( "\tTarring the jobsub workspace folder [", tarname, "]"  )
      cmd  = "cd ..; tar -zcvf %s jobsub_workspace;mv %s %s;cd %s;" % (tarname,tarname,outdir_tar,PWD)
      proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
      pipe = proc.communicate()[0].decode('ascii')
      if proc.returncode != 0 :
         sys.exit( "Unable to perform the tar procedure." ) 

   cmdlist.append( "--tar_file_name dropbox://%s/%s" % (outdir_tar,tarname) ) 

   # get the number of files 
   nfiles = opts["nfiles"]
   files_dir = "%s/replay_workspace/files_on_test_system/%s" % (PWD,basename)

   if not os.path.isdir(files_dir):
      sys.exit( "The directory [%s] does not exist. Will not be able to submit batch jobs. Check the detector type" % opts["detector"])

   files_in_dir = len([name for name in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, name))])

   if nfiles == -1 or nfiles > files_in_dir :
      nfiles = files_in_dir

   cmdlist.append( "-N %d" % nfiles )
   cmdlist.append( "-e START=%d" % opts["start"] )

   # set environment variables
   cmdlist.append( "-e DETECTOR_CONFIG=\"%s\"" % opts["detector"] )
   cmdlist.append( "--OS=EL9" )
   cmdlist.append( "--singularity-image=/cvmfs/singularity.opensciencegrid.org/fermilab/fnal-wn-el9:latest" )
   cmdlist.append( "--cpu=8" )
   cmdlist.append( "--memory=8GB" )
   cmdlist.append( "--timeout=12h" )

   if opts["offsite"] :
      cmdlist.append( "--offsite-only" )
   else :
      cmdlist.append( "--onsite-only" )


   # run jobsub launch submission
   cmdstring = " ".join(cmdlist)
   cmd       = "jobsub_submit -G dune %s file://%s/replay.jobsub.sh" % (cmdstring,PWD)

   print( "\n\tBelow is the launch command:\n\t%s\n\n" % cmd )

   proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
   stdout, error = proc.communicate()
   stdout = stdout.decode("utf-8").split("\n")
   error  = error.decode("utf-8").split("\n")

   print( "\tCompleted launching the justin submission." )

   for s in stdout :
       print( "\t\tMessage: %s" % s)
   for e in error :
       print( "\t\tError: %s" % e)

   if proc.returncode != 0 : 
      sys.exit( "Unable to launch jobs successful." )

   print( "Output files are in the directory [%s]" % outdir )
   print( "Exit launch replay jobs for [%s]\n\n" % (opts["detector"]) )
