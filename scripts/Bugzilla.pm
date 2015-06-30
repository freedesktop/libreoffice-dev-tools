package Bugzilla;

use strict;
use warnings;
use URI::Escape qw(uri_escape);

our ($bugserver);
our @EXPORT_OK = qw(bugserver get_url get_deps get_query read_bugstats);

# Please take the time to check that the script still runs
# before changing this to something else.
$bugserver = "bugs.documentfoundation.org";

# use me for testing XML pretty printing etc.
my $fast_debug = 0;

sub get_url($)
{
    my $url = shift;
    my @lines;
    my $handle;
    open ($handle, "curl -A 'Mozilla/4.0' -k -s '$url' 2>&1 |") || die "can't exec curl: $!";
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

    my $debug = 0;

    my $region = 'header';
    my $closer_name;
    my %closed_stats;
    my $delta = 0;

    while ((my $line = shift @lines) && $region ne 'end') {
	print STDERR "$region -> $line\n" if ($debug);
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

	} elsif (($region eq 'top-closers' || $region eq 'top-closer-name') &&
		 ($line =~ m/<\/table>/ || $line =~ m/Top .* bug reporters/)) {
	    $region = 'end';

	} elsif ($region eq 'top-closer-name' && $line =~ m/<span class=".*">(.*)<\/span>/) {
	    $closer_name = $1;
	    print STDERR "$closer_name\n" if ($debug);
	    $region = 'top-closer-count';

	} elsif ($region eq 'top-closer-count' && $line =~ m/">([0-9]+)<\/a><\/td>/) {
	    die "no closer name for '$line'" if (!defined $closer_name);
	    $closed_stats{$closer_name} = $1;
	    print STDERR "\tRecord: $closer_name -> $1\n" if ($debug);
	    $region = 'top-closers'
	}
    }

    $region eq 'end' || die "Failed to parse weekly bug summary - in region '$region'";

    return \%closed_stats;
}

1;
