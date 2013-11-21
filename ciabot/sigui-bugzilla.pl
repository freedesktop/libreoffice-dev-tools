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

do $ENV{'HOME'} . "/bin/config.pl";

# The bug_regex should extract the bug id from the commit message and place
# it in $1
my $bug_regex = 'fdo#(\d+)';

##### End user configurable section

use vars qw ($tree @parent $author $committer);
use vars qw ($user $rev $logmsg);

my $repo   = $ARGV[0];
my $sha    = $ARGV[1];
my $branch = $ARGV[2];

use WWW::Bugzilla;
my $cgiturl = "https://gerrit.libreoffice.org/gitweb?p=$repo.git;a=commit;h=$sha";
$branch = "master";
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

The patch should be included in the next version of SI-GUI.
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

my $product = $bz->product;

die "wrong product" unless $product eq 'LibreOffice';


$bz->additional_comments( $comment );

$bz->commit;