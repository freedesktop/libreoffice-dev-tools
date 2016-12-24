#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#


### DESCRIPTION
#
# This program collect data from
#     Openhub (including history and committer list)
#     Bugzilla (including comments and history)
#     Gerrit (including list of committers)
#     Git (all LibreOffice repos)
#
# The data is dumped to json files, with a history of minimum 1 year
#     esc/dump/['openhub','bugzilla','gerrit','git']_dump.json
#
# The JSON is a 1-1 copy of the data in the systems
# This program should only be changed when one of systems is updated.
#
# Installed on vm174:/usr/local/bin runs every night (making delta collection)
#
# Remark this program put a heavy load on our services, so please do not just run it.
# For analysis and reporting see the 2 other programs available.
#

import sys
import csv
import io
import os
import operator
import datetime
import json
import xmltodict
import requests
from requests.auth import HTTPDigestAuth



def util_load_file(fileName):
    try:
      fp = open(fileName, encoding='utf-8')
      rawData = json.load(fp)
      fp.close()
    except Exception as e:
      print('Error load file ' + fileName + ' due to ' + str(e))
      rawData = None
      pass
    return rawData



def util_load_url(url, useDict=False, useRaw=False, uUser=None, uPass=None):
    try:
      if uUser is None:
        r = requests.get(url)
        if useDict:
          rawData = xmltodict.parse(r.text)
        elif useRaw:
          rawData = r.text
        else:
          rawData = r.json()
      else:
        r = requests.get(url, auth=HTTPDigestAuth(uUser, uPass))
        rawData = json.loads(r.text[5:])
      r.close()
    except Exception as e:
      print('Error load url ' + url + ' due to ' + str(e))
      exit(-1)
    return rawData



def util_dump_file(fileName, rawList):
    try:
      fp = open(fileName, 'w', encoding='utf-8')
      json.dump(rawList, fp, ensure_ascii=False, indent=4, sort_keys=True)
      fp.close()
    except Exception as e:
      print('Error dump file ' + fileName + ' due to ' + str(e))
      os.remove(fileName)
      exit(-1)



def util_load_data_file(cfg, fileName, funcName, rawListProto):
    rawList = util_load_file(fileName)
    if rawList == None:
      rawList = rawListProto
      rawList['newest-entry'] = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d 00")
      print('retrieving full year of ' + funcName + ', take a coffee')
    searchDate = datetime.datetime.strptime(rawList['newest-entry'], "%Y-%m-%d %H") - datetime.timedelta(days=2)
    return searchDate, rawList



def get_openhub(cfg):
    fileName = cfg['homedir'] + 'dump/openhub_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'openhub', {'project': {}, 'people': {}})
    newDate = searchDate
    print("Updating openHub dump from " + rawList['newest-entry'])

    urlBase = 'https://www.openhub.net/p/libreoffice'
    url = urlBase + '.xml?api_key=' + cfg['openhub']['api-key']
    rawList['project'] = util_load_url(url, useDict=True)['response']['result']['project']

    url = urlBase + '/contributors.xml?api_key=' + cfg['openhub']['api-key'] + '&sort=latest_commit&page='
    pageId = -1
    while True:
      pageId += 1
      idList = util_load_url(url + str(pageId), useDict=True)['response']['result']['contributor_fact']
      for row in idList:
        rawList['people'][row['contributor_id']] = row
      xDate = datetime.datetime.strptime(idList[-1]['last_commit_time'], "%Y-%m-%dT%H:%M:%SZ")
      if xDate < searchDate:
        break
      if xDate > newDate:
        newDate = xDate
    rawList['newest-entry'] = newDate.strftime("%Y-%m-%d %H")

    util_dump_file(fileName, rawList)
    return rawList



