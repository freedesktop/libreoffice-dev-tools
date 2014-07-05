#!/usr/bin/env python
# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# LIbreOffice Normative-Strings Searcher
import web
from web import form
import os
import subprocess
from subprocess import CalledProcessError
import traceback
import _lionss.gitter
from config import *

version = '0.7.1'
urls = (
    '/', 'index',
    '/pick(.*)', 'pick'
)

render = web.template.render(os.path.join(os.path.dirname(__file__), 'tpl/'))

searcher = form.Form(
    form.Textbox('SString', form.notnull, description = 'Searched String'),
    form.Textbox('lev', 
                    form.regexp('\d+', 'Must be a figure between 1 (strict) and 100 (loose)'),
                    form.Validator('Must be more than 0', lambda x:int(x)>0),
                    form.Validator('Must be less than 101', lambda x:int(x)<=100),
                    description = 'Strictness', size = "5", default = "0", value = "1" ),
    form.Checkbox('case', description = 'Case-Sensitive', value='case', checked='true'),
    form.Button('Try to find',type = "submit"),
    ) 


web.template.Template.globals['footerhtml'] = render.footer()

class index:
    def GET(self):
        web.template.Template.globals['headerhtml'] = render.header(version, '')
        ttf = searcher() # ttf = Try To Find :)
        return render.index(ttf)

    def POST(self):
        web.template.Template.globals['url'] = web.ctx['realhome']
        web.template.Template.globals['headerhtml'] = render.header(version, 'ERROR')
        ttf = searcher()
        if not ttf.validates():
            return render.index(ttf)
        dbgstr = ""

        try:
            finder = _lionss.gitter.worker(ttf.SString.value, 
                                ttf.case.checked, repo_localpath)

            # search for approximate values
            dbg = finder.start( gg_settings[0])

            # check for levenshtein test
            finder.apply_lev(int(ttf.lev.value))
            web.template.Template.globals['headerhtml'] = render.header(version, 'Search results')

            # we will crash if there are empty proposals. Should only occur if 
            # generic structure of file change (split of string inside grep result)
            return render.result(finder.proposals, str(ttf.SString.value))
            #~ return render.result(finder.proposals, str(dbg))

        except CalledProcessError as e:
            return render.error(str(e))
        except Exception as e:
            return render.error(traceback.format_exc()+"\n"+ dbgstr)


class pick:
    def GET(self, mangled):
        ''' [http://127.0.0.1:8080/pick]/Smart%20Tag/sw/source/ui/smartmenu/stmenu.src/32 '''
        ''' None needle filename line '''
        
        web.template.Template.globals['headerhtml'] = render.header(version, 'ERROR')
        identity = mangled.split('/')
        
        if identity[0]:
            return render.error('MALFORMED URL ::' + identity[0] + '::')
            
        filename = os.path.join(repo_localpath, '/'.join(identity[2:-1]))
        line = int(identity[-1])
        
        resid = filename.split('uiconfig/')[1]
        if isinstance(resid, (int, long)): # resid should be a string
            return render.error('Stopped at '+str(resid))
        if not resid:
            return render.error('Resource ID not found for ' + identity[1])
        grok_url = og_root + resid
        raise web.seeother(grok_url)

if __name__ == "__main__":
	web.config.debug = True
	app = web.application(urls, globals())
    app.run()
else:
    web.config.debug = False
    app = web.application(urls, globals(), autoreload=False)
    application = app.wsgifunc()

# vim: set noet sw=4 ts=4:
