#!/usr/bin/perl -w

#
# A script to attempt to determine OS versions from user-agent strings.
#

use strict;
use POSIX;

my %global_date_to_epoch;

sub ymd_to_epoch($$$)
{
    my ($year, $month, $day) = @_;

    my $key = "$year-$month-$day";

    if ( ! defined $global_date_to_epoch{$key} ) {
	# 1970-01-01 is Thursday, add 3 days (259200 seconds), and divide
	my $seconds = POSIX::strftime( "%s", 0, 0, 12, $day, $month - 1, $year - 1900 ); # see the manual

	# remember the ISO week
	my $week = POSIX::strftime( "%G-%V", 0, 0, 12, $day, $month - 1, $year - 1900 ); # see the manual
	$global_date_to_epoch{$key} = $week;
    }
    return $global_date_to_epoch{$key};
}

# de-mangle windows user-agents
my %win_ver_hash = (
    'NT 10.0' => 'Windows 10',
    'NT 9.0' => 'Windows 9',
    'NT 6.3' => 'Windows 8.1',
    'NT 6.2' => 'Windows 8',
    'NT 7.0' => 'Windows 7',
    'NT 6.1' => 'Windows 7',
    'NT 6.0' => 'Windows Vista',
    'NT 5.2' => 'Windows Server 2003',
    'NT 5.1' => 'Windows XP',
    'NT 5.01' => 'Windows 2000 SP1',
    'NT 5.0' => 'Windows 2000',
    'NT 4.0' => 'Windows NT 4.0',
    '98; Win 9x 4.90' => 'Windows ME',
    '98' => 'Windows 98',
    '95' => 'Windows 95',
    'CE' => 'Windows CE',
    );

sub win_real_ver($)
{
    my $vin = shift;
    my $vout = $win_ver_hash{$vin};
    if (!defined $vout) {
	$vout = 'Windows other';
    }
    return $vout;
}

my %month_to_num = (
    'Jan' => '01',
    'Feb' => '02',
    'Mar' => '03',
    'Apr' => '04',
    'May' => '05',
    'Jun' => '06',
    'Jul' => '07',
    'Aug' => '08',
    'Sep' => '09',
    'Oct' => '10',
    'Nov' => '11',
    'Dec' => '12',
);

my %totals;
my %breakdown_by_week;

