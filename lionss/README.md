Lionss
======

Introduction
--------------
The python webapp provides a web GUI to search for UI strings in LO code base, show all occurrences, and let you decide which one you want to search the references for in OpenGrok.

OpenGrok has some issues which forced us to do this app. Else it would be able to cope with it.


Notes on implementation
-------------------------------
### Choices

We used Python 2.7, with `web.py` and `pylev` specific packages.

We rely on a standard git repository. Due to architecture of .ui files and their references, we cannot use a bare repo now *(at least I don't know how. Well, it is handled by the code, but not supported anymore, actually)*.
We rely on git being in the path.

Strategy is we query for terms including all letters and same number of occurrences. Then we refine with levenshtein algorithm. So jokers are not allowed in search field. Once we found referenced text in .ui, we search for the same in the sources to provides all its uses, and link them to OpenGrok.

### WebApp

We kept the module layout although it is very small, because it is also a training for my Python skills

#### Config

The configuration file holds:

* the git repo path
* the OpenGrok LO base url for queries
* the analysis config: file extensions, patterns for deciphering. It is held in a dict as we may want more items later (we had with [hs]rc + ui).

### Script

Not done since moving to .ui makes current work invalid. I will wait for validation of webapp before going into script.

*Draft* : The python script does roughly the same workflow, but shows you file paths and lines so you can go through them in your shell.

### Deployment

+ Bundled webserver of  `web.py` : smooth
+ Managed to configure Apache + mod_wsgi : some tricks, but that's Apache
+ Tried heroku, but lack of filesystem (was simple, though)
+ Tried OpenShift: has a small quota filesystem (1GB) for the free plan, but is a pain to configure
  + A first level is almost useless, because wsgi expects either a ./wsgi.py or a /wsgi with some content.
  + static files are expected in a specific place, so if you want to keep the framework struct, you need a `.htaccess` to redirect that.
  + doesn't accept a module folder whose name is the same as base script.
  + To keep in the 1GB allowed:
    + `git clone -n --single-branch https://git.libreoffice.org/core lo_core  (~900MB out of 1GB)`
    + `git config core.sparsecheckout true`
    + `echo *.ui > .git/info/sparse-checkout`
    + `git grep -l "" HEAD -- *.ui  | awk -F:  '{print $2}' | xargs git checkout HEAD --`
