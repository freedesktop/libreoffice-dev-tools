#!/usr/bin/perl -w

use strict;

# A hook script which integrates with bugzilla. It looks for bug IDs in
# commit messages and adds the commit message as well as a link to the
# changeset as a comment on the bug.

# This program is released under the terms of the GNU General Public License
# version 2. A copy of the license may be obtained by emailing the author,
# or at http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
#
# The absolute lack of warranty and other disclaimers as per the license
# apply.
#
# Copyright 2008, Devendra Gera. All rights reserved.
#
# Author : Devendra Gera

### user configurable section

our $bugzilla = {};

use File::Basename;

my $config = dirname($0) . "/config.pl";

do $config;

# The bug_regex should extract the bug id from the commit message and place
# it in $1
my $bug_regex = 'fdo#(\d+)';

# This contains the target version for all commits to master
# Adjust it if a new version branch has been created
my $master_target = '4.4.0';


##### End user configurable section

use vars qw ($tree @parent $author $committer);
use vars qw ($user $rev $logmsg);

my $repo   = $ARGV[0];
my $sha    = $ARGV[1];
my $branch = $ARGV[2];

use WWW::Bugzilla;

my $cgiturl = "http://cgit.freedesktop.org/libreoffice/$repo/commit/?id=$sha";
my $next_version = '';
my $target_version = '';
my $target = 'target:';

if ( !defined( $branch ) || $branch eq '' )
{
    $branch = "master";
    $target .= $master_target;
}
else
{
    $cgiturl .= "&h=$branch";

    # the fix will be available in the first version that branches from this
    if ( $branch =~ /libreoffice-([0-9]+)-([0-9]+)-([0-9]+)\b/ ) {
        $next_version = "\nIt will be available already in LibreOffice $1.$2.$3.";
        $target .= "$1.$2.$3";
    }
    elsif ( $branch =~ /libreoffice-([0-9]+)-([0-9]+)\b/ ) {
        $next_version = "\nIt will be available in LibreOffice $1.$2.";
        my $next = -1;
        $target .= "$1.$2.";
        open BRANCHES, "git branch -r |" or die "cannot get the list of branches";
        while (defined (my $remote = <BRANCHES>)) {
            if ( $remote =~ /$branch-([0-9]+)/ ) {
                if ( $1 > $next ) {
                    $next = $1;
                }
            }
        }
        close BRANCHES;
	if( $next == -1 ) {
		my $tags = "libreoffice-"."$1.$2.0.*";
		open TAGS, "git tag -l $tags |" or die "cannot get the tags";
		my $beta = 0;
		my $RC = 0;
		while (defined (my $tag = <TAGS>)) {
			if( $tag =~ /libreoffice-([0-9]+)\.([0-9]+)\.0\.0\.beta([0-9]+)/) {
				if( $3 > $beta ) {
					$beta = $3;
				}
			}
			if( $tag =~ /libreoffice-([0-9]+)\.([0-9]+)\.0\.([1-9]+)/ ) {
				if ( $3 > $RC ) {
					$RC = $3;
				}
			}
		}

		if( $beta == 2 || $RC > 0) {
			$target = "target:$1.$2.0.";
			$target .= $RC + 1;
		}
		else {
			$target = "target:$1.$2.0.0.beta";
			$target .= $beta +1;
		}

	}
	else {
		$next_version .= $next + 1 . ".";
		$target .= $next + 1;
	}
	}
	else {
# don't update bugzilla for feature branches
		exit;
	}
}

my $line;

open COMMIT, "git cat-file commit $sha|" or die "git cat-file commit $sha: $!";
my $state = 0;
$logmsg = '';
while (defined ($line = <COMMIT>)) {
    if ($state == 1) {
        $logmsg .= $line;
        $state++;
        next;
    } elsif ($state > 1) {
        next;
    }

    chomp $line;
    unless ($line) {
        $state = 1;
        next;
    }

    my ($key, $value) = split(/ /, $line, 2);
    if ($key eq 'tree') {
        $tree = $value;
    } elsif ($key eq 'parent') {
        push(@parent, $value);
    } elsif ($key eq 'author') {
        $author = $value;
        $author =~ s/ <.*//;
    } elsif ($key eq 'committer') {
        $committer = $value;
        $committer =~ s/ <.*//;
    }
}
close COMMIT;

my ($bugNr) = ( $logmsg =~ /$bug_regex/ );

die "no bug number in the commit" unless defined $bugNr;

my $comment = <<END_COMMENT;
$author committed a patch related to this issue.
It has been pushed to "$branch":

$cgiturl

$logmsg
$next_version

The patch should be included in the daily builds available at
http://dev-builds.libreoffice.org/daily/ in the next 24-48 hours. More
information about daily builds can be found at:
http://wiki.documentfoundation.org/Testing_Daily_Builds
Affected users are encouraged to test the fix and report feedback.
END_COMMENT

# sanitize the comment - we are not handling utf-8 correctly from some reason
for ( $comment ) {
    s/á/a/g;
    s/Á/A/g;
    s/é/e/g;
    s/ě/e/g;
    s/É/E/g;
    s/Ě/E/g;
    s/í/i/g;
    s/Í/I/g;
    s/ó/o/g;
    s/Ó/O/g;
    s/ú/u/g;
    s/ů/ů/g;
    s/Ú/U/g;
    s/Ů/U/g;
    s/ý/y/g;
    s/Ý/Y/g;
}

#commit the comment to bugzilla
my $bz = WWW::Bugzilla->new(
        server		=> $bugzilla->{ server },
        email		=> $bugzilla->{ user },
        password	=> $bugzilla->{ password },
        bug_number	=> $bugNr
    );

die "cannot connect to bugzilla" unless defined $bz;

my $whiteboard = $bz->status_whiteboard();

if ( !defined( $whiteboard ) || $whiteboard eq '' )
{
    $whiteboard = $target;
}
elsif ( $target =~ /([0-9]+)\.([0-9]+)\.([0-9]+)/ )
{
    my ( $major, $minor, $micro ) = ( $1, $2, $3 );

    # check that we only get one entry of the form target:$1.$2 even
    # if pushed to libreoffice-$1-$2 and libreoffice-$1-$2-$3
    if ( $whiteboard =~ /target:$major\.$minor\.([0-9]+)/ )
    {
        if ( $micro < $1 )
        {
            $whiteboard =~ s/target:$major\.$minor\.$1/$target/;
        }
    }
    else
    {
    	$whiteboard .= ' ' . $target;
    }
}
else
{
	if( $whiteboard =~ $target ) {
	}
	else {
		$whiteboard .= ' ' . $target;
	}
}

$bz->status_whiteboard($whiteboard);

$bz->additional_comments( $comment );

$bz->commit;
