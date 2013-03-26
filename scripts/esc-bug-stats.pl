#!/usr/bin/perl -w

sub get_url($)
{
    my $url = shift;
    my @lines;
    my $handle;
    open ($handle, "curl -s '$url' 2>&1 |") || die "can't exec curl: $!";
    while (<$handle>) {
	push @lines, $_;
    }
    close ($handle);
    return @lines;
}

sub get_deps($)
{
    my ($url) = @_;
    my @bugs = get_url($url);

    my $bug_count = -1;
    while (my $line = shift (@bugs)) {
	if ($line =~ m/^\s*depends on\s*$/) {
	    $line = shift @bugs;
#	    print STDERR "Have depends on\n";
	    if ($line =~ m/^\s*(\d+)\s*$/) {
		my $num = $1;
		$line = shift @bugs;
		$line = shift @bugs;
		if ($line =~ m/bugs:/) {
		    $bug_count = $num;
		    last;
		}
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
    my @bugs = get_url($url);

    my $bug_count = -1;
    while (my $line = shift (@bugs)) {
	if ($line =~ m/<span class="bz_result_count">(\d+) bugs found./) {
	    $bug_count = $1;
	    last;
	}
    }
    return $bug_count;
}

my %bug_to_ver = (
    '4.1' => '60270',
    '4.0' => '54157',
    '3.6' => '44446'
);

print "Querying for open MABs:\n";
for my $ver (sort keys %bug_to_ver) {
    my $bug = $bug_to_ver{$ver};
    my $base_url = "https://bugs.freedesktop.org/showdependencytree.cgi?id=" . $bug;
    my $all = get_deps($base_url);
    my $open = get_deps($base_url . "&hide_resolved=1");
    $percent = ($open * 100.0) / $all;
    print "$ver: $open/$all - $percent%\n";
}

my ($all, $open);

print "Querying for regressions:\n";
my $regression_query="https://bugs.freedesktop.org/buglist.cgi?columnlist=bug_severity%2Cpriority%2Ccomponent%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc&keywords=regression%2C%20&keywords_type=allwords&list_id=267671&product=LibreOffice&query_format=advanced&order=bug_id&limit=0";
my $regression_open_query="https://bugs.freedesktop.org/buglist.cgi?keywords=regression%2C%20&keywords_type=allwords&list_id=267687&columnlist=bug_severity%2Cpriority%2Ccomponent%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc&resolution=---&query_based_on=Regressions&query_format=advanced&product=LibreOffice&known_name=Regressions&limit=0";
$all = get_query($regression_query);
$open = get_query($regression_open_query);
print "$open/$all\n";

print "Querying for bibisection:\n";
my $bibisect_query = "https://bugs.freedesktop.org/buglist.cgi?n2=1&f1=status_whiteboard&list_id=267679&o1=substring&resolution=---&resolution=FIXED&resolution=INVALID&resolution=WONTFIX&resolution=DUPLICATE&resolution=WORKSFORME&resolution=MOVED&resolution=NOTABUG&resolution=NOTOURBUG&query_based_on=BibisectedAll&o2=substring&query_format=advanced&f2=status_whiteboard&v1=bibisected&v2=bibisected35older&product=LibreOffice&known_name=BibisectedAll&limit=0";
my $bibisect_open_query = "https://bugs.freedesktop.org/buglist.cgi?n2=1&f1=status_whiteboard&list_id=267685&o1=substring&resolution=---&query_based_on=Bibisected&o2=substring&query_format=advanced&f2=status_whiteboard&v1=bibisected&v2=bibisected35older&product=LibreOffice&known_name=Bibisected&limit=0";

$all = get_query($bibisect_query);
$open = get_query($bibisect_open_query);
print "$open/$all\n";


