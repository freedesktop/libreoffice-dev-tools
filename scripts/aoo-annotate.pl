#!/usr/bin/perl -w

# use strict;

sub read_git_notes($)
{
    my $git_dir = shift;
    my %has_note;
    my $outputh;

    print STDERR "read legacy tags from notes\n";
    open ($outputh, "cd $git_dir ; git notes list |") || die "can't read git notes";
    while (<$outputh>) {
	/\s*(\S+)\s+(\S+)$/ || die "badly formatted '\$ git notes list' output";
	$has_note{$2} = 1;
    }
    close ($outputh);

    return \%has_note;
}

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

    print STDERR "read revisions:\n";
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

my $git_dir = shift @ARGV;

if (!defined $git_dir) {
    $git_dir = `pwd`;
}

my $has_note = read_git_notes($git_dir);
my $revs = read_log($git_dir);

my $rev_count = scalar (@{$revs});

print STDERR "Commits to scan $rev_count\n";

for my $rev (@{$revs}) {

    my $note = $rev->{note};
    chomp ($note);
    print "$rev->{hash}\t$rev->{note}\n";
}
