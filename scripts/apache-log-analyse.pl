#!/usr/bin/perl -w

use Date::Parse;
use Date::Format;

my %bydate;    # date -> page -> count
my %referrers; # count of referrers by URL

while (<>) {
    my $line = $_;
    my $slice = $line;
# wiki.documentfoundation.org.log:wiki.documentfoundation.org:80 190.69.122.160 - - [16/Oct/2011:08:17:18 +0200] "GET /Development/Easy_Hacks HTTP/1.1" 200 13665 "http://www.libreoffice.org/get-involved/" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.202 Safari/535.1"
    my ($server, $host, $date, $page, $referrer);
    if ($slice =~ s/^[^:]+:([^:]+):\d+\s+([\d\.]+)\s+-\s+-\s+//) {
	$server = $1; $host = $2;

# [11/Oct/2011:06:26:20 +0200] "GET /Development/Easy_Hacks_by_Difficulty/be HTTP/1.1" 404 5516 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
	if ($slice =~ s/^\[\s*([^\]]+)\s*\]\s+//) {
	    $date = $1;

# "GET /Development/Easy_Hacks HTTP/1.1" 200 13663 "-" "Mozilla/5.0 (compatible; ScoutJet; +http://www.scoutjet.com/)
	    if ($slice =~ s/^\"([^"]+)\"\s+\d+\s+\d+\s+//) {
		$page = $1;
# "http://wiki.documentfoundation.org/Development/Easy_Hacks" "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)"
		if ($slice =~ s/^\"([^"]*)\"//) {
		    $referrer = $1;
		    $referrer = '' if ($referrer eq '-');
#		    printf "line remainder $slice\n";
		} else {
		    die "invalid referrer: $slice";
		}
	    } else {
		die "invalid page fetch: $slice";
	    }
	} else {
	    die "invalid date in: $slice";
	}
    }
    else {
	die "invalid host in $slice";
    }

    # cleanup page
    $page =~ s/^GET\s+//;
    $page =~ s/s*HTTP\s*$//;
    $page =~ s/\s*HTTP\/[\d\.]*$//;

    # Mangle date into year-month
    my ($year, $month, $day);
    if ($date =~ m/([^\/]+)\/([^\/]+)\/([^\:]+):/) {
	$day = $1; $month = $2; $year = $3;
    } else {
	die "invalid date '$date'";
    }

    $referrers{$referrer} = 0 if (!defined $referrers{$referrer});
    $referrers{$referrer} += 1;

    $monthkey = "$month $year";
#    print "Date '$date' -> '$monthkey'\n";
    $bydate{$monthkey} = 0 if (!defined $bydate{$monthkey});
    $bydate{$monthkey} += 1;
}

for my $date (keys %bydate) {
    print "$date\t" . $bydate{$date} . "\n";
}

for my $ref (sort { $referrers{$b} <=> $referrers{$a} } keys %referrers) {
    print "$ref\t" . $referrers{$ref} . "\n";
}
