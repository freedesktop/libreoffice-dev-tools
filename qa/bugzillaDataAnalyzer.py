#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common
import datetime

reportPeriodDays = 365

# Use enhancements, bugs, all
kindOfData = ['enhancements', 'bugs', 'all']

lKeywords = ['haveBacktrace', 'regression', 'bisected']


def util_create_basic_schema():
    return {
        'id': [],
        'author': [],
        'split_week': {},
        'split_month': {},
        'component': {},
        'product': {p : 0 for p in common.product_list},
        'system': {s : 0 for s in common.system_list},
        'platform': {},
        'status': {s : 0 for s in common.statutes_list},
        'resolution': {},
        'difftime': []
        }

def util_create_ticket_schema():
    return {
        'created': util_create_basic_schema(),
        'confirmed': util_create_basic_schema(),
        'closed': util_create_basic_schema(),
        'fixed': util_create_basic_schema(),
        'keywords': { k : util_create_basic_schema() for k in lKeywords},
        }

def util_create_statList():
    return {
        'enhancements' : util_create_ticket_schema(),
        'bugs' : util_create_ticket_schema(),
        'all' : util_create_ticket_schema(),
        'people' : {},
        'stat': {'oldest': datetime.datetime.now(), 'newest': datetime.datetime(2001, 1, 1)}
    }

def util_increase_action(value, rowId, creatorMail, status, product,
        component, resolution, platform, system, week, month, difftime=-1):
    value['id'].append(rowId)
    value['author'].append(creatorMail)
    value['status'][status] += 1
    value['product'][product] += 1

    if component not in value['component']:
        value['component'][component] = 0
    value['component'][component] += 1

    if resolution not in value['resolution']:
        value['resolution'][resolution] = 0
    value['resolution'][resolution] += 1

    if platform not in value['platform']:
        value['platform'][platform] = 0
    value['platform'][platform] += 1

    if system not in value['system']:
        value['system'][system] = 0
    value['system'][system] += 1

    if week not in value['split_week']:
        value['split_week'][week] = 0
    value['split_week'][week] += 1

    if month not in value['split_month']:
        value['split_month'][month] = 0
    value['split_month'][month] += 1

    if difftime >= 0:
        value['difftime'].append(difftime)

def util_decrease_action(value, rowId, creatorMail, status, product,
        component, resolution, platform, system, week, month):
    value['id'].pop()
    value['author'].pop()
    value['status'][status] -= 1
    value['product'][product] -= 1
    value['component'][component] -= 1
    value['resolution'][resolution] -= 1
    value['platform'][platform] -= 1
    value['system'][system] -= 1
    value['split_week'][week] -= 1
    value['split_month'][month] -= 1

    if value['difftime']:
        value['difftime'].pop()

def check_kindOfTicket(severity):
    if severity == 'enhancement':
        return 'enhancements'
    else:
        return 'bugs'

