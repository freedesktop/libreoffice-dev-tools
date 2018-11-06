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

import matplotlib
import matplotlib.pyplot as plt

lKeywords = ['haveBacktrace', 'regression', 'bisected']


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
        'metabug': util_create_basic_schema(),
        'keywords': { k : util_create_basic_schema() for k in lKeywords},
        'people' : {},
        'unconfirmedCount' : {},
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
    fixedBugs = []
    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'] != 'deletionrequest':
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
            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(
                        statList, actionMail, '', actionDate, rowId)

                actionDay = str(actionDate.strftime("%Y-%m-%d"))
                diffTime = (actionDate - creationDate).days

                for change in action['changes']:

                        if change['field_name'] == 'status':
                            addedStatus = change['added']
                            removedStatus = change['removed']

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
                                if addedResolution == 'FIXED' and not removedResolution:
                                    fixedBugs.append(rowId)
                                    isFixed = True

                                elif removedResolution == 'FIXED' and isFixed and not addedResolution:
                                    fixedBugs.pop()
                                    isFixed = False

                        elif change['field_name'] == 'keywords':
                            if check_date(actionDate, cfg):
                                keywordsAdded = change['added'].split(", ")
                                for keyword in keywordsAdded:
                                    if keyword in lKeywords:
                                        if keyword in rowKeywords:
                                            util_increase_action(statList['keywords'][keyword], rowId, actionMail, actionDay, diffTime)

                        elif change['field_name'] == 'blocks':
                            if check_date(actionDate, cfg):
                                if change['added']:
                                    for metabug in change['added'].split(', '):
                                        if int(metabug) in row['blocks']:
                                            util_increase_action(statList['metabug'], rowId, actionMail, actionDay, diffTime)

            commentMail = None
            comments = row['comments'][1:]
            bugFixers = set()
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(
                        statList, commentMail, '', commentDate, rowId)

                if check_date(commentDate, cfg) and rowId in fixedBugs:
                    if commentMail == "libreoffice-commits@lists.freedesktop.org":
                        commentText = comment['text']
                        author =  commentText.split(' committed a patch related')[0]
                        if author not in bugFixers:
                            bugFixers.add(author)
                            diffTime = (commentDate - creationDate).days
                            commentDay = commentDate.strftime("%Y-%m-%d")
                            util_increase_action(statList['fixed'], rowId, author, commentDay, diffTime)
                            if 'crash' in row['summary'].lower() or row['priority'] == "highest":
                                statList['criticalFixed'][rowId]= {'summary': row['summary'], 'author': author}


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

        totalCount = 0
        for k, v in unconfirmedCountPerDay.items():
            xDay = datetime.strptime( k, "%Y-%m-%d")
            if xDay < single_date:
                totalCount += v

        statList['unconfirmedCount'][single_day] = totalCount

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
    #Remove even labels
    for count, i in enumerate(ax.get_xticklabels()):
        if count % 2 == 1:
            i.set_visible(False)
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
    print("<ol>", file=fp)
    sortedList = sorted(value["author"].items(), key=lambda x: x[1], reverse=True)
    itCount = 1
    for item in sortedList:
        if itCount > 10:
            break
        if action == 'fixed':
            print(makeLI("{} ( {} )".format(item[0], item[1])), file=fp)
        else:
            print(makeLI("{} ( {} )".format(statList['people'][item[0]]['name'], item[1])), file=fp)
        itCount += 1
    print("</ol>", file=fp)
    print(file=fp)
    print('<img src="PATH_HERE/' + sectionName.replace(' ', '_') + \
            '.png" alt="" width="640" height="480" class="alignnone size-full" />', file=fp)
    print(file=fp)

    createPlot(value['day'], "bar", sectionName + " Per Day", sectionName, plotColor)

def createList(fp, value, listName):
    urlPath = "https://bugs.documentfoundation.org/show_bug.cgi?id="
    print(makeStrong(listName), file=fp)
    print("<ol>", file=fp)
    for k, v in value.items():
        print(makeLI("{} {} ( Thanks to {} )".format(makeLink(urlPath + str(k), str(k)), v['summary'], v['author'])), file=fp)
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
    createSection(fp, statList['verified'], "Verified Bugs", "verified", "Verifiers", "palegreen")
    createSection(fp, statList['metabug'], "Categorized Bugs", "categorized with a metabug", "Categorizers", "lightpink")
    createSection(fp, statList['keywords']['bisected'], "Bisected Bugs", "bisected", "Bisecters", "orange")

    print(makeH2("Evolution of Unconfirmed Bugs"), file=fp)
    print(file=fp)
    print('<img src="PATH_HERE/Unconfirmed_Bugs.png" alt="" width="640" height="480" class="alignnone size-full" />', file=fp)
    print(file=fp)
    createPlot(statList['unconfirmedCount'], "line", "Unconfirmed Bugs Per Day", "Unconfirmed Bugs", "blue")

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
