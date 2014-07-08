package Bugzilla;

use strict;
use warnings;
use URI::Escape qw(uri_escape);

our ($bugserver);
our @EXPORT_OK = qw(bugserver get_url get_deps get_query read_bugstats);

# Please take the time to check that the script still runs
# before changing this to something else.
$bugserver = "bugs.freedesktop.org";

# use me for testing XML pretty printing etc.
my $fast_debug = 0;

# config for eliding top bug contributors who are
# not (yet) libreoffice hackers.
my %sadly_non_libreoffice = (
    'Chris Wilson' => 1,
    'Bastien Nocera' => 1,
    'Kristian Høgsberg' => 1,
    'Simon McVittie' => 1,
    'Søren Sandmann Pedersen' => 1,
    'Daniel Vetter' => 1,
    'Sergey V. Udaltsov' => 1,
    'Marek Olšák' => 1,
    'Emil Velikov' => 1,
    'ajax at nwnk dot net' => 1,
    'Jesse Barnes' => 1,
    'Albert Astals Cid' => 1,
    'Daniel Stone' => 1,
    'Eric Anholt' => 1,
    'Lennart Poettering' => 1,
    'Ilia Mirkin' => 1,
    'Behdad Esfahbod' => 1,
    'Richard Hughes' => 1,
    'Ben Widawsky' => 1,
    'Chengwei Yang' => 1,
    'Dan Nicholson' => 1,
    'Zbigniew Jedrzejewski-Szmek' => 1,
    'Tanu Kaskinen' => 1,
    'Vinson Lee' => 1,
    'Sylvain BERTRAND' => 1,
    'lu hua' => 1,
    'Kenneth Graunke' => 1,
    'Seif Lotfy' => 1,
    'Alex Deucher' => 1,
    'Ian Romanick' => 1,
    'Tollef Fog Heen' => 1,
    'Patrick Ohly' => 1,
    'Peter Hutterer' => 1,
    'Guillaume Desmottes' => 1,
    'Bryce Harrington' => 1,
    'Paolo Zanoni' => 1,
    'David Faure' => 1,
    'Rex Dieter' => 1,
    'Tom Stellard' => 1,
    'almos' => 1,
    'Andreas Boll' => 1,
);

sub get_url($)
{
    my $url = shift;
    my @lines;
    my $handle;
    open ($handle, "curl -k -s '$url' 2>&1 |") || die "can't exec curl: $!";
    while (<$handle>) {
	push @lines, $_;
    }
    close ($handle);
    return @lines;
}

sub get_deps($)
{
    my ($url) = @_;

    return 42 if ($fast_debug);

    my @bugs = get_url($url);

    my $bug_count = -1;
    while (my $line = shift (@bugs)) {
	if ($line =~ m/does not depend on any open bugs/) {
	    $bug_count = 0;
	    last;
	}
	elsif ($line =~ m/^\s*depends on\s*$/) {
	    $line = shift @bugs;
#	    print STDERR "Have depends on '$line'\n";
	    if ($line =~ m/^\s*(\d+)\s*$/) {
		my $num = $1;
		$line = shift @bugs;
		$line = shift @bugs;
		if ($line =~ m/bugs:/) {
		    $bug_count = $num;
		    last;
		}
	    } elsif ($line =~ m/\s+one\s+/) { # special case for one
		$bug_count = 1;
		last;
	    } else {
		print STDERR "odd depends on follow-on: '$line'\n";
	    }
	}
    }
    return $bug_count;
}

sub get_query($)
{
    my ($url) = @_;

    return 6 if ($fast_debug);

    my @bugs = get_url($url);

    my $bug_count = -1;
    while (my $line = shift (@bugs)) {
	if ($line =~ m/<span class="bz_result_count">(\d+) bugs found./) {
	    $bug_count = $1;
	    last;
	} elsif ($line =~ m/One bug found./) {
	    $bug_count = 1;
	    last;
	} elsif ($line =~ m/Zarro Boogs found./) {
	    $bug_count = 0;
	    last;
	}
    }
    return $bug_count;
}

sub extract_number($)
{
    my $line = shift;
    chomp ($line);
    $line =~ s/^.*\"\>//;
    $line =~ s/<.*$//;
    return $line;
}

sub read_bugstats($)
{
    my @lines = get_url(shift);

    my $region = 'header';
    my $closer_name;
    my %closed_stats;
    my $delta = 0;

    while ((my $line = shift @lines) && $region ne 'end') {
#	print STDERR "$region -> $line\n";
	if ($region eq 'header' && $line =~ /<h2>Top .* modules<\/h2>/) {
	    $region = 'top-modules';

	} elsif ($region eq 'top-modules' &&
		 $line =~ /<td>LibreOffice<\/td>/) {
	    my ($total, $opened, $closed);
	    $total = extract_number (shift @lines);
	    $opened = extract_number (shift @lines);
	    $closed = extract_number (shift @lines);
	    my $sign = '', $delta = $opened + $closed;
	    $sign = '+' if ($delta > 0);
	    print STDERR "    $opened    $closed	($sign$delta overall)\n";
	    $region = 'seek-end-top-modules';

	} elsif ($region eq 'seek-end-top-modules' &&
		 $line =~ /<h2>Top .* bug closers<\/h2>/) {
	    $region = 'top-closers';

	} elsif ($region eq 'top-closers' && $line =~ m/<tr class/) {
	    undef $closer_name;
	    $region = 'top-closer-name';

	} elsif ($region eq 'top-closers' && $line =~ m/<\/table>/) {
	    $region = 'end';

	} elsif ($region eq 'top-closer-name' && $line =~ m/<span class=".*">(.*)<\/span>/) {
	    $closer_name = $1;
#	    print "$closer_name\n";
	    $region = 'top-closer-count';

	} elsif ($region eq 'top-closer-count' && $line =~ m/">([0-9]+)<\/a><\/td>/) {
	    die "no closer name for '$line'" if (!defined $closer_name);
	    $closed_stats{$closer_name} = $1;
	    $region = 'top-closers'
	}
    }

    $region eq 'end' || die "Failed to parse weekly bug summary - in region '$region'";

    for my $name (keys %closed_stats) {
	delete $closed_stats{$name} if (defined $sadly_non_libreoffice{$name});
    }

    return \%closed_stats;
}