def analyze_bugzilla_data(statList, bugzillaData, cfg):
    print("Analyzing bugzilla\n", end="", flush=True)
    statNewDate = statList['stat']['newest']
    statOldDate = statList['stat']['oldest']

    statList['addDate'] = datetime.date.today().strftime('%Y-%m-%d')

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'] != 'deletionrequest':
            creationDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
            if creationDate < statOldDate:
                statOldDate = creationDate
            if creationDate > statNewDate:
                statNewDate = creationDate

            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            kindOfTicket = check_kindOfTicket(row['severity'])
            rowComponent = row['component']
            rowPlatform = row['platform']
            rowSystem = row['op_sys']
            rowProduct = row['product']

            #get information about created bugs in reportPeriod
            if creationDate >= cfg['reportPeriod']:
                week = str(creationDate.year) + '-' + str(creationDate.strftime("%V"))
                month = str(creationDate.year) + '-' + str(creationDate.strftime("%m"))
                util_increase_action(statList[kindOfTicket]['created'], rowId, creatorMail, rowStatus, rowProduct,
                    rowComponent, rowResolution, rowPlatform, rowSystem, week, month)

                util_increase_action(statList['all']['created'], rowId, creatorMail, rowStatus, rowProduct,
                    rowComponent, rowResolution, rowPlatform, rowSystem, week, month)

            common.util_check_bugzilla_mail(
                    statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            isFixed = False
            isClosed = False
            isConfirmed = False
            weekConfirmed = None
            monthConfirmed = None
            weekClosed = None
            monthClosed = None
            weekFixed = None
            monthFixed = None

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                common.util_check_bugzilla_mail(
                        statList, actionMail, '', actionDate, rowId)

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:
                    if change['field_name'] == 'is_confirmed':
                        if actionDate >= cfg['reportPeriod'] and row['is_confirmed']:
                            if change['added'] == "1":
                                weekConfirmed = str(actionDate.year) + '-' + str(actionDate.strftime("%V"))
                                monthConfirmed = str(actionDate.year) + '-' + str(actionDate.strftime("%m"))
                                difftimeConfirmed = (actionDate - creationDate).days
                                util_increase_action(statList[kindOfTicket]['confirmed'], rowId, actionMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekConfirmed, monthConfirmed, difftimeConfirmed)

                                util_increase_action(statList['all']['confirmed'], rowId, actionMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekConfirmed, monthConfirmed, difftimeConfirmed)

                                isConfirmed = True

                            elif isConfirmed:
                                util_decrease_action(statList[kindOfTicket]['confirmed'], rowId, creatorMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekConfirmed, monthConfirmed)

                                util_decrease_action(statList['all']['confirmed'], rowId, creatorMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekConfirmed, monthConfirmed)

                                isConfirmed = False

                    if change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if actionDate >= cfg['reportPeriod'] and not common.isClosed(removedStatus) and \
                                common.isClosed(addedStatus) and common.isClosed(row['status']):
                            if isClosed:
                                util_decrease_action(statList[kindOfTicket]['closed'], rowId, creatorMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekClosed, monthClosed)

                                util_decrease_action(statList['all']['closed'], rowId, creatorMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekClosed, monthClosed)

                            weekClosed = str(actionDate.year) + '-' + str(actionDate.strftime("%V"))
                            monthClosed = str(actionDate.year) + '-' + str(actionDate.strftime("%m"))
                            difftimeClosed = (actionDate - creationDate).days
                            util_increase_action(statList[kindOfTicket]['closed'], rowId, actionMail, rowStatus, rowProduct,
                                rowComponent, rowResolution, rowPlatform, rowSystem, weekClosed, monthClosed, difftimeClosed)

                            util_increase_action(statList['all']['closed'], rowId, actionMail, rowStatus, rowProduct,
                                rowComponent, rowResolution, rowPlatform, rowSystem, weekClosed, monthClosed, difftimeClosed)

                            isClosed = True

                        if  addedStatus == 'RESOLVED' or addedStatus == 'VERIFIED':
                            if(rowResolution):
                                addedStatus = addedStatus + "_" + rowResolution
                            else:
                                newStatus = addedStatus

                        if actionDate >= cfg['reportPeriod'] and addedStatus == 'RESOLVED_FIXED' and \
                                removedStatus != 'REOPENED' and row['resolution'] == 'FIXED':
                            if isFixed:
                                util_decrease_action(statList[kindOfTicket]['fixed'], rowId, creatorMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekFixed, monthFixed)

                                util_decrease_action(statList['all']['fixed'], rowId, creatorMail, rowStatus, rowProduct,
                                    rowComponent, rowResolution, rowPlatform, rowSystem, weekFixed, monthFixed)

                            weekFixed = str(actionDate.year) + '-' + str(actionDate.strftime("%V"))
                            monthFixed = str(actionDate.year) + '-' + str(actionDate.strftime("%m"))
                            difftimeFixed = (actionDate - creationDate).days
                            util_increase_action(statList[kindOfTicket]['fixed'], rowId, actionMail, rowStatus, rowProduct,
                                rowComponent, rowResolution, rowPlatform, rowSystem, weekFixed, monthFixed, difftimeFixed)

                            util_increase_action(statList['all']['fixed'], rowId, actionMail, rowStatus, rowProduct,
                                rowComponent, rowResolution, rowPlatform, rowSystem, weekFixed, monthFixed, difftimeFixed)

                            isFixed = True

                    elif change['field_name'] == 'resolution':
                        if newStatus:
                            addedStatus = newStatus + "_" + change['added']

                            newStatus = None

                    elif change['field_name'] == 'keywords':
                        keywordsAdded = change['added'].split(", ")
                        for keyword in keywordsAdded:
                            if keyword in lKeywords:
                                if actionDate >= cfg['reportPeriod'] and keyword in rowKeywords:
                                    weekKeyword = str(actionDate.year) + '-' + str(actionDate.strftime("%V"))
                                    monthKeyword = str(actionDate.year) + '-' + str(actionDate.strftime("%m"))
                                    difftimeKeyword = (actionDate - creationDate).days
                                    util_increase_action(statList[kindOfTicket]['keywords'][keyword], rowId, actionMail, rowStatus, rowProduct,
                                        rowComponent, rowResolution, rowPlatform, rowSystem, weekKeyword, monthKeyword, difftimeKeyword)

                                    util_increase_action(statList['all']['keywords'][keyword], rowId, actionMail, rowStatus, rowProduct,
                                        rowComponent, rowResolution, rowPlatform, rowSystem, weekKeyword, monthKeyword, difftimeKeyword)

            commentMail = None
            comments = row['comments'][1:]
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(
                        statList, commentMail, '', commentDate, rowId)

            for person in row['cc_detail']:
                email = person['email']
                if commentMail == email or actionMail == email:
                    common.util_check_bugzilla_mail(statList, email, person['real_name'])

    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")


    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])

