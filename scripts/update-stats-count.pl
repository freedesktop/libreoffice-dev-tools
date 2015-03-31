#!/usr/bin/perl -w

#
# A simpler approach
#

use strict;
use POSIX;

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

# A single monster hash by unique IP address of all update requests.
my %unique_ips;
# how many update requests we saw in each iso week
my %count_per_week;
# how many new unique IP addresses we saw in each iso week
my %unique_per_week;
# total update counts by OS.
my %os_breakdown;

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

open LOG, "( bzcat logs/update.libreoffice.org-access_log-*.bz2 ; cat logs/update.libreoffice.org-access_log ) |" or die "Cannot open the log: $!";
while (<LOG>) {
    if ( /^([^ ]+) - - \[([^\/]+)\/([^\/]+)\/([^:]+):([0-9][0-9])[^\]]*\] "[^"]*" [^ ]+ [^ ]+ "[^"]*" "[^(]*\(([^-;]+)[^;]*; ([^;]*);/ ) {
	#print "$1, $2, $3, $4, $5, $6, $7\n";
	my ( $ip, $day, $month, $year, $hour, $version, $os ) =
	    ( $1, $2, $month_to_num{$3}, $4, $5, $6, $7 );

	my $year_week = ymd_to_epoch($year, $month, $day);

	# count of upate pings per iso week
#	$count_per_week{$year_week} = 0 if (!defined $count_per_week{$year_week});
	$count_per_week{$year_week}++;

	# count of new unique IPs
	if (!defined $unique_ips{$ip}) {
#	    $unique_per_week{$year_week} = 0 if (!defined $unique_per_week{$year_week});
	    $unique_ips{$ip} = 1;
	    $unique_per_week{$year_week}++;
	}

	# how many of what OS do we have ?
	$os_breakdown{$os}++;
    }
}
close LOG;

print "Generated on: " . qx(date --rfc-3339=seconds) . "\n";
print "Unique IP addresses (from where LO asked for updates up to now): " . scalar( keys( %unique_ips ) ) . "\n\n";

print "Update pings by ISO week:\n";
foreach my $yw ( sort( keys %count_per_week ) ) {
    print "$yw," . $count_per_week{$yw} . "\n";
}
print "\n\n";

print "New Unique IPs by ISO week:\n";
foreach my $yw ( sort( keys %unique_per_week ) ) {
    print "$yw," . $unique_per_week{$yw} . "\n";
}
print "\n\n";

print "Breakdown by OS:\n";
my $total = 0;
foreach my $os ( sort { $os_breakdown{$b} <=> $os_breakdown{$a} } ( keys %os_breakdown ) ) {
    print "$os," . $os_breakdown{$os} . "\n";
    $total += $os_breakdown{$os};
}
print "\n\n";

print "Total update pings: $total\n";

