#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common
from datetime import datetime, timedelta
import argparse
import math

import matplotlib
import matplotlib.pyplot as plt

lKeywords = ['havebacktrace', 'regression', 'bisected']

oldBugsYears = 4

def util_create_basic_schema():
    return {
        'id': [],
        'author': {},
        'day': {},
        'difftime': []
        }

def util_create_statList():
    return {
        'created': util_create_basic_schema(),
        'confirmed': util_create_basic_schema(),
        'verified': util_create_basic_schema(),
        'fixed': util_create_basic_schema(),
        'criticalFixed': {},
        'crashFixed': {},
        'oldBugsFixed': {},
        'metabug': util_create_basic_schema(),
        'keywords': { k : util_create_basic_schema() for k in lKeywords},
        'people' : {},
        'unconfirmedCount' : {},
        'regressionCount' : {},
        'bibisectRequestCount' : {},
        'highestCount' : {},
        'highCount' : {},
        'stat': {'oldest': datetime.now(), 'newest': datetime(2001, 1, 1)}
    }

def util_increase_action(value, rowId, creatorMail, day, difftime=-1):
    value['id'].append(rowId)
    if creatorMail not in value['author']:
        value['author'][creatorMail] = 0
    value['author'][creatorMail] += 1

    if day not in value['day']:
        value['day'][day] = 0
    value['day'][day] += 1

    if difftime >= 0:
        value['difftime'].append(difftime)

def util_decrease_action(value, creatorMail, day):
    value['id'].pop()
    value['author'][creatorMail] -= 1
    value['day'][day] -= 1

    if value['difftime']:
        value['difftime'].pop()

def check_date(xDate, cfg):
    if xDate >= cfg.Date[0] and xDate < cfg.Date[1]:
        return True
    else:
        return False

def daterange(cfg):
    for n in range(int ((cfg.Date[1] - cfg.Date[0]).days)):
        yield cfg.Date[0] + timedelta(n)

