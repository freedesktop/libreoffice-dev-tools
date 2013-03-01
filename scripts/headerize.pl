#!/usr/bin/perl -w

#
# Tool for prepending an MPLv2 header to an existing ALv2
# licensed module; must only be used on ALv2 licensed code.
# pipe a list of files to update into this tool.
#

use strict;

my $dry_run = 0;
my $headerize = 0;

my $header_string =
'* This file is part of the LibreOffice project.
*
* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at http://mozilla.org/MPL/2.0/.
*
* This file incorporates work covered by the following license notice:
*
*   Licensed to the Apache Software Foundation (ASF) under one or more
*   contributor license agreements. See the NOTICE file distributed
*   with this work for additional information regarding copyright
*   ownership. The ASF licenses this file to you under the Apache
*   License, Version 2.0 (the "License"); you may not use this file
*   except in compliance with the License. You may obtain a copy of
*   the License at http://www.apache.org/licenses/LICENSE-2.0 .
';

sub emit_header($$)
{
    my ($file, $fmt) = @_;
    print $file $fmt->{pre} . "\n";
    my $header = $header_string;
    $header =~ s/\*/$fmt->{comment}/g;
    print $file "$header";
    print $file $fmt->{post} . "\n";
}

my %idl = (
    ext        => qr/\.idl$/,
    start_re   => '^\s*\/\*{10,}',
    end_re     => '^\s*\*\s*\*{10,}.*\*\/',
    pre        => '/*',
    comment    => ' *',
    post       => ' */',
    in_n_lines => 5,
    bin_utf8   => 1,
);

my %cplus_plus = (
    ext        => qr/\.[ch]$/,
    ext2       => qr/\.[ch]xx$/,
    ext3       => qr/\.[sh]rc$/,
    ext4       => qr/\.sdi$/,
    ext5       => qr/\.java$/,
    ext6       => qr/\.idl$/,
    ext7       => qr/\.ulf$/,
    ext8       => qr/\.[ch]pp$/,
    ext9       => qr/\.inc$/,
    ext10      => qr/\.s$/,
    ext11      => qr/\.cs$/,
    ext12      => qr/\.y$/,
    ext13      => qr/\.mm$/,
    ext14      => qr/verinfo\.rc$/,
    ext15      => qr/\.cc$/,
    ext16      => qr/\.css$/,
    start_re   => '^\s*\/\*{10,}',
    end_re     => '^\s*\*\s*\*{10,}.*\*\/',
    pre        => '/*',
    comment    => ' *',
    post       => ' */',
    in_n_lines => 5,
    bin_utf8   => 1,
);

my @formats = ( \%cplus_plus, \%idl );

sub find_format($)
{
    my $fname = shift;
    for my $fmt (@formats) {
	# try to match all 'ext' prefixed keys
	for my $extkey (keys %{$fmt}) {
	    $extkey =~ m/^ext/ || next;
	    my $re = $fmt->{$extkey};
#	    print STDERR "match '$fname' vs '$re'\n";
	    return $fmt if ($fname =~ m/$re/);
	}
    }
#    print STDERR "no match\n";
    my $undefined;
    return $undefined;
}

while (my $arg = shift @ARGV) {
    if ($arg eq '--dry-run') {
	$dry_run = 1;
    } elsif ($arg eq '--headerize') {
	$headerize = 1;
    } else {
	die "unknown arg $arg";
    }
}

# Read filenames from stdin and re-write headers for re-based files
my $cwd = `pwd`;
chomp ($cwd);

while (<STDIN>) {
    my $fname = $_;
    chomp ($fname);
    $fname =~ /^\s*$/ && next;
    $fname =~ /^#/ && next; # comment
    $fname = "$cwd/$fname"; # qualify the path

    my $fmt = find_format ($fname);
    if (!defined $fmt) {
	print STDERR "$fname:0:0 warning: unknown format\n" if (!has_license($fname));
	next;
    }
    my $start_re = qr/$fmt->{'start_re'}/;
    my $end_re = qr/$fmt->{'end_re'}/;

    my ($in, $out);

    open ($in, "$fname") || die "can't open $fname: $!";
    if ($dry_run) {
	open ($out, ">", "/dev/null");
    } else {
	open ($out, ">", "$fname.new") || die "can't open $fname.new: $!";
    }
    my $in_header = 0;
    my $ignore_white = 0;
    my $header_count = 0;
    my $line_count = 0;
    my $re_written = 0;
    my $mplv2_relicensed = 0;
    my $apache_header = 0;
    while (<$in>) {
	my $line = $_;

	# we sometimes get some mis-guided utf-8 flagging chars at the top
	if ($line_count == 0 && defined ($fmt->{bin_utf8})) {
	    $line =~ s/^\xef\xbb\xbf//;
	}
#	print STDERR "$line_count $line";

	if ($headerize && $header_count == 0) { # add headers where missing
	    emit_header($out, $fmt);
	    print $out $line;
	    $re_written = 1;
	    $header_count++;
	}

	$mplv2_relicensed = 1 if ($line =~ m/This file is part of the LibreOffice project/);

	if (!$in_header && $line =~ m/$start_re/) {
#	    print STDERR "hit header !\n";
	    if ($line_count < $fmt->{in_n_lines}) {
		if ($header_count == 0) {
		    $in_header = 1;
		} else {
		    print STDERR "odd: more than one license header in $fname\n";
		}
		$header_count++;
	    } else {
#		print STDERR "start of license comment not at top of $fname:$line_count\n";
		print $out $line;
	    }
	} elsif ($in_header && $line =~ m/$end_re/) {
	    $in_header = 0;
	    if ($apache_header < 2 && !$mplv2_relicensed) {
		print STDERR "$fname:0:0 error: invalid header\n";
		die;
		last;
	    }
	    emit_header($out, $fmt);
	    $ignore_white = 1;
	    $re_written = 1;
	} elsif ($in_header) { # skip it.
	    $apache_header++ if ($line =~ m|to you under the Apache License, Version 2.0|);
	    $apache_header++ if ($line =~ m|distributed with this work for additional information|);
	} else {
	    if ($line =~ m/^\s*$/ && $ignore_white) {
		# don't output line
	    } else {
		$ignore_white = 0;
		print $out $line;
	    }
	}
	$line_count++ if (!($line =~ m/^\s*$/));
    }
    close ($out);
    close ($in);

    if ($mplv2_relicensed && $re_written) {
	print STDERR "$fname:0:0 error: added a redundant MPL license header.\n";
	die;
    }
    if ($header_count > 1) {
	print STDERR "$fname:0:0 error: more than one header\n";
	die;
    }
    if ($in_header) {
	print STDERR "$fname:0:0 error: failed to exit header\n";
	die;
    }
    if (!$re_written && !$mplv2_relicensed) {
	print STDERR "$fname:0:0 failed to re-write header\n";
	die;
    }
    if ($re_written && !$dry_run) {
	rename ("$fname", "$fname.bak") || die "Can't rename away $fname: $!";
	rename ("$fname.new", "$fname") || die "Can't replace $fname: $!";
    }
}