def util_print_QA_line_data(statList, dValue, kind, action, total_count):

    fileName = '/tmp/data_' + action + '_' + kind + '_report.txt'
    fp = open(fileName, 'w', encoding='utf-8')
    print('Creating ' + action + ' ' + kind + ' report in ' + fileName)

    print(('  * {} {} {}.').format(len(dValue['id']), kind, action), file=fp)

    #Count the number of reps
    my_dict = {i: dValue['author'].count(i) for i in dValue['author']}

    d_view = [(v, k) for k, v in my_dict.items()]
    d_view.sort(reverse=True)

    print('  * Total users: {}'.format(len(d_view)), file=fp)

    usersString = '  * Done by: \n'
    count = 0
    for i1,i2 in d_view:
        try:
            count += 1
            if count <= total_count:
                usersString += statList['people'][i2]['name'] + ' ( ' + str(i1) + ' ) \n'
            else:
                break
        except:
            continue

    print(usersString[:-2], file=fp)

    print(file=fp)
    print('   * {} {} by week'.format(kind, action), file=fp)
    for key, value in sorted(dValue['split_week'].items()):
        print('{}: {}'.format(key, value), file=fp)


    print(file=fp)
    print('   * {} {} by month'.format(kind, action), file=fp)

    for key, value in sorted(dValue['split_month'].items()):
        print('{}: {}'.format(key, value), file=fp)

    print(file=fp)
    print('   * Components of {} {}'.format(kind, action), file=fp)
    util_print_QA_line(fp, dValue['component'])

    print(file=fp)
    print('   * Systems of {} {}'.format(kind, action), file=fp)
    util_print_QA_line(fp, dValue['system'])

    print(file=fp)
    print('   * Platforms of {} {}'.format(kind, action), file=fp)
    util_print_QA_line(fp, dValue['platform'])

    print(file=fp)
    print('   * statuses of {} {}'.format(kind, action), file=fp)
    util_print_QA_line(fp, dValue['status'])

    print(file=fp)
    print('   * Products of {} {}'.format(kind, action), file=fp)
    util_print_QA_line(fp, dValue['product'])

    print(file=fp)
    print('   * Resolution of {} {}'.format(kind, action), file=fp)
    util_print_QA_line(fp, dValue['resolution'])
    print(file=fp)

    if 'difftime' in dValue and dValue['difftime']:
        sortList = sorted(dValue['difftime'])
        rangeList = sortList[-1] - sortList[0]
        subLists = {}
        for i in sortList:
            timePeriod = ''
            if i < 1:
                timePeriod = '1. 1 day'
            elif i < 7:
                timePeriod = '2. 7 days'
            elif i < 30:
                timePeriod = '3. 1 month'
            elif i < 90:
                timePeriod = '4. 3 months'
            elif i < 180:
                timePeriod = '5. 6 months'
            elif i < 365:
                timePeriod = '6. 1 year'
            elif i < 1095:
                timePeriod = '7. 3 years'
            else:
                timePeriod = '8. Older'
            if timePeriod not in subLists:
                subLists[timePeriod] = []
            subLists[timePeriod].append(i)

        print('  * Times: ', file=fp)
        for k,v in sorted(subLists.items()):
            print(str(k) + ' : ' + str(len(v)), file=fp)
    fp.close()

def util_print_QA_line(fp, dValue ):
    s = [(k, dValue[k]) for k in sorted(dValue, key=dValue.get, reverse=True)]
    for k, v in s:
        if v > 0:
            print('{}: {}'.format(k, v), file=fp)

def data_Report(statList) :
    for kind in kindOfData:
        for k,v in statList[kind].items():
            if k == 'keywords':
                for kKey, vKey in v.items():
                    util_print_QA_line_data(statList, vKey, kind, kKey, 10)
            else:
                util_print_QA_line_data(statList, v, kind, k, 10)

def runCfg():
    cfg = {}
    cfg['reportPeriod'] = common.util_convert_days_to_datetime(cfg, reportPeriodDays)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla_data(statList, bugzillaData, cfg)

    data_Report(statList)

    print('End of report')
