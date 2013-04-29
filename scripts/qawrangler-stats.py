#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# qawrangler-stats.py
#
# Returns statistics of most active wranglers and reporters for a given
# month.
#
# For usage information, run:
#   qawrangler-stats.py -h
#

import sys
import re
import datetime
import gzip
import argparse
import csv
from urllib.request import urlopen, URLError
from io import BytesIO
from collections import Counter, OrderedDict

URL = 'http://lists.freedesktop.org/archives/libreoffice-bugs/{}.txt.gz'
ENTITIES = OrderedDict({
    'changers': re.compile(r'^(.+)\schanged:$', re.MULTILINE),
    'reporters': re.compile(r'^\s*Reporter:\s(.+)$', re.MULTILINE),
    'commentators': re.compile(r'^--- Comment #\d+ from (.+) ---$',
        re.MULTILINE),
})

def get_parser():
    """Returns an argparse instance, setting the arguments for the script"""
    parser = argparse.ArgumentParser(
        description='LibreOffice contributor statistics')
    parser.add_argument('-m', '--month', dest='month', type=int,
        default=datetime.date.today().month,
        help='month to generate statistics from (default is current month)')
    parser.add_argument('-y', '--year', dest='year', type=int,
        default=datetime.date.today().year,
        help='year to generate statistics from (default is current year)')
    parser.add_argument('-n', '--num', dest='num', type=int, default=None,
        help='number of top contributors of each category (default is all)')
    parser.add_argument('--csv', dest='csv', action='store_true',
        help='output information in CSV format')

    return parser

def get_fname(date):
    """Returns the `Libreoffice-bugs Archives' file name for a given a @date
    datetime object. Note that only year and month are relevant, day is
    ignored"""
    return '{}-{}'.format(date.year, date.strftime('%B'))

def get_data(url):
    """Fetches and uncompresses the `Libreoffice-bugs Archives' file given its
    @url. The return of the function is the content of the gile as a string"""
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    else:
        with gzip.GzipFile(fileobj=BytesIO(resp.read())) as f:
            return f.read().decode('us-ascii')

def get_entity_values(data, pattern, num):
    """Returns the first @num matches of a @pattern in the @data string. If
    @num is None, all matches are returned"""
    values = re.findall(pattern, data)
    return Counter(values).most_common(num)

def nice_print(values_dict, num_output, date):
    """Prints to stdout the output of the script in a human readable way.
    @values_dict is a dict containing a key for each entity (e.g. wranglers,
    reporters, etc), and as values, a list of tuples containing the name and
    the number of occurrences. An example:

    >>> {
    >>>    'wranglers': [
    >>>        ('Wrangler 1 <wrangler1@his_email.com>', 30),
    >>>            # 30 is the number of times he wrangled
    >>>        ('Wrangler 2 <wrangler2@his_email.com>', 15),
    >>>    ]
    >>> }

    @num_output is the number of top values in each categories are requested
    to be displayed (e.g. number of top wranglers), and @date is a datetime
    object containing the requested year and month"""
    print('=== {} ==='.format(date.strftime('%B %Y')))
    print()
    for name, values in values_dict.items():
        print('--- Top {} {} ---'.format(num_output or '', name))
        print('\n'.join('{0:75}{1:5d}'.format(*v) for v in values))
        print()

def csv_print(values_dict):
    """Print to stdout the output of the script in CSV format. @values_dict
    has the same format as for the `nice_print' function. The CSV file has
    the default format for Python's csv module (comma delimited, strings
    quoted when necessary)"""
    writer = csv.writer(sys.stdout)
    for entity_name, values in values_dict.items():
        for val_name, val_count in values:
            writer.writerow([entity_name, val_name, val_count])

def main(args):
    """Main function of the program.
     * Fetches the file for the requested month and date
     * For each defined entity, gathers each match of its pattern,
        and counts the number of occurrences
     * Prints the retrieved information to stdout in the requested format
    """
    date = datetime.date(args.year, args.month, 1)
    fname = get_fname(date)
    url = URL.format(fname)
    data = get_data(url)
    values = OrderedDict()
    for name, regex in ENTITIES.items():
        values[name] = get_entity_values(data, regex, args.num)

    if args.csv:
        csv_print(values)
    else:
        nice_print(values, args.num, date)

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    main(args)

