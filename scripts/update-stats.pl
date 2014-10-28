#!/usr/bin/perl -w

use strict;

my %versions = (
#    '7362ca8' => '3.5.0_Beta1',
#    '8589e48' => '3.5.0_Beta2',
#    'da8462e' => '3.5.0_Beta2', # mac
#    'e40af8c' => '3.5.0_Beta3',
#    'b6c8ba5' => '3.5.0_RC1',
#    'e371a95' => '3.5.0_RC2',
    '7e68ba2' => '3.5.0_RC3',
#    '45a2874' => '3.5.1_RC1',
    'dc9775d' => '3.5.1_RC2',
#    '1488b14' => '3.5.2_RC1',
    '281b639' => '3.5.2_RC2',
#    '21cb047' => '3.5.3_RC1',
    '235ab8a' => '3.5.3_RC2',
#    '7306755' => '3.5.4_RC1',
    '165a79a' => '3.5.4_RC2',
#    'c9944f7' => '3.5.5_RC1',
#    '24b32b4' => '3.5.5_RC2',
    '7122e39' => '3.5.5_RC3',
#    '9cb76c3' => '3.5.6_RC1',
    'e0fbe70' => '3.5.6_RC2',
#    '3fa2330' => '3.5.7_RC1',
    '3215f89' => '3.5.7_RC2',

#    '1f1cdd8' => '3.6.0_Beta1',
#    'f010139' => '3.6.0_Beta2',
#    '3e2b862' => '3.6.0_Beta3',
#    '73f9fb6' => '3.6.0_RC1',
#    '815c576' => '3.6.0_RC2',
#    '61d5034' => '3.6.0_RC3',
    '932b512' => '3.6.0_RC4',
#    '4db6344' => '3.6.1_RC1',
    'e29a214' => '3.6.1_RC2',
#    'ba822cc' => '3.6.2_RC1',
    'da8c1e6' => '3.6.2_RC2',
#    'f8fce0b' => '3.6.3_RC1',
    '58f22d5' => '3.6.3_RC2',
#    'a9a0717' => '3.6.4_RC1',
#    '859ab85' => '3.6.4_RC2', // skipped
    '2ef5aff' => '3.6.4_RC3',
#    No 3.6.5 RC1 at all
    '5b93205' => '3.6.5_RC2',
#    'a61ad19' => '3.6.6_RC1',
    'f969faf' => '3.6.6_RC2',

    '7545bee9c2a0782548772a21bc84a9dcc583b89' => '4.0.0_RC3',
    '53fd80e80f44edd735c18dbc5b6cde811e0a15c' => '4.0.0_RC3', # mac

    '84102822e3d61eb989ddd325abf1ac077904985' => '4.0.1_RC2',

    '4c82dcdd6efcd48b1d8bba66bfe1989deee49c3' => '4.0.2_RC2',

    '0eaa50a932c8f2199a615e1eb30f7ac74279539' => '4.0.3_RC3',

    '9e9821abd0ffdbc09cd8c52eaa574fa09eb08f2' => '4.0.4_RC2',

    '5464147a081647a250913f19c0715bca595af2f' => '4.0.5_RC2',

    '2e2573268451a50806fcd60ae2d9fe01dd0ce24' => '4.0.6_RC2',

    '89ea49ddacd9aa532507cbf852f2bb22b1ace28' => '4.1.0_RC4',

    '7e4286b58adc75a14f6d83f53a03b6c11fa2903' => '4.1.1_RC2',

    '40b2d7fde7e8d2d7bc5a449dc65df4d08a7dd38' => '4.1.2_RC3',

    '70feb7d99726f064edab4605a8ab840c50ec57a' => '4.1.3_RC3',

    '0a0440ccc0227ad9829de5f46be37cfb6edcf72' => '4.1.4_RC2',

    '1c1366bba2ba2b554cd2ca4d87c06da81c05d24' => '4.1.5_RC3',

    '40ff705089295be5be0aae9b15123f687c05b0a' => '4.1.6_RC2',

    '05dceb5d363845f2cf968344d7adab8dcfb2ba71' => '4.2.0_RC4',

    'd7dbbd7842e6a58b0f521599204e827654e1fb8b' => '4.2.1_RC1',

    '3be8cda0bddd8e430d8cda1ebfd581265cca5a0f' => '4.2.2_RC1',

    '6c3586f855673fa6a1576797f575b31ac6fa0ba3' => '4.2.3_RC3',
    '882f8a0a489bc99a9e60c7905a60226254cb6ff0' => '4.2.3_RC3', # hotfix1

    '63150712c6d317d27ce2db16eb94c2f3d7b699f8' => '4.2.4_RC2',

    '61cb170a04bb1f12e77c884eab9192be736ec5f5' => '4.2.5_RC2',
    '6ff819b65674ae6c83f3cbab9e4a4c2b292a7a94' => '4.2.5_RC2', # hotfix1

    '185f2ce4dcc34af9bd97dec29e6d42c39557298f' => '4.2.6_RC2',
    '3fd416d4c6db7d3204c17ce57a1d70f6e531ee21' => '4.2.6_RC2', # secfix1

    '62ad5818884a2fc2e5780dd45466868d41009ec0' => '4.3.0_RC4',

    '958349dc3b25111dbca392fbc281a05559ef6848' => '4.3.1_RC2',

    'edfb5295ba211bd31ad47d0bad0118690f76407d' => '4.3.2_RC2',
);

