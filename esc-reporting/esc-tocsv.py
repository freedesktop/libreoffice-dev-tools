#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#








import sys
import csv
import io
import os
import operator
import datetime
import json
import xmltodict


def util_load_data_file(fileName):
    try:
      fp = open(fileName, encoding='utf-8')
      rawData = json.load(fp)
      fp.close()
    except Exception as e:
      print('Error load file ' + fileName + ' due to ' + str(e))
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



def runCfg(platform):
    global cfg
    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/jani/esc'
    cfg = util_load_data_file(homeDir + '/config.json')
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    print("Reading and writing data to " + cfg['homedir'])

    cfg['award-mailed'] = util_load_data_file(cfg['homedir'] + 'award.json')['award-mailed']
    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    return cfg


def doPrint(title, var, fp, useTop=53):
    print(title, end='', file=fp)
    for i in range(1, useTop):
        print(str(var[i]) + ';', end='', file=fp)
    print('', file=fp)



def loadWeekGenerateCSV(argv):
    global cfg, statList

    stats = []
    for i in argv[1:]:
        stats.append(util_load_data_file(cfg['homedir'] + 'weeks/' + i))

    stats2016 = util_load_data_file(cfg['homedir'] + 'weeks/week_2017_01.json')
    statList = util_load_data_file(cfg['homedir'] + 'stats.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')

    csv = {'git': {'committer':      {'week': [0] * 53, 'sum': [0] * 53, 'avg': [0] * 53},
                   'contributor':    {'week': [0] * 53, 'sum': [0] * 53, 'avg': [0] * 53},
                   'committer_cnt':  {'week': [0] * 105, 'all': [0] * 105, 'avg': [0] * 105},
                   'contributor_cnt': {'week': [0] * 105, 'all': [0] * 105, 'avg': [0] * 105}},
                   'gerrit': {'committer':   {'merged':   {'week': [0] * 53, 'sum': [0] * 53, 'avg': [0] * 53},
                                      'reviewed': {'week': [0] * 53, 'sum': [0] * 53, 'avg': [0] * 53}},
                      'contributor': {'merged':   {'week': [0] * 53, 'sum': [0] * 53, 'avg': [0] * 53}}},
           'easyhacks': {'assigned': [0] * 53, 'open': [0] * 53},
           'trend': {'header':      ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','<100','<200','<300','<400','<500',
                                     '<600','<700','<800','<900','<1000','many'],
                     'count':       [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,100,200,300,400,500,600,700,800,900,1000,5000],
                     'committer':   [0] * 27,
                     'contributor': [0] * 27}}

    startDate = datetime.datetime(day=25,month=12,year=2014)
    cutDate = datetime.datetime(day=29,month=12,year=2016)
    weekSum = { 'committer' : [],
                'committer1' : [],
                'contributor': [],
                'contributor1': [],
                'firsttime' : []}
    for i in range(0,105):
        weekSum['committer'].append([])
        weekSum['committer1'].append([])
        weekSum['contributor'].append([])
        weekSum['contributor1'].append([])

    for key, row in gitData['commits'].items():
        xDate = datetime.datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S").replace(hour=0, minute=0, second=0, microsecond=0)
        if xDate < startDate or xDate >= cutDate:
            continue
        email = row['author-email'].lower()
        if email in statList['aliases']:
            email = statList['aliases'][email]
        if not email in statList['people']:
            raise Exception('email cannot be found!')
        week = int(((xDate - startDate).days / 7))
        x = (xDate - startDate).days
        if statList['people'][email]['isCommitter']:
            xType = 'committer'
        else:
            xType = 'contributor'
        xType1 = xType + '1'
        if not email in weekSum[xType1][week]:
            weekSum[xType1][week].append(email)
        elif not email in weekSum[xType][week]:
            weekSum[xType][week].append(email)

    committerSum = 0
    contributorSum = 0
    for i in range(1,105):
        csv['git']['committer_cnt']['all'][i] = len(weekSum['committer1'][i-1])
        csv['git']['committer_cnt']['week'][i] = len(weekSum['committer'][i-1])
        csv['git']['contributor_cnt']['all'][i] = len(weekSum['contributor1'][i-1])
        csv['git']['contributor_cnt']['week'][i] = len(weekSum['contributor'][i-1])
        committerSum += csv['git']['committer_cnt']['week'][i]
        csv['git']['committer_cnt']['avg'][i] = int(committerSum / i)
        contributorSum += csv['git']['contributor_cnt']['week'][i]
        csv['git']['contributor_cnt']['avg'][i] = int(contributorSum / i)

    trendLgd = len(csv['trend']['header'])
    for i in range(1,trendLgd):
        for ent in stats2016['data']['trend']['committer']['owner']['1year']:
            x = int(ent)
            if x > csv['trend']['count'][i-1] and x <= csv['trend']['count'][i]:
                csv['trend']['committer'][i] += stats2016['data']['trend']['committer']['owner']['1year'][ent]
        for ent in stats2016['data']['trend']['contributor']['owner']['1year']:
            x = int(ent)
            if x > csv['trend']['count'][i-1] and x <= csv['trend']['count'][i]:
                csv['trend']['contributor'][i] += stats2016['data']['trend']['contributor']['owner']['1year'][ent]

    i = 1
    type1 = True
    for week in stats:
        csv['git']['committer']['week'][i] = week['data']['commits']['committer']['1week']['owner']
        csv['git']['committer']['sum'][i] = csv['git']['committer']['week'][i]
        csv['git']['contributor']['week'][i] = week['data']['commits']['contributor']['1week']['owner']
        csv['git']['contributor']['sum'][i] = csv['git']['contributor']['week'][i]

        csv['gerrit']['committer']['merged']['week'][i] = week['data']['gerrit']['committer']['1week']['MERGED']
        csv['gerrit']['committer']['merged']['sum'][i]  = csv['gerrit']['committer']['merged']['week'][i]
        csv['gerrit']['committer']['reviewed']['week'][i] = week['data']['gerrit']['committer']['1week']['reviewed']
        csv['gerrit']['committer']['reviewed']['sum'][i] = csv['gerrit']['committer']['reviewed']['week'][i]

        csv['gerrit']['contributor']['merged']['week'][i] = week['data']['gerrit']['contributor']['1week']['MERGED']
        csv['gerrit']['contributor']['merged']['sum'][i] = csv['gerrit']['contributor']['merged']['week'][i]

        csv['easyhacks']['assigned'][i] = week['data']['easyhacks']['assigned']
        csv['easyhacks']['open'][i] = week['data']['easyhacks']['open']
        i += 1

    for i in range(1,53):
        csv['git']['committer']['sum'][i] += csv['git']['committer']['sum'][i-1]
        csv['git']['committer']['avg'][i] = int(csv['git']['committer']['sum'][i] / i)
        csv['git']['contributor']['sum'][i] += csv['git']['contributor']['sum'][i-1]
        csv['git']['contributor']['avg'][i] = int(csv['git']['contributor']['sum'][i] / i)
        csv['gerrit']['committer']['merged']['sum'][i]  += csv['gerrit']['committer']['merged']['sum'][i-1]
        csv['gerrit']['committer']['merged']['avg'][i]  = int(csv['gerrit']['committer']['merged']['sum'][i] / i)
        csv['gerrit']['committer']['reviewed']['sum'][i] += csv['gerrit']['committer']['reviewed']['sum'][i-1]
        csv['gerrit']['committer']['reviewed']['avg'][i] = int(csv['gerrit']['committer']['reviewed']['sum'][i] / i)
        csv['gerrit']['contributor']['merged']['sum'][i] += csv['gerrit']['contributor']['merged']['sum'][i-1]
        csv['gerrit']['contributor']['merged']['avg'][i] = int(csv['gerrit']['contributor']['merged']['sum'][i] / i)

    with open('/Users/jani/TMPesc.csv', 'w') as fp:
        print('Mentoring 2016;', file=fp)
        print('', file=fp)
        print('origin;type;art;', end='', file=fp)
        for i in range(1,53):
            print('week' + str(i) + ';', end='', file=fp)
        print('', file=fp)
        doPrint('git;committer;week;', csv['git']['committer']['week'], fp)
        doPrint('git;committer;sum;', csv['git']['committer']['sum'], fp)
        doPrint('git;committer;avg;', csv['git']['committer']['avg'], fp)
        print('', file=fp)
        doPrint('git;contributor;week;', csv['git']['contributor']['week'], fp)
        doPrint('git;contributor;sum;', csv['git']['contributor']['sum'], fp)
        doPrint('git;contributor;avg;', csv['git']['contributor']['avg'], fp)
        print('', file=fp)
        doPrint('gerrit;committer;week-merged;', csv['gerrit']['committer']['merged']['week'], fp)
        doPrint('gerrit;committer;sum-merged;', csv['gerrit']['committer']['merged']['sum'], fp)
        doPrint('gerrit;committer;avg-merged;', csv['gerrit']['committer']['merged']['avg'], fp)
        print('', file=fp)
        doPrint('gerrit;committer;week-reviewed;', csv['gerrit']['committer']['reviewed']['week'], fp)
        doPrint('gerrit;committer;sum-reviewed;', csv['gerrit']['committer']['reviewed']['sum'], fp)
        doPrint('gerrit;committer;avg-reviewed;', csv['gerrit']['committer']['reviewed']['avg'], fp)
        print('', file=fp)
        doPrint('gerrit;contributor;week-merged;', csv['gerrit']['contributor']['merged']['week'], fp)
        doPrint('gerrit;contributor;sum-merged;', csv['gerrit']['contributor']['merged']['sum'], fp)
        doPrint('gerrit;contributor;avg-merged;', csv['gerrit']['contributor']['merged']['avg'], fp)
        print('', file=fp)
        print('Number of patches versus number of people;', file=fp)
        print('number of patches;;;', end='', file=fp)
        for i in range(1, trendLgd):
            print('"' + csv['trend']['header'][i] + '";', end='', file=fp)
        print('', file=fp)
        print('committers;;;', end='', file=fp)
        for i in range(1, trendLgd):
            print(str(csv['trend']['committer'][i]) + ';', end='', file=fp)
        print('', file=fp)
        print('contributors;;;', end='', file=fp)
        for i in range(1, trendLgd):
            print(str(csv['trend']['contributor'][i]) + ';', end='', file=fp)
        print('', file=fp)
        print('', file=fp)
        doPrint('git;contributor;week-cnt;', csv['git']['contributor_cnt']['week'], fp, useTop=105)
        doPrint('git;contributor;week-all;', csv['git']['contributor_cnt']['all'], fp, useTop=105)
        doPrint('git;contributor;week-avg;', csv['git']['contributor_cnt']['avg'], fp, useTop=105)
        print('', file=fp)
        doPrint('git;committer;week-cnt;', csv['git']['committer_cnt']['week'], fp, useTop=105)
        doPrint('git;committer;week-all;', csv['git']['committer_cnt']['all'], fp, useTop=105)
        doPrint('git;committer;week-avg;', csv['git']['committer_cnt']['avg'], fp, useTop=105)

    print('done see /tmp/esc.csv')


if __name__ == '__main__':
    runCfg(sys.platform)
    loadWeekGenerateCSV(sys.argv)
