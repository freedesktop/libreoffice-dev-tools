README.txt

This directory contains tools relating to the LibreOffice "Bibisect"
QA Tool, created by Bjoern Michaelsen:
https://wiki.documentfoundation.org/Bibisect

Building a bibisect repository
------------------------------

The scripts in this directory are the primary tools for creating
bibisect repositories. You'll want to read over these files (ignore
mergeranges for now) to learn more about how the process works.


  Stuff you'll need:
  ------------------

- The dev-tools repository (I assume you have it, as you're reading this)

- The LibreOffice core repository

  I suggest you build LibreOffice once by itself, just to make
  sure that everything is working properly, before you jump in
  to building a bibisect repo.

- A suitable build environment

- ccache
  
  Should be in 'ccache' package on most distros. Read this page to
  properly configure ccache for building LibreOffice:
  https://wiki.documentfoundation.org/Development/BuildingOnLinux#ccache


  Getting ready:
  --------------

- Build LibreOffice

- Edit bibisect.cfg to suit your particular environment:

WARNING: Do not use shell expansion tricks like "~/foo" or "../blah"
in these variables. Use full path names, please!

  FROM:, TO:   These variables should be set to the start and end
               of your range, either sha1 sums or tags.
	       NOTE: This range is INCLUSIVE (?).

               This command should return the complete list of sha1s
               between the commits without error:
               git rev-list --reverse <FROM>..<TO>

  INTERVAL:    How many commits will be skipped between builds when
               generating the bibisect repository, e.g. '64'

  ORDERMODE:   Either 'master' or 'tags', indicating which will be
               used in the FROM: and TO: fields.

  WORKDIR:     Location of the working directory you've created for
               building the bibisect repository, e.g. '/run/bibisect'

  SOURCEREPO:  Location of the LibreOffice core repository
  	       (I'm not sure why the .git subdir is specified, but
	        that's the format given)
               e.g. '/root/core/.git'

  BINREPO:     I think this is the path for the actual bibisect
               repository. This will be deleted/created during
               the process.  (example: '/root/binrepo')

  BUILDSCRIPT: Path to the buildscript. Don't touch this.

  Kicking off the script
  ----------------------

It's a simple Makefile. Just run 'make' in the bibisect directory.



USAGE for 'mergeranges'
-----------------------

The 'mergeranges' tool may be used to merge ranges of bibisect commits
together, regardless of whether they may be found in the same or
different git repositories.

To use the tool, you'll need a separate file containing the ranges of
commits to merge. Here's an example of a file containing ranges:

  50612eb408c515e3672952083b805be708d59c4a..remotes/bibisect35/master
  d38dc5cb288aeef58175a0d656091940a3f35ee5..remotes/bibisect36/master
  b4e60c226e714050f5ab0680669463b98ccd8ea8..remotes/bibisect40/master

NOTE: These ranges are *inclusive* -- we'll include ALL of these
commits in the new/expanded bibisect repository.

The script may be called as follows:

  ./mergeranges <file containing ranges>


  Step-by-Step Instructions for a New Repo
  ----------------------------------------

  Prep Cleanup
  ------------

(Things that may need to be cleaned up before you run mergeranges)

Tags that may already exist:
# UPDATE: we now use 'git tag -f', so if a tag already exists we'll
# just blow it away...
#
#  $ for i in `git tag -l|grep "source-hash"`; do git tag -d $i; done
#  $ git tag -d oldest last40onmaster last36onmaster last35onmaster

Branches:
# UPDATE:
# If it's actually a new repo, then it won't have a 'mergeranges' branch.
#
  $ git branch -D mergeranges

  Starting
  --------

Given:
 * Two different git bibisect repositories 'Alice' and 'Bob'
 * Alice with linear commits [50612eb4..5b4b36d8]
 * Bob with linear commits   [1f3b10d8..25428b1e]
 * The Bob range follows the Alice range
 
1) Create a new repo 'Combined'

2) Edit the 'ranges' file alongside mergeranges to contain:
   50612eb4..5b4b36d8
   1f3b10d8..25428b1e

   WARNING: Look through the commits carefully (especially the
   first/last commits), and see if there are any empty/stub commits
   that don't contain a build. If there are, cut those out of your
   range -- they'll just be in the way.

     Example:
       $ git log --oneline
       0777cd0 source-hash-b800d0b6ad74ce4a9adb23b865dd174d1eefa47b
       cc9a130 source-hash-12bcfec04fcbe6425e327109ad47cd2b2b80d2bd
       ...
       812c4a4 source-hash-dea4a3b9d7182700abeb4dc756a24a9e8dea8474
       b6c93c8 root

       Use the range: 812c4a4..0777cd0

