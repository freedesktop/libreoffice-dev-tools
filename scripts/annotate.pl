#!/usr/bin/perl -w

use strict;

my %valid_reasons = (
    'ignore' => 1,
    'merged as' => 1,
    'prefer' => 1,
    'reject' => 1
);

sub clean_note($)
{
    my $note = shift;
    chomp ($note); # ideally sanitise to pull out our notes ...
    $note =~ m/\n/ && die "multi-line note\n";
    return $note;
}

sub fetch_git_notes($)
{
    my $git_dir = shift;
    `(cd '$git_dir'; git --no-pager fetch origin refs/notes/commits:refs/notes/commits)`;
}

sub push_git_notes($)
{
    my $git_dir = shift;
    `(cd '$git_dir'; git --no-pager push origin refs/notes/commits:refs/notes/commits)`;
}

# starts with a git hash;
sub validate_git_hash($)
{
    my $hash = shift;
    return 0 if (! ($hash =~ m/^([0-9a-fA-F]{40})/) );
    return 1;
}

sub validate_check_note($)
{
    my $note_text = shift;
    $note_text =~ m/^(\S.+):\s+(.+)$/ || die "note: '$note_text' is missing a explanation: reason";
    my $reason = $1;
    my $expl = $2;

    if (!defined $valid_reasons{$reason}) {
	my @reasons = keys %valid_reasons;
	print STDERR "Invalid reason: '$reason' - valid reasons are @reasons\n";
	exit 1;
    } elsif ($reason eq 'merged as' || $reason eq 'prefer') {
	validate_git_hash($expl) ||
	    die "reason '$reason' must have an explanation beginning with a git hash\n";
    }
}

sub read_log($)
{
    my $git_dir = shift;
    my @revisions;
    my $outputh;

#    print STDERR "read revisions:\n";
    open ($outputh, "cd '$git_dir' ; git --no-pager log --pretty='%H,%cn,%ce,%cd,>>%s<<>>%N<<' aoo/approx-3.4.0..origin/aoo/trunk|") || die "can't get git log: $!";
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
    for my $rev (reverse @{$revs}) {
	if($rev->{note} ne "") {
	    my $stem = $rev->{note};
	    $stem =~ s/^merged as.*$/merged as:/;
	    $stem =~ s/^prefer.*$/prefer:/;
	    $stem =~ s/^reject.*$/reject:/;
	    $frequency{$stem} = 0 if (!defined $frequency{$stem});
	    $frequency{$stem}++;
	    $annotated++;
	    $contiguous++ if ($in_start_run);
	} else {
	    $in_start_run = 0;
	}
    }

    print "$annotated annotations of $rev_count commits\n";
    for my $stem (sort { $frequency{$b} <=> $frequency{$a} } keys %frequency) {
	print "$frequency{$stem}\t$stem\n";
    }
    print "contiguous annotations: $contiguous\n";
}

sub sanity_check_revs($$)
{
    my $git_dir = shift;
    my $revs = shift;
    my $note_count = 0;
    for my $rev (@{$revs}) {
	my $note = $rev->{note};
	$note_count++ if ($note ne "");
    }
    if ($note_count < 100) {
	print STDERR "It looks as if you have not fetched your git notes please add the -f parameter to do that, or in extremis do:\n";
	print STDERR "(cd '$git_dir'; git --no-pager fetch -f origin refs/notes/commits:refs/notes/commits)\n";
	print STDERR "attempting to fetch notes for you ...\n";
	fetch_git_notes($git_dir);
	print STDERR "exiting, re-start me ...\n";
	exit 1;
    }
}

# ensure the hash we're annotating is in the right tree
sub check_hash_for_note($$)
{
    my ($git_dir, $hash) = @_;
    my $revs = read_log($git_dir);
    for my $rev (@{$revs}) {
	return if ($rev->{hash} eq $hash);
    }
    die "Unknown hash '$hash' - did you get your hashes the wrong way around ?";
}

sub usage()
{
    print STDERR "Usage: aoo-annotate.pl [args] [--git /path/to/git] ['merged as: 1234' <hash>]\n";
    print STDERR "annotate AOO commits as to their status\n";
    print STDERR "\n";
    print STDERR "  -a, --all     list all commits regardless of status\n";
    print STDERR "  -g, --git <d> pass a path to a git repository [default is cwd]\n";
    print STDERR "  -l, --list    list all un-annotated commits\n";
    print STDERR "  -n, --notes   list just commits with notes\n";
    print STDERR "  -h, --help    show this\n";
    print STDERR "  -s, --stats   show stats on merging\n";
    print STDERR "  -f, --fetch   fetch latest notes\n";
}

my $git_dir;
my $stats = 0;
my $all = 0;
my $list = 0;
my $notes = 0;
my $fetch = 0;
my $note_text;
my $note_hash;

while (my $arg = shift @ARGV) {
    if ($arg eq '--help' || $arg eq '-h') {
	usage();
	exit;
    } elsif ($arg eq '--stats' || $arg eq '-s') {
	$stats = 1;
    } elsif ($arg eq '--fetch' || $arg eq '-f') {
	$fetch = 1;
    } elsif ($arg eq '--list' || $arg eq '-l') {
	$list = 1;
    } elsif ($arg eq '--all' || $arg eq '-a') {
	$all = 1;
	$list = 1;
    } elsif ($arg eq '--notes' || $arg eq '-n') {
	$notes = 1;
    } elsif ($arg eq '--git' || $arg eq '-g') {
	$git_dir = shift @ARGV;
    } elsif (!defined $note_text) {
	$note_text = $arg;
    } elsif (!defined $note_hash) {
	$note_hash = $arg;
    } else {
	usage ();
	die "unknown argument: $arg";
    }
}

if (!defined $git_dir) {
    $git_dir = `pwd`;
    chomp ($git_dir);
}

if (!$list && !$stats && !$fetch) {

    print "$note_text' '$note_hash\n";
    if (!defined $note_text || !defined $note_hash) {
	usage();
	die "need some note text";
    }

    validate_check_note($note_text);
    validate_git_hash($note_hash) ||
	    die "Hash on master '$note_hash' doesn't look like a git hash\n";

    check_hash_for_note($git_dir, $note_hash);
    fetch_git_notes($git_dir);
    `( cd '$git_dir' ; git --no-pager notes add -m '$note_text' $note_hash )`;
    push_git_notes($git_dir);
} else {
    fetch_git_notes($git_dir) if ($fetch);

    my $revs = read_log($git_dir);
    sanity_check_revs($git_dir, $revs);

    if ($list) {
	print STDERR "Commits:\n";
	for my $rev (@{$revs}) {
	    my $note = $rev->{note};
	    chomp ($note);
	    my $has_note = ($note ne "");
	    my $printit = $all || ($has_note && $notes) || (!$has_note && !$notes);
	    print "$rev->{hash}\t$rev->{note}\t$rev->{name}\t$rev->{subject}\n" if ($printit);
	}
    }

    if ($stats == 1) {
	print STDERR "\n" if ($list);
	dump_breakdown ($revs);
    }
}