def get_bugzilla(cfg):
    fileName = cfg['homedir'] + 'dump/bugzilla_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'bugzilla', {'bugs': {}})
    print("Updating bugzilla dump from " + rawList['newest-entry'])

    url = 'https://bugs.documentfoundation.org/rest/bug?' \
          '&order=changeddate&chfieldto=Now&chfieldfrom=' + searchDate.strftime("%Y-%m-%d") + \
          '&limit=200&offset='
    newList = []
    while True:
      tmp = util_load_url(url + str(len(newList)))['bugs']
      if len(tmp) == 0:
        break
      newList.extend(tmp)

    urlH = 'https://bugs.documentfoundation.org/rest/bug/{}/history'
    urlC = 'https://bugs.documentfoundation.org/rest/bug/{}/comment'
    cnt = 0
    for row in newList:
      id = str(row['id'])
      if not 'cc' in row:
        row['cc'] = []
      if not 'keywords' in row:
        row['keywords'] = []
      tmp = util_load_url(urlH.format(id))
      row['history'] = tmp['bugs'][0]['history']
      tmp = util_load_url(urlC.format(id))
      row['comments'] = tmp['bugs'][id]['comments']
      rawList['bugs'][id] = row
      xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
      if xDate > searchDate:
        searchDate = xDate
      cnt += 1
      if cnt > 400:
        rawList['newest-entry'] = searchDate.strftime('%Y-%m-%d %H')
        util_dump_file(fileName, rawList)
        cnt = 0

    rawList['newest-entry'] = searchDate.strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def get_gerrit(cfg):
    fileName = cfg['homedir'] + 'dump/gerrit_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'gerrit', {'patch': {}, 'committers' : []})
    print("Updating gerrit dump from " + rawList['newest-entry'])

    urlBase = 'https://gerrit.libreoffice.org/a/'
    uid = cfg['gerrit']['user']
    upw = cfg['gerrit']['password']
    rawList['committers'] = []
    tmp = util_load_url(urlBase + 'groups/Committers/members', uUser=uid, uPass=upw)
    for row in tmp:
      for i in 'username', 'email':
        if not i in row:
          row[i] = '*DUMMY*'
      rawList['committers'].append(row)

    url = urlBase + 'changes/?q=after:' + searchDate.strftime("%Y-%m-%d") + \
         '&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS&o=MESSAGES&limit=200&start='
    offset = 0
    if 'offset' in rawList:
      offset = int(rawList['offset'])
    while True:
      tmp = util_load_url(url + str(offset), uUser=uid, uPass=upw)
      for row in tmp:
        for i in 'email', 'username', 'name':
          if not i in row['owner']:
            row['owner'][i] = '*DUMMY*'
        for x in row['messages']:
          if not 'author' in x:
            x['author'] = {}
          for i in 'email', 'username', 'name':
            if not i in x['author']:
              x['author'][i] = '*DUMMY*'
        for i in 'Verified', 'Code-Review':
          if not i in row['labels']:
            row['labels'][i] = {}
          if not 'all' in row['labels'][i]:
            row['labels'][i]['all'] = []
          for x in row['labels'][i]['all']:
            if 'name' not in x:
              x['name'] = '*DUMMY*'
            if 'email' not in x:
              x['email'] = '*DUMMY*'
            if 'username' not in x:
              x['username'] = '*DUMMY*'
            if 'value' not in x:
              x['value'] = 0

        rawList['patch'][str(row['_number'])] = row
        xDate = datetime.datetime.strptime(row['updated'], "%Y-%m-%d %H:%M:%S.%f000")
        if xDate > searchDate:
          searchDate = xDate
      if '_more_changes' in tmp[-1] and tmp[-1]['_more_changes'] == True:
        rawList['offset'] = offset
        offset += len(tmp)
        del rawList['patch'][str(row['_number'])]['_more_changes']
      else:
        break
    if 'offset' in rawList:
      del rawList['offset']

    rawList['newest-entry'] = searchDate.strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def get_git(cfg):
    fileName = cfg['homedir'] + 'dump/git_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'git', {'commits': {}})
    print("Updating git dump from " + rawList['newest-entry'])

    for repo in cfg['git']['repos']:
      print(' working on ' + repo['name'])
      useFormat = '{"hash": "%H", "date": "%ci", "author": "%an", "author-email": "%ae", ' \
                  '"committer": "%cn", "committer-email": "%ce" }'
      basedir = cfg['homedir'] + '../libreoffice/'
      if repo['git'] and cfg['platform'] == 'linux':
        os.system('(cd ' + basedir + repo['dir'] + ';git pull -r;git fetch --all) > /dev/null')
      os.system('(cd ' + basedir + repo['dir'] + ";git log --pretty=format:'" + useFormat + "') > /tmp/git.log")
      fp = open('/tmp/git.log', encoding='utf-8')
      while True:
        x = fp.readline()
        if x is None or x == '':
          break
        row = json.loads(x)
        row['repo'] = repo['name']
        key = repo['name'] + '_' + row['hash']
        if not key in rawList['commits']:
          row['date'] = row['date'][:-6]
          rawList['commits'][key] = row
        x = row['date'].split(' ')[:2]
        xDate = datetime.datetime.strptime(x[0]+' '+x[1], "%Y-%m-%d %H:%M:%S")
        if xDate < searchDate:
          break

    nDate = searchDate
    for key in rawList['commits']:
      xDate = datetime.datetime.strptime(rawList['commits'][key]['date'], "%Y-%m-%d %H:%M:%S")
      if xDate > nDate:
        nDate = xDate

    rawList['newest-entry'] = nDate.strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def runCfg(platform):
    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/jani/esc'
    cfg = util_load_file(homeDir + '/config.json')
    if cfg == None:
        exit(-1)
    keys = util_load_file(homeDir + '/config_collect.json')
    if keys == None:
        exit(-1)

    cfg.update(keys)
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    print("Reading and writing data to " + cfg['homedir'])
    return cfg



def runBuild(cfg):
    openhubData = get_openhub(cfg)
    bugzillaData = get_bugzilla(cfg)
    gerritData = get_gerrit(cfg)
    gitData = get_git(cfg)



if __name__ == '__main__':
    runBuild(runCfg(sys.platform))