3) cd into Combined (we'll run mergeranges from there)

4) Add Alice, Bob as remotes
  git remote add alice /home/qubit/alice/.git
  git remote add bob /home/qubit/bob/.git
  git remote update # This step might take a little while

5) Run the mergeranges script:
  ../dev-tools/bibisect/mergeranges ../dev-tools/bibisect/ranges

6) Cross your fingers!

  Step-by-Step Instructions for Adding to a Repo
  ----------------------------------------------

  Prep Cleanup
  ------------

(Things that may need to be cleaned up before you run mergeranges)

Tags:
   Tags may already exist, but we want to save many of them, so punt on this.

Branches:
  We want to save the 'mergeranges' branch

  Starting
  --------

Given:
 * Two different git bibisect repositories 'Alice' and 'Bob'
 * Alice with commits in a 'mergeranges' branch
 * The Bob range follows the Alice range
 * Bob with linear commits   [24c6e765..f36b371d]

1) Edit the 'ranges' file alongside mergeranges to contain:
   24c6e765..f36b371d

   WARNING: Look through the commits carefully (especially the
   first/last commits), and see if there are any empty/stub commits
   that don't contain a build. If there are, cut those out of your
   range -- they'll just be in the way.

2) cd into Alice (we'll run mergeranges from there)

3) Add Bob as a remote
  git remote add bob /home/qubit/bob/.git
  git remote update # This step might take a little while

4) Run the mergeranges script:
  ../dev-tools/bibisect/mergeranges ../dev-tools/bibisect/ranges

6) Cross your fingers!

  Cleanup After Merge
  -------------------

1) Remove the remotes
   git remote rm alice
   git remote rm bob

2) Tag the oldest commit (the script handles the latest commit)

   # NOTE: If you're using an existing 'mergeranges' branch, the
   # 'oldest' tag should already be set on the right commit!
   #
   # Note: The following should theoretically work, but there's an
   # extra 'root' commit in the source repos (perhaps I could remove them?)
   #git tag oldest `git rev-list --max-parents=0`
   git tag oldest 65fd30f5

3) git gc
   Starting size: 8.4GB
   After gc:      8.3GB

   (Testing with a smaller merged repo:
      Starting size: 3.8GB
      After gc:      3.7GB)

4) Upload/save a copy before aggressively gc'ing the thing

5) (OPTIONAL) git gc --aggressive
   This will sometimes/often fail, especially when run on GB's of
   data. I've had it fail several times -- be prepared for sadness... :P

6) Try checking-out the repo from the server
   This repo is only 7.7GB in size (after checking-out 'mergeranges',
   it's 8.2GB on disk)

7) (TEST BANDWIDTH/SPEED)
   Add a new build to the repo (I'm just using 4.2.0.0.beta1 as test data);

   Commit:
     1-2 minutes (very quick)
   git push:
     2.5 minutes (Size: 154.23 MiB | 2.61 MiB/s) # Big because of gc?
   # On the local checkout of the bibisect repo
   git remote update: 
     1.5 minutes (Size: 154.23 MiB | 1.77 MiB/s)

   Conclusion: Rather speedy, esp. over WiFi.