def analyze_bugzilla_data(statList, bugzillaData, cfg):
    print("Analyzing bugzilla\n", end="", flush=True)


    unconfirmedCountPerDay = {}
    regressionsCountPerDay = {}
    bibisectRequestCountPerDay = {}
    highestCountPerDay = {}
    highCountPerDay = {}
    fixedBugs = {}

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'].lower() != 'deletionrequest':
            creationDate = datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")


            #Some old bugs were directly created as NEW, skipping the UNCONFIRMED status
            #Use the oldest bug ID in the unconfirmed list
            if rowId >= 89589:
                strDay = creationDate.strftime("%Y-%m-%d")
                if strDay not in unconfirmedCountPerDay:
                    unconfirmedCountPerDay[strDay] = 0
                unconfirmedCountPerDay[strDay] += 1

            rowStatus = row['status']
            rowResolution = row['resolution']

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            #get information about created bugs in the period of time
            if check_date(creationDate, cfg):
                creationDay = str(creationDate.strftime("%Y-%m-%d"))
                util_increase_action(statList['created'], rowId, creatorMail, creationDay)

            common.util_check_bugzilla_mail(
                    statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            isFixed = False
            isConfirmed = False
            isVerified = False
            dayConfirmed = None
            dayVerified = None
            authorConfirmed = None
            authorVerified = None
            isRegression = False
            isRegressionClosed = False
            isBibisectRequest = False
            isBibisectRequestClosed = False
            isHighest = False
            isHighestClosed = False
            isHigh = False
            isHighClosed = False
            isThisBugClosed = False

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(
                        statList, actionMail, '', actionDate, rowId)

                actionDay = str(actionDate.strftime("%Y-%m-%d"))
                diffTime = (actionDate - creationDate).days

                for change in action['changes']:
                        if change['field_name'] == 'priority':
                            addedPriority = change['added']
                            removedPriority = change['removed']

                            # Sometimes the priority is increased to highest after the bug is fixed
                            # Ignore those cases
                            if not isThisBugClosed and not isHighestClosed:
                                if not isHighest and addedPriority == "highest":
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highestCountPerDay:
                                        highestCountPerDay[strDay] = 0
                                    highestCountPerDay[strDay] += 1
                                    isHighest = True

                                if isHighest and removedPriority == "highest":
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highestCountPerDay:
                                        highestCountPerDay[strDay] = 0
                                    highestCountPerDay[strDay] -= 1
                                    isHighest = False

                            # TODO: IsThisBugClosed should be check here, but the result is not accurate
                            if not isHighClosed:
                                if not isHigh and addedPriority == "high":
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highCountPerDay:
                                        highCountPerDay[strDay] = 0
                                    highCountPerDay[strDay] += 1
                                    isHigh = True

                                if isHigh and removedPriority == "high":
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highCountPerDay:
                                        highCountPerDay[strDay] = 0
                                    highCountPerDay[strDay] -= 1
                                    isHigh = False

                        if change['field_name'] == 'status':
                            addedStatus = change['added']
                            removedStatus = change['removed']

                            if common.isOpen(addedStatus):
                                isThisBugClosed = False
                            else:
                                isThisBugClosed = True

                            #See above
                            if rowId >= 89589:
                                if removedStatus == "UNCONFIRMED":
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in unconfirmedCountPerDay:
                                        unconfirmedCountPerDay[strDay] = 0
                                    unconfirmedCountPerDay[strDay] -= 1

                                elif addedStatus == 'UNCONFIRMED':
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in unconfirmedCountPerDay:
                                        unconfirmedCountPerDay[strDay] = 0
                                    unconfirmedCountPerDay[strDay] += 1

                            if isRegression:
                                # the regression is being reopened
                                if isRegressionClosed and not isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in regressionsCountPerDay:
                                        regressionsCountPerDay[strDay] = 0
                                    regressionsCountPerDay[strDay] += 1
                                    isRegressionClosed = False

                                # the regression is being closed
                                if not isRegressionClosed and isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in regressionsCountPerDay:
                                        regressionsCountPerDay[strDay] = 0
                                    regressionsCountPerDay[strDay] -= 1
                                    isRegressionClosed = True

                            if isBibisectRequest:
                                # the bibisectRequest is being reopened
                                if isBibisectRequestClosed and not isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in bibisectRequestCountPerDay:
                                        bibisectRequestCountPerDay[strDay] = 0
                                    bibisectRequestCountPerDay[strDay] += 1
                                    isBibisectRequestClosed = False

                                # the bibisectRequest is being closed
                                if not isBibisectRequestClosed and isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in bibisectRequestCountPerDay:
                                        bibisectRequestCountPerDay[strDay] = 0
                                    bibisectRequestCountPerDay[strDay] -= 1
                                    isBibisectRequestClosed = True

                            if isHighest:
                                # the Highest priority bug is being reopened
                                if isHighestClosed and not isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highestCountPerDay:
                                        highestCountPerDay[strDay] = 0
                                    highestCountPerDay[strDay] += 1
                                    isHighestClosed = False

                                # the Highest priority bug is being closed
                                if not isHighestClosed and isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highestCountPerDay:
                                        highestCountPerDay[strDay] = 0
                                    highestCountPerDay[strDay] -= 1
                                    isHighestClosed = True

                            if isHigh:
                                # the High priority bug is being reopened
                                if isHighClosed and not isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highCountPerDay:
                                        highCountPerDay[strDay] = 0
                                    highCountPerDay[strDay] += 1
                                    isHighClosed = False

                                # the High priority bug is being closed
                                if not isHighClosed and isThisBugClosed:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in highCountPerDay:
                                        highCountPerDay[strDay] = 0
                                    highCountPerDay[strDay] -= 1
                                    isHighClosed = True

                            if check_date(actionDate, cfg):
                                if removedStatus == "UNCONFIRMED":
                                    util_increase_action(statList['confirmed'], rowId, actionMail, actionDay, diffTime)
                                    dayConfirmed = actionDay
                                    authorConfirmed = actionMail
                                    isConfirmed = True

                                elif addedStatus == 'UNCONFIRMED' and isConfirmed:
                                    util_decrease_action(statList['confirmed'], authorConfirmed, dayConfirmed)
                                    isConfirmed = False

                                if addedStatus == 'VERIFIED':
                                    util_increase_action(statList['verified'], rowId, actionMail, actionDay, diffTime)
                                    dayVerified = actionDay
                                    authorVerified = actionMail
                                    isVerified = True

                                elif removedStatus == 'VERIFIED' and isVerified and common.isOpen(addedStatus):
                                    util_decrease_action(statList['verified'], authorVerified, dayVerified)
                                    isVerified = False

                        elif change['field_name'] == 'resolution':
                            if check_date(actionDate, cfg):
                                addedResolution = change['added']
                                removedResolution = change['removed']
                                if addedResolution == 'FIXED':
                                    fixedBugs[rowId] = actionDate
                                    isFixed = True

                                elif removedResolution == 'FIXED' and isFixed:
                                    del fixedBugs[rowId]
                                    isFixed = False

                        elif change['field_name'] == 'keywords':
                            keywordsAdded = change['added'].lower().split(", ")
                            keywordsRemoved = change['removed'].lower().split(", ")

                            if check_date(actionDate, cfg):
                                for keyword in keywordsAdded:
                                    if keyword in lKeywords:
                                        util_increase_action(statList['keywords'][keyword], rowId, actionMail, actionDay, diffTime)

                            # TODO: IsThisBugClosed should be check here, but the result is not accurate
                            if not isRegressionClosed:
                                if not isRegression and 'regression' in keywordsAdded:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in regressionsCountPerDay:
                                        regressionsCountPerDay[strDay] = 0
                                    regressionsCountPerDay[strDay] += 1
                                    isRegression = True

                                if isRegression and 'regression' in keywordsRemoved:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in regressionsCountPerDay:
                                        regressionsCountPerDay[strDay] = 0
                                    regressionsCountPerDay[strDay] -= 1
                                    isRegression = False

                            # In the past, 'bibisectRequest' was added after the bug got fixed
                            # to find the commit fixing it. Ignore them
                            if not isThisBugClosed and not isBibisectRequestClosed:
                                if not isBibisectRequest and 'bibisectrequest' in keywordsAdded:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in bibisectRequestCountPerDay:
                                        bibisectRequestCountPerDay[strDay] = 0
                                    bibisectRequestCountPerDay[strDay] += 1
                                    isBibisectRequest = True

                                if isBibisectRequest and 'bibisectrequest' in keywordsRemoved:
                                    strDay = actionDate.strftime("%Y-%m-%d")
                                    if strDay not in bibisectRequestCountPerDay:
                                        bibisectRequestCountPerDay[strDay] = 0
                                    bibisectRequestCountPerDay[strDay] -= 1
                                    isBibisectRequest = False

                        elif change['field_name'] == 'blocks':
                            if check_date(actionDate, cfg):
                                if change['added']:
                                    for metabug in change['added'].split(', '):
                                        if int(metabug) in row['blocks']:
                                            util_increase_action(statList['metabug'], rowId, actionMail, actionDay, diffTime)

            commentMail = None
            comments = row['comments'][1:]
            bugFixers = []
            commitNoticiation=False
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(
                        statList, commentMail, '', commentDate, rowId)

                if rowId in fixedBugs:
                    if commentMail == "libreoffice-commits@lists.freedesktop.org":
                        commentText = comment['text']
                        author =  commentText.split(' committed a patch related')[0]
                        if author not in bugFixers and 'uitest' not in commentText.lower():
                            bugFixers.append(author)
                            diffTime = (commentDate - creationDate).days
                            commentDay = commentDate.strftime("%Y-%m-%d")
                            util_increase_action(statList['fixed'], rowId, author, commentDay, diffTime)
                            commitNoticiation=True
                            if row['priority'] == "highest":
                                statList['criticalFixed'][rowId]= {'summary': row['summary'], 'author': author}
                            elif 'crash' in row['summary'].lower():
                                statList['crashFixed'][rowId]= {'summary': row['summary'], 'author': author}
                            elif creationDate < common.util_convert_days_to_datetime(oldBugsYears * 365):
                                statList['oldBugsFixed'][rowId]= {'summary': row['summary'], 'author': author}

            if rowId in fixedBugs and not commitNoticiation:
                actionDate = fixedBugs[rowId]
                actionDay = actionDate.strftime("%Y-%m-%d")
                diffTime = (actionDate - creationDate).days
                util_increase_action(statList['fixed'], rowId, 'UNKNOWN', actionDay, diffTime)

            for person in row['cc_detail']:
                email = person['email']
                if commentMail == email or actionMail == email:
                    common.util_check_bugzilla_mail(statList, email, person['real_name'])

    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")

    for single_date in daterange(cfg):
        single_day = single_date.strftime("%Y-%m-%d")

        #Fill empty days to be displayed on the charts
        for k0, v0 in statList.items():
            if k0 == 'keywords':
                for k1, v1 in statList['keywords'].items():
                    if single_day not in statList['keywords'][k1]['day']:
                        statList['keywords'][k1]['day'][single_day] = 0
            else:
                if 'day' in statList[k0]:
                    if single_day not in statList[k0]['day']:
                        statList[k0]['day'][single_day] = 0

        totalCount1 = 0
        for k, v in unconfirmedCountPerDay.items():
            xDay = datetime.strptime( k, "%Y-%m-%d")
            if xDay < single_date:
                totalCount1 += v

        statList['unconfirmedCount'][single_day] = totalCount1

        totalCount2 = 0
        for k, v in regressionsCountPerDay.items():
            xDay = datetime.strptime( k, "%Y-%m-%d")
            if xDay < single_date:
                totalCount2 += v

        statList['regressionCount'][single_day] = totalCount2

        totalCount3 = 0
        for k, v in highestCountPerDay.items():
            xDay = datetime.strptime( k, "%Y-%m-%d")
            if xDay < single_date:
                totalCount3 += v

        statList['highestCount'][single_day] = totalCount3

        totalCount4 = 0
        for k, v in highCountPerDay.items():
            xDay = datetime.strptime( k, "%Y-%m-%d")
            if xDay < single_date:
                totalCount4 += v

        statList['highCount'][single_day] = totalCount4

        totalCount5 = 0
        for k, v in bibisectRequestCountPerDay.items():
            xDay = datetime.strptime( k, "%Y-%m-%d")
            if xDay < single_date:
                totalCount5 += v

        statList['bibisectRequestCount'][single_day] = totalCount5

def makeStrong(text):
    return "<strong>" + str(text) + "</strong>"

def makeLI(text):
    return "<li>" + str(text) + "</li>"

def makeH2(text):
    return "<h2>" + str(text) + "</h2>"

def makeLink(url, text):
    return '<a href="' + url + '">' + text + '</a>'

def createPlot(valueDict, plotType, plotTitle, plotLabel, plotColor):

    x, y = zip(*sorted(valueDict.items(), key = lambda x:datetime.strptime(x[0], '%Y-%m-%d')))
    if plotType == "line":
        plt.plot(y, label=plotLabel, linewidth=2, color=plotColor)
    elif plotType == "bar":
        plt.bar(range(len(y)), y, label=plotLabel, width=0.8, color=plotColor)

    plt.xticks(range(len(x)), x, rotation=90)
    plt.title(plotTitle)
    plt.xlabel("Date")
    plt.ylabel("Number");
    plt.legend();
    ax = plt.gca()
    ax.grid(axis="y", linestyle='--')
    #Remove labels depending on number of elements
    total = math.ceil( len(ax.get_xticklabels()) / 20 )
    for idx, val in enumerate(ax.get_xticklabels()):
        #Hide all tick labels by default, otherwise it doesn't work
        val.set_visible(False)
        if idx % total == 0:
            val.set_visible(True)

    #plt.show()
    filePath = "/tmp/" + plotLabel.replace(" ", "_") + ".png"
    print("Saving plot " + plotLabel + " to " + filePath)
    plt.savefig(filePath)
    plt.gcf().clear()

def createSection(fp, value, sectionName, action, actionPerson, plotColor):
    print(makeH2(sectionName), file=fp)
    print("{} bugs have been {} by {} people.".format(
        makeStrong(len(value["id"])), action,
        makeStrong(len(value["author"]))), file=fp)

    print(file=fp)
    print(makeStrong("Top 10 " + actionPerson), file=fp)
    print('<a href="PATH_HERE/' + sectionName.replace(' ', '_') + \
            '.png" rel="noopener"><img class="alignright" src="PATH_HERE/' + sectionName.replace(' ', '_') + \
            '.png" alt="" width="300" height="225" /></a>', file=fp)
    print("<ol>", file=fp)
    sortedList = sorted(value["author"].items(), key=lambda x: x[1], reverse=True)
    itCount = 1
    for item in sortedList:
        if itCount > 10:
            break
        if action == 'fixed':
            if item[0] == 'UNKNOWN':
                continue
            print(makeLI("{} ( {} )".format(item[0], item[1])), file=fp)
        else:
            print(makeLI("{} ( {} )".format(statList['people'][item[0]]['name'], item[1])), file=fp)
        itCount += 1

    print("</ol>", file=fp)

    while itCount <= 10:
        print("&nbsp;",file=fp)
        itCount += 1

    createPlot(value['day'], "bar", sectionName + " Per Day", sectionName, plotColor)

def createEvolutionSection(fp, value, sectionName, urlParam, color):
    urlPath = "https://bugs.documentfoundation.org/buglist.cgi?"
    print(makeH2("Evolution of {}".format(sectionName)), file=fp)
    print("Check the current list of {} {}".format(sectionName.lower(), makeLink(urlPath + urlParam, "here")), file=fp)
    print('<img src="PATH_HERE/{}.png" alt="" width="640" height="480" class="alignnone size-full" />'.format(
        sectionName.replace(" ", "_")), file=fp)
    createPlot(value, "line", sectionName + " Per Day", sectionName, color)


def createList(fp, value, listName):
    urlPath = "https://bugs.documentfoundation.org/show_bug.cgi?id="
    print(makeStrong(listName), file=fp)
    print("<ol>", file=fp)
    for k, v in value.items():
        print(makeLI("{} {} ( Thanks to {} )".format(makeLink(urlPath + str(k), "tdf#" +  str(k)),
            v['summary'], v['author'])), file=fp)
    print("</ol>", file=fp)
    print(file=fp)

def createReport(statList):
    fileName = '/tmp/blogReport.txt'
    fp = open(fileName, 'w', encoding='utf-8')
    print("creating Blog Report in " + fileName)
    createSection(fp, statList['created'], "Reported Bugs", "reported", "Reporters", "red")
    createSection(fp, statList['confirmed'], "Triaged Bugs", "triaged", "Triagers", "gold")
    createSection(fp, statList['fixed'], "Fixed Bugs", "fixed", "Fixers", "darksalmon")
    createList(fp, statList['criticalFixed'], "List of critical bugs fixed")
    createList(fp, statList['crashFixed'], "List of crashes fixed")
    createList(fp, statList['oldBugsFixed'], "List of old bugs ( more than {} years old ) fixed".format(oldBugsYears))
    createSection(fp, statList['verified'], "Verified bug fixes", "verified", "Verifiers", "palegreen")
    createSection(fp, statList['metabug'], "Categorized Bugs", "categorized with a metabug", "Categorizers", "lightpink")
    createSection(fp, statList['keywords']['regression'], "Regression Bugs", "set as regressions", "", "mediumpurple")
    createSection(fp, statList['keywords']['bisected'], "Bisected Bugs", "bisected", "Bisecters", "orange")

    createEvolutionSection(
        fp, statList['unconfirmedCount'], "Unconfirmed Bugs",
        "bug_status=UNCONFIRMED&query_format=advanced&resolution=---", "blue")
    createEvolutionSection(
        fp, statList['regressionCount'], "Open Regressions",
        "bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&keywords=regression%2C &keywords_type=allwords&query_format=advanced&resolution=---", "green")
    createEvolutionSection(
        fp, statList['bibisectRequestCount'], "Open bibisectRequests",
        "bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&keywords=bibisectRequest%2C &keywords_type=allwords&query_format=advanced&resolution=---", "lightpink")
    createEvolutionSection(
        fp, statList['highestCount'], "Highest Priority Bugs",
        "bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&priority=highest&query_format=advanced&resolution=---", "sandybrown")
    createEvolutionSection(
        fp, statList['highCount'], "High Priority Bugs",
        "bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&priority=high&query_format=advanced&resolution=---", "indianred")

    print(makeStrong('Thank you all for making Libreoffice rock!'), file=fp)
    print(makeStrong('Join us and help to keep LibreOffice super reliable!'), file=fp)
    print(makeStrong('Check <a href="https://wiki.documentfoundation.org/QA/GetInvolved">the Get Involved page</a> out now!'), file=fp)
    fp.close()

def mkdate(datestr):
      try:
        return datetime.strptime(datestr, '%Y-%m-%d')
      except ValueError:
        raise argparse.ArgumentTypeError(datestr + ' is not a proper date string')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('Date',type=mkdate, nargs=2, help="Introduce the starting date as first" + \
            " argument and the ending date as second argument. FORMAT: YYYY-MM-DD")
    args=parser.parse_args()

    if args.Date[0] >= args.Date[1]:
        print('Argument 1 must be older than argument 2... Closing!!')
        exit()

    print("Reading and writing data from " + common.dataDir)

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla_data(statList, bugzillaData, args)

    createReport(statList)

    print('End of report')
