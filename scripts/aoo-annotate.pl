#!/usr/bin/perl -w

use strict;

sub clean_note($)
{
    my $note = shift;
    chomp ($note); # ideally sanitise to pull out our notes ...
    $note =~ m/\n/ && die "multi-line note\n";
    return $note;
}

sub read_log($)
{
    my $git_dir = shift;
    my @revisions;
    my $outputh;

#    print STDERR "read revisions:\n";
    open ($outputh, "cd $git_dir ; git --no-pager log --pretty='%H,%cn,%ce,%cd,>>%s<<>>%N<<' aoo/approx-3.4.0..origin/aoo/trunk|") || die "can't get git log: $!";
    while (<$outputh>) {
	my $line = $_;
	chomp ($line);
#	print STDERR "line '$line'\n";
	my %commit;
	$line =~ s/^(\S+),([^,]+),([^,]+),([^,]+),>>(.*)<<>>(.*)$// || die "badly formatted line: $line";
	$commit{hash} = $1;
	$commit{name} = $2;
	$commit{email} = $3;
	$commit{date} = $4;
	$commit{subject} = $5;
	my $note = $6;

#	print STDERR "here - note is $note\n";
	while (1) {
#	    print STDERR "note: $note";
	    if ($note =~ s/<<//) {
#		print STDERR "no match !";
		last;
	    } else {
		$note = $note . readline $outputh;
	    }
	}

	$commit{note} = clean_note($note);
	push @revisions, \%commit;
    }
    close ($outputh);

    return \@revisions;
}

sub dump_breakdown($)
{
    my $revs = shift;

    my $rev_count = scalar (@{$revs});
    my $annotated = 0;
    my %frequency;
    my $contiguous = 0;
    my $in_start_run = 1;
    for my $rev (@{$revs}) {
	if($rev->{note} ne "") {
	    my $stem = $rev->{note};
	    $stem =~ s/^merged as.*$/merged:/;
	    $stem =~ s/^prefer.*$/prefer:/;
	    $frequency{$stem} = 0 if (!defined $frequency{$stem});
	    $frequency{$stem}++;
	    $annotated++;
	    $contiguous++ if ($in_start_run);
	} else {
	    $in_start_run = 0;
	}
    }

    print STDERR "$annotated annotations of $rev_count commits\n";
    for my $stem (sort { $frequency{$b} <=> $frequency{$a} } keys %frequency) {
	print STDERR "$frequency{$stem}\t$stem\n";
    }
    print STDERR "contiguous annotations: $contiguous\n";
}

sub usage()
{
    print STDERR "Usage: aoo-annotate.pl [args] [/path/to/git]\n";
    print STDERR "annotate AOO commits as to their status\n";
    print STDERR "\n";
    print STDERR "  -a, --all    list all commits regardless of status\n";
    print STDERR "  -n, --notes  list just commits with notes\n";
    print STDERR "  -h, --help   show this\n";
    print STDERR "  -s, --stats  show stats on merging\n";
}

my $git_dir;
my $stats = 0;
my $all = 0;
my $notes = 0;

for my $arg (@ARGV) {
    if ($arg eq '--help' || $arg eq '-h') {
	usage();
	exit;
    } elsif ($arg eq '--stats' || $arg eq '-s') {
	$stats = 1;
    } elsif ($arg eq '--all' || $arg eq '-a') {
	$all = 1;
    } elsif ($arg eq '--notes' || $arg eq '-n') {
	$notes = 1;
    } elsif (!defined $git_dir) {
	$git_dir = $arg;
    } else {
	usage ();
	die "unknown argument: $arg";
    }
}

if (!defined $git_dir) {
    $git_dir = `pwd`;
}

my $revs = read_log($git_dir);

print STDERR "Commits:\n";
for my $rev (@{$revs}) {
    my $note = $rev->{note};
    chomp ($note);
    my $has_note = ($note ne "");
    my $printit = $all || ($has_note && $notes) || (!$has_note && !$notes);
    print "$rev->{hash}\t$rev->{note}\t$rev->{name}\t$rev->{subject}\n" if ($printit);
}

if ($stats == 1) {
    print STDERR "\n";
    dump_breakdown ($revs);
}