my %month_to_num = (
    'Jan' => '01',
    'Feb' => '02',
    'Mar' => '03',
    'Apr' => '04',
    'May' => '05',
    'Jun' => '06',
    'Jul' => '07',
    'Aug' => '08',
    'Sep' => '09',
    'Oct' => '10',
    'Nov' => '11',
    'Dec' => '12',
);

my $try_geoip = 0;

my %result_ips;
my %result_versions;
my %result_os;
my %result_daily;
my %result_geoip;
my %result_countries;

# update first
system('rsync -av gimli.documentfoundation.org:update/ logs/ 1>&2');

#open LOG, "update.libreoffice.org-access_log" or die "Cannot open the log";
open LOG, "( bzcat logs/update.libreoffice.org-access_log-*.bz2 ; cat logs/update.libreoffice.org-access_log ) |" or die "Cannot open the log";
while (<LOG>) {
    if ( /^([^ ]+) - - \[([^\/]+)\/([^\/]+)\/([^:]+):([0-9][0-9])[^\]]*\] "[^"]*" [^ ]+ [^ ]+ "[^"]*" "[^(]*\(([^-;]+)[^;]*; ([^;]*);/ ) {
	#print "$1, $2, $3, $4, $5, $6, $7\n";
	my ( $ip, $day, $month, $year, $hour, $version, $os ) =
	    ( $1, $2, $month_to_num{$3}, $4, $5, $versions{$6}, $7 );

	if ( defined( $version ) ) {
	    my $date = "$year-$month-$day";
	    my $time = "$date\_$hour";

	    # new unique IP's per hour (regardless the version / os / etc.)
	    my $unique = 0;
	    if ( !defined( $result_ips{$ip} ) ) {
		$unique = 1;
	    }
	    if ( !$unique ) {
		$unique = 1;
		foreach my $ver ( values( %versions ) ) {
		    $unique = 0 if ( defined( $result_ips{$ip}{$ver} ) );
		}
	    }

	    # count the unique IP to be able to get the cummulative count
	    if ( $unique ) {
		if ( !defined( $result_daily{$date}{'unique'} ) ) {
		    $result_daily{$date}{'unique'} = 0;
		}
		++$result_daily{$date}{'unique'};

		# geoip counts
		if ( $try_geoip ) {
		    my $country = `geoiplookup '$ip'`;
		    chomp $country;
		    $country =~ s/^.*, //;
		    if ( !defined( $result_countries{$country} ) ) {
			$result_countries{$country} = 1;
		    }
		    if ( !defined( $result_geoip{$date}{$country} ) ) {
			$result_geoip{$date}{$country} = 0;
		    }
		    ++$result_geoip{$date}{$country};
		}
	    }

	    if ( !defined( $result_ips{$ip}{$version}{$os} ) ) {
		$result_ips{$ip}{$version}{$os} = 1;

		if ( !defined( $result_versions{$version}{$os} ) ) {
		    $result_versions{$version}{$os} = 0;
		}
		++$result_versions{$version}{$os};

		# daily reports per version
		if ( !defined( $result_daily{$date}{$version} ) ) {
		    $result_daily{$date}{$version} = 0;
		}
		++$result_daily{$date}{$version};
	    }

	    # just to keep the list of all osses we have
	    if ( !defined( $result_os{$os} ) ) {
		$result_os{$os} = 1;
	    }
	}
    }
}
close LOG;

print "Generated on: " . qx(date --rfc-3339=seconds) . "\n";
print "Unique IP addresses (from where LO asked for updates up to now): " . keys( %result_ips ) . "\n\n";

print "Version";
foreach my $os ( sort( keys %result_os ) ) {
    print ",$os abs";
}
print ",all";
foreach my $os ( sort( keys %result_os ) ) {
    print ",$os %";
}
print "\n";
foreach my $version ( sort( keys( %result_versions ) ) ) {
    printf '%s', $version;
    my $all = 0;
    foreach my $os ( sort( keys %result_os ) ) {
	my $num = $result_versions{$version}{$os};
	$all += $num if ( defined( $num ) );
    }
    my $percentage = "";
    foreach my $os ( sort( keys %result_os ) ) {
	my $num = $result_versions{$version}{$os};
	$num = 0 if ( !defined( $num ) );
	print ",$num";
	$percentage .= ',' . sprintf( '%d', 100*($num/$all) );
    }
    print ",$all$percentage\n";
}

my @print_versions = ( 'unique', sort( keys( %result_versions ) ) );

print "\nNew IP's asking for update per day:\n\nTime,new unique IP's (never seen before)";
foreach my $version ( sort( keys( %result_versions ) ) ) {
    print ",$version";
}
print "\n";
foreach my $date ( sort( keys( %result_daily ) ) ) {
    print "$date";
    foreach my $version ( @print_versions ) {
	my $count = $result_daily{$date}{$version};
	if ( !defined( $count ) ) {
	    print ",";
	} else {
	    print ",$count";
	}
    }
    print "\n";
}

if ( $try_geoip ) {
    print "\nNew IP's asking for update per day per country:\n\nTime";
    foreach my $country ( sort( keys( %result_countries ) ) ) {
	print ",$country";
    }
    print "\n";
    foreach my $date ( sort( keys( %result_geoip ) ) ) {
	print "$date";
	foreach my $country ( sort( keys( %result_countries ) ) ) {
	    my $count = $result_geoip{$date}{$country};
	    if ( !defined( $count ) ) {
		print ",";
	    } else {
		print ",$count";
	    }
	}
	print "\n";
    }
}
