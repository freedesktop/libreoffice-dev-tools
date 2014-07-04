#!/usr/bin/perl -w

use FindBin;
use lib "$FindBin::Bin";

use strict;
use Bugzilla;

my $git_dir = '/opt/libreoffice/push-tree';

# FIXME: add a re-build-section thing ...
# German comments: overall stats ... smallest <N> modules ...
# a bit of text on how to fix that etc.

sub usage()
{
    print "build-portal.pl [--help] [--git path/to/git/repo]\n";
    exit 1;
}

sub read_dialogs($)
{
    my $dialogs = shift;

    my $pipe;
    open ($pipe, "(cd $git_dir ; bin/count-todo-dialogs)|") || die "can't count dialogs: $!";
    while (<$pipe>) {
	my $line = $_;
	if (m/(\d+) \.ui files currently/) {
	    $dialogs->{ui_files} = $1;
	} elsif (m/There are (\d+) unconverted dialogs/) {
	    $dialogs->{ui_dialogs} = $1;
	} elsif (m/There are (\d+) unconverted tabpages/) {
	    $dialogs->{ui_tabpages} = $1;
	}
    }
    close ($pipe);
}

while (my $arg = shift(@ARGV)) {
    usage() if ($arg eq '--help' || $arg eq '-h');
}

my %dialogs;

read_dialogs(\%dialogs);

print << "EOF"
<html>
<header>
LibreOffice Development Portal
</header>
<body>
    <div>
    <p><strong>UI dialogs</strong</p>
    <p>$dialogs{ui_files} UI files</p>
    <p>$dialogs{ui_dialogs} dialogs left</p>
    <p>$dialogs{ui_tabpages} tab-pages left</p>
    <a href="FIXME: Caolan's write-up">Get Involved</a>
    </div>
</body>
</html>
EOF
    ;