sub analyze_dir($)
{
    my $dirname = shift;

    open LOG, "( cd $dirname ; bzcat download.documentfoundation.org*access*.bz2 2>/dev/null ) |" or die "Cannot open the logs";
    while (<LOG>) {
	my $line = $_;
	if ( /^([^ ]+) - - \[([^\/]+)\/([^\/]+)\/([^:]+):([0-9][0-9])[^\]]*\] "[^"]*" [^ ]+ [^ ]+ "[^"]*" "(.*)"/ ) {
	    my ( $ip, $day, $month, $year, $hour, $useragent ) =
		( $1, $2, $month_to_num{$3}, $4, $5, $6, );

	    next if ($useragent eq '-' || $useragent eq 'setup');

	    # download tools & skip bots
	    next if ($useragent =~ m|Wget| || $useragent =~ m|chocolatey|);
	    next if ($useragent =~ m|lftp/| || $useragent =~ m|curl/|);
	    next if ($useragent =~ m|FPS-DAV-Client/| || $useragent =~ m|Deluge/|);
	    next if ($useragent =~ m|FPS-GET-Client/| || $useragent =~ m|SoftonicDownloader/|);
	    next if ($useragent =~ m|CCBot/| || $useragent =~ m|AhrefsBot/|);
	    next if ($useragent =~ m|SputnikBot/| || $useragent =~ m|YandexBot/|);
	    next if ($useragent =~ m|MojeekBot/| || $useragent =~ m|Webmon /|);
	    next if ($useragent =~ m|bingbot/| || $useragent =~ m|Baiduspider/|);
	    next if ($useragent =~ m|Yahoo! Slurp| || $useragent =~ m|portscout/|);
	    next if ($useragent =~ m|CRAZYWEBCRAWLER | || $useragent =~ m|FDM |);
	    next if ($useragent =~ m|YisouSpider| || $useragent =~ m|ABCdatos BotLink/|);
	    next if ($useragent =~ m|ia_archiver | || $useragent =~ m|BTWebClient/|);
	    next if ($useragent =~ m|portroach/| || $useragent =~ m|Java/|);
	    next if ($useragent =~ m|Googlebot| || $useragent =~ m|escan |);
	    next if ($useragent =~ m|Python-urllib/| || $useragent =~ m|PycURL/|);
	    next if ($useragent =~ m|fetch | || $useragent =~ m|WWWC/|);
	    next if ($useragent =~ m|Xovibot/| || $useragent =~ m|Dolphin |);
	    next if ($useragent =~ m|Megaindex.ru/| || $useragent =~ m|idmarch  |);
	    next if ($useragent =~ m|coccoc/| || $useragent =~ m|WebMon |);
	    next if ($useragent =~ m|Download Master| || $useragent =~ m|Downloader |);

	    # Misc. foo to reduce noise
	    next if ($useragent =~ /GetRedirect/ || $useragent =~ /setup_\d/ ||
		     $useragent =~ /GetLength/ || $useragent =~ /xbps-src-update-check/);

	    my $year_week = ymd_to_epoch($year, $month, $day);

	    my $key;
	    if ($useragent =~ m/Windows \s*([^;\)]+)\s*[;\)]/) {
#		print "good: Windows: $1\n";
		$key = win_real_ver($1);
	    } elsif ($useragent =~ m/Macintosh;.*Intel Mac OS X\s*([0-9_]+)/) {
		my $short = $1;
		$short =~ s/_[0-9]+$//;
#		print "good: OS/X: $short\n";
		$key = "OSX $short";
	    } elsif ($useragent =~ m/X11; Linux/ ||
		     $useragent =~ m/X11; Ubuntu/ ||
		     $useragent =~ m/Linux; /) {
		$key = "Linux";
#		print "good: linux\n";
	    } elsif ($useragent =~ m|[Bb]ot/|) {
#		print "auto-bot: '$useragent'";
	    } else {
		$key = "other";
#		print "odd: '$useragent'\n";
	    }
	    if (defined $key) {
		$totals{$key}++;
		$breakdown_by_week{$year_week}{$key}++;
	    }
	} else {
	    if ($line =~ m|Wget/| || $line =~ m|CCBot/|) {
#		print STDERR "bot? '$line'";
	    } else {
		print STDERR "bad line: '$line'\n";
	    }
	}
    }
    close LOG;
}

sub scan_dirs($);
sub scan_dirs($)
{
    my $dirname = shift;

    print STDERR "analyzing: $dirname\n";
    analyze_dir($dirname);
    opendir(my $dirh, $dirname) || die "Can't open $dirname: $!";
    my @subdirs;
    while (my $subdir = readdir($dirh)) {
	next if ($subdir =~ m/^\./);
	push @subdirs, $subdir if -d "$dirname/$subdir";
    }
    closedir $dirh;

    for my $subdir (@subdirs) {
	scan_dirs ("$dirname/$subdir");
    }
}

my $toplevel = `pwd`;
chomp($toplevel);
scan_dirs ($toplevel);

my @os_list = sort keys %totals;

print "Generated on: " . qx(date --rfc-3339=seconds) . "\n";

print "Totals:\n";
for my $os (@os_list) {
    print "$os\t".$totals{$os}."\n";
}

print "By week:\n";

print "year/week\t";
for my $os (@os_list) {
    print "$os\t";
}
print "\n";

for my $week (sort keys %breakdown_by_week) {
    print "$week\t";
    for my $os (@os_list) {
	if (defined $breakdown_by_week{$week}{$os}) {
	    print $breakdown_by_week{$week}{$os}."\t";
	} else {
	    print "0\t";
	}
    }
    print "\n";
}
