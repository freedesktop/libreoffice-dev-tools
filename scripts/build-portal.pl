#!/usr/bin/perl -w

use strict;

my $git_dir = '/opt/libreoffice/push-tree';

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
    </div>
</body>
</html>
EOF
    ;

