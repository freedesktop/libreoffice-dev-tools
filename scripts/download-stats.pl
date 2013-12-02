#!/usr/bin/perl -w

use strict;
use threads ('yield',
	     'stack_size' => 64*4096,
	     'exit' => 'threads_only',
	     'stringify');
use POSIX qw(strftime);

my $verbose = 0;
my $rsync_first = 0;
my $cpus_to_use = 16;    # level of parallelism
my $bzcat_grouping = 10; # files to pass to bzcat at once
my $path_to_log_tree;
my $threaded = 1;

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

my %products;
my %allversions;
my %all_files_list;
my %date_product_count;
my %date_version_count;
my $total_downloads;

# FIXME: ODF is -incredibly- lame in this regard ... we badly want R1C1 style referencing here [!]
sub coltoref($)
{
    my $col = shift;
    die ("odff needs R1C1") if ($col > 25);
    return chr (ord('A') + $col);
}

sub print_date_cell($$)
{
    my ($style,$date) = @_;
    # sadly not truly a date but a year + ISO week number.
print << "EOF"
            <table:table-cell table:style-name="$style" office:value-type="string">
                  <text:p>$date</text:p>
	    </table:table-cell>
EOF
;
}

sub find_logs($);
sub find_logs($)
{
    my $path = shift;
    my $dirh;
    my @logfiles;

    if (-l $path) {
	$path = readlink $path;
    }

    if (-f $path ) {
	if ($path =~ m/documentfoundation\.org.*[0-9][-_]access[_.]log/) {
	    if ($verbose) {
		print STDERR "hit: $path\n";
	    }
	    return $path;
	} else {
	    return;
	}
    }

    if (!-d $path) {
	return;
    }

    opendir ($dirh, $path) || die "can't open '$path': $!";
    while (my $name = readdir ($dirh)) {
	next if ($name =~ m/^\./);
	push @logfiles, find_logs("$path/$name");
    }
    close ($dirh);

    return @logfiles;
}

sub is_uninteresting_file($)
{
    my $file = shift;

    return 1 if ( $file =~ /^$/ );
    return 1 if ( $file =~ /^{/ );
    return 1 if ( $file =~ /^%/ );
    return 1 if ( $file =~ /^debian-repo\/testing\// );
    return 1 if ( $file =~ /^\/libreoffice\/old\// );
    return 1 if ( $file =~ /^\/libreoffice\/src\// );
    return 1 if ( $file =~ /^\/robots\.txt$/ );
    return 1 if ( $file =~ /\/index\.php$/ );
    return 1 if ( $file =~ /\/a\.sh$/ );
    return 1 if ( $file =~ /^\/TIMESTAMP/ );

    # ignore source
    return 1 if ( $file =~ m|/src/| );

    # ignore android remote
    return 1 if ( $file =~ m/ImpressRemote.apk$/ );

    # anywhere
    return 1 if ( $file =~ /\/customer_testimonials.php/ );

    # anything that is missing an extension (directory names, metafiles) and slash
    return 1 if ( $file =~ /\/[^.\/]+$/ );
    return 1 if ( $file =~ /^[^\/]+$/ );

    # not interesting extensions
    return 1 if ( $file =~ /\/$/ );
    return 1 if ( $file =~ /\?C=[MNS];O=[AD]$/ );
    return 1 if ( $file =~ /\.asc$/ );
    return 1 if ( $file =~ /\.btih$/ );
    return 1 if ( $file =~ /\.css$/ );
    return 1 if ( $file =~ /\/favicon\.ico$/ );
    return 1 if ( $file =~ /\.gif$/ );
    return 1 if ( $file =~ /\.gpg$/ );
    return 1 if ( $file =~ /\.html$/ );
    return 1 if ( $file =~ /\.info\.php$/ );
    return 1 if ( $file =~ /\.log$/ );
    return 1 if ( $file =~ /\.magnet$/ );
    return 1 if ( $file =~ /\.md5$/ );
    return 1 if ( $file =~ /\.meta4$/ );
    return 1 if ( $file =~ /\.metalink$/ );
    return 1 if ( $file =~ /\.mirrorlist$/ );
    return 1 if ( $file =~ /\/Packages$/ );
    return 1 if ( $file =~ /\/Packages\.bz2$/ );
    return 1 if ( $file =~ /\/Packages\.gz$/ );
    return 1 if ( $file =~ /\/Packages\.lzma$/ );
    return 1 if ( $file =~ /\/Packages\.xz$/ );
    return 1 if ( $file =~ /\.png$/ );
    return 1 if ( $file =~ /\/Release$/ );
    return 1 if ( $file =~ /\.sha1$/ );
    return 1 if ( $file =~ /\.sha256$/ );
    return 1 if ( $file =~ /\.torrent$/ );
    return 1 if ( $file =~ /\.zsync$/ );

    # noise
    return 1 if ( $file =~ /%/ );
    return 1 if ( $file =~ /&/ );

    # is interesting ...
    return 0;
}

sub characterise($$)
{
    my ($filerec, $file) = @_;

    # currently based entirely on the filename
    $file =~ m|/([^/]+)$| || die "not a filename: '$file'";
    my $name = $1;

    $name =~ s/BrOffice/LibO/; # BrOffice is obsolete
    $name =~ s/-/_/g; # use underscores everywhere

    my @elements = split(/_/, $name);

    if (@elements < 2) {
	print STDERR "Unknown filename '$name'\n";
	return 0;
    }
    my $prod = $elements[0];

    if ($prod eq 'LibO' &&
	( $elements[1] eq 'SDK' || $elements[1] eq 'Dev' ) ) { # ignore sdk + dev-builds
	return 0;

    } elsif ( $prod eq 'LibreOfficePortableTest') {     # ignore test builds
	return 0;

    # Odd - legacy stuff
    } elsif ($prod eq 'libreoffice' && (
		 $name =~ m/\.tar\.gz$/ ||
		 $name =~ m/\.tar.bz2$/ ||
		 $name =~ m/\.tar\.xz$/)) { # source
	return 0;

    # obsolete snafu
    } elsif ($prod eq 'libo3.4.4' && $name =~ /\.iso$/) {
	$filerec->{version} = '3.4.4';
	$filerec->{product} = 'Win-dvd';

    # LibreOffice portable
    } elsif ($prod eq 'LibreOfficePortable') {
	if ($name =~ m/(\d\.\d\.\d).*\.exe$/) {
	    $filerec->{version} = $1;
	    $filerec->{product} = 'Win-portable';
	} else {
	    print STDERR "Unknown portable version in '$name'\n";
	    return 0;
	}

    # Bread and butter:
    } elsif ($prod eq 'LibO' || $prod eq 'LibreOffice' ||
	     $prod eq 'LO' || $prod eq 'LibOx') {
	$filerec->{version} = $elements[1];

	my $product;
	if ($name =~ m/\.iso$/) {
	    if ($name =~ m/allproducts/) {
		$product = "All-dvd";
	    } else {
		$product = "Win-dvd";
	    }
	} elsif ($name =~ m/Win_x86/) {
	    $product = "Win-x86";
	} elsif ($name =~ m/Linux_x86-64/) {
	    $product = "Linux-x86-64";
	} elsif ($name =~ m/Linux_x86/) {
	    $product = "Linux-x86";
	} elsif ($name =~ m/MacOS_x86/) {
	    $product = "Mac-x86";
	} elsif ($name =~ m/MacOS_PPC/) {
	    $product = "Mac-PPC";
	} else {
	    print STDERR "Unknown product for '$name'\n";
	}
	$filerec->{product} = $product;

    } else {
	print STDERR "Unknown initial element '$prod' of '$name'\n";
	return 0;
    }

    # characterise helppacks and langpacks

    $name =~ s/helppack/langpack/g; # destructive !
    $filerec->{langpack} = 0;
    if ($name =~ /_langpack_/ ) {
	$filerec->{langpack} = 1;
    }
#    print STDERR "'$name' is a lang-pack: " . $filerec->{langpack} . "\n";

    return 1;
}

sub parse_log($)
{
    my $log = shift;
    my @files;

    # in order to get a good representation of weeks at the start and end of the
    # year (so that we don't get 1/2 of the data at the end, and 1/2 at the start
    # of the next one), we use "epoch_week" - week since 1970-01-01 (1st week)
    my $old_date = "";
    my $epoch_week;
    my %epoch_week_to_year;

    while (<$log>) {
	my $line = $_;
	if ( $line =~ m/^([^ ]+) - - \[([^\/]+)\/([^\/]+)\/([^:]+):([0-9][0-9])[^\]]*\] "GET ([^"]*) HTTP\/[^"]*" ([0-9]+) ([0-9]+)/ ) {
	    #print "$1, $2, $3, $4, $5, $6\n";
	    my ( $ip, $day, $month, $year, $hour, $file, $status, $size ) = ( $1, $2, $month_to_num{$3}, $4, $5, $6, $7, $8 );

	    # we are interested only in redirects and successful downloads
	    next if ( $status != 302 && $status != 200 && $status != 206 );

	    # partial download? - only count when it finished
	    if ( $status == 206 )
	    {
		if ( $line =~ / size:([0-9]+) bytes=([0-9]+)-([0-9]*)$/ )
		{
		    my ( $wanted, $from ) = ( $1, $2 );
		    next if ( $wanted != $from + $size );
		}
		else {
		    next;
		}
	    }

	    # canonicalize
	    $file =~ s/^\s+//;
	    $file =~ s/\s+$//;
	    $file =~ s/^http:\/\/download.documentfoundation.org//g;
	    $file =~ s/\/\//\//g;
	    $file =~ s/\?.*//g;
	    $file =~ s/;jsessionid=.*//g;
	    $file =~ s/\/libreoffice\/box\///g;
	    $file =~ s/\/libreoffice\/old\///g;
	    $file =~ s/\/libreoffice\/portable\///g;
	    $file =~ s/\/libreoffice\/stable\///g;
	    $file =~ s/\/libreoffice\/testing\///g;

	    # not interesting path starts
	    next if ( is_uninteresting_file ($file) );

	    my %filerec;
	    $filerec{file} = $file;

	    next if ( ! characterise(\%filerec, $file) );

	    # update the $epoch_week, if necessary
	    if ( "$year-$month-$day" ne $old_date ) {
		$old_date = "$year-$month-$day";

		# 1970-01-01 is Thursday, add 3 days (259200 seconds), and divide
		my $seconds = POSIX::strftime( "%s", 0, 0, 12, $day, $month - 1, $year - 1900 ); # see the manual
		$epoch_week = sprintf( "%d", ($seconds + 259200) / 604800 );

		# remember the week
		my $week = POSIX::strftime( "%V", 0, 0, 12, $day, $month - 1, $year - 1900 ); # see the manual
		$epoch_week_to_year{$epoch_week} = sprintf( "$year-w%02d", $week );
	    }

	    $filerec{date} = $epoch_week;
	    $filerec{pretty_date} = $epoch_week_to_year{$epoch_week};

	    push @files, \%filerec;
	}
#	elsif ($verbose) { # don't touch a global variable it's bad news
#	    print STDERR "invalid line in apache logs: '$line'\n";
#	}
    }

    return @files;
}

sub parse_type($@)
{
    my $type = shift;
    my @file_list = @_;
    my @results;
    my $log;

    while (@file_list) {
	my $files = "";
	for (my $i = 0; $i < $bzcat_grouping; $i++) {
	    my $file = shift (@file_list) || next;
	    $files = "$files $file";
	}
	open ($log, "$type $files |") || die "Can't '$type $files': $!";
	push @results, parse_log($log);
	close $log;
	print STDERR ".";
    }

    return @results;
}

sub parse_logs($)
{
    my $filelist = shift;
    my @results;
    my @bzipped;
    my @gzipped;

    for my $file (@{$filelist}) {
	if ($file =~ m/\.bz2$/) {
	    push @bzipped, $file;
	} elsif ($file =~ m/\.gz$/) {
	    push @gzipped, $file;
	} else {
	    my $log;
	    open ($log, "$file") || die "Can't open '$file': $!";
	    push @results, parse_log($log);
	    close $log;
	}
    }

    push @results, parse_type('bzcat', @bzipped);
    push @results, parse_type('zcat',  @gzipped);

    return \@results;
}

sub merge_results($)
{
    my $list = shift;

    for my $filerec (@{$list}) {

	# without helppacks and langpacks
	next if ( $filerec->{langpack} );

	# build list of files
	my $file = $filerec->{file};
	if (!defined $all_files_list{$file}) {
	    $all_files_list{$file} = 0;
	}
	$all_files_list{$file}++;

	my $date = $filerec->{pretty_date};
	my $ver = $filerec->{version};
	my $product = $filerec->{product};

	# accumulate products
	$products{$product} = 1;

	# aggregate versions
	$allversions{$ver} = 1;

	$total_downloads++;

	# aggregate by product
	if ( !defined( $date_product_count{$date} ) ||
	     !defined( $date_product_count{$date}{$product} ) ) {
	    $date_product_count{$date}{$product} = 0;
	}
	++$date_product_count{$date}{$product};

	# aggregate by version
	if ( !defined( $date_version_count{$date} ) ||
	     !defined( $date_version_count{$date}{$ver} ) ) {
	    $date_version_count{$date}{$ver} = 0;
	}
	++$date_version_count{$date}{$ver};
    }
}

sub spawn_parse_log_thread($)
{
    my ($file_list) = @_;
    return threads->create( { 'context' => 'list' },
			    sub { return parse_logs($file_list); } );
}

while (my $arg = shift @ARGV) {
    if ($arg eq '-v' || $arg eq '--verbose') {
	$verbose = 1;
    } elsif ($arg eq '-c' || $arg eq '--cpus') {
	$cpus_to_use = shift @ARGV;
    } elsif ($arg eq '-u' || $arg eq '--update') {
	$rsync_first = 1;
    } elsif (!defined $path_to_log_tree) {
	$path_to_log_tree = $arg;
    } else {
	die "Unknown parameter '$arg'";
    }
}

if (!defined $path_to_log_tree) {
    $path_to_log_tree = `pwd`;
    chomp ($path_to_log_tree);
    $path_to_log_tree = "$path_to_log_tree/downloads";
}

# update first
if ($rsync_first) {
    system('rsync --delete -av bilbo.documentfoundation.org:/var/log/apache2/download.documentfoundation.org/ downloads/download.documentfoundation.org/ 1>&2');
    system('rsync --delete -av bilbo.documentfoundation.org:/var/log/apache2/downloadarchive.documentfoundation.org/ downloads/downloadarchive.documentfoundation.org/ 1>&2');
    system('rsync -av bilbo2.documentfoundation.org:/var/log/apache2/download.documentfoundation.org/ downloads/bilbo2.documentfoundation.org/ 1>&2');
}

my @log_filenames = find_logs ($path_to_log_tree);
if ($verbose) {
    print STDERR "Have log paths of:\n\t" . (join("\n\t", @log_filenames)) . "\n";
}

# the slow piece - parsing the logs
my $files_in = @log_filenames;
my $parallel = $cpus_to_use;
print STDERR "reading log data $files_in files:\n";

if ($threaded) {
    # divide up the work first.
    my @thread_files;
    for (my $i = 0; $i < $parallel; $i++) {
	my @foo; $thread_files[$i] = \@foo;
    }
    while (@log_filenames) {
	for (my $i = 0; $i < $parallel; $i++) {
	    my $file = shift (@log_filenames) || next;
	    push @{$thread_files[$i]}, $file;
	}
    }

    my @threads;
    for (my $i = 0; $i < $parallel; $i++) {
	my $file_list = $thread_files[$i];
	if (scalar (@{$file_list}) > 0) {
	    push @threads, spawn_parse_log_thread ($file_list);
	}
    }

    print STDERR "joining threads: ";
    while (@threads) {
	my $thread = shift @threads;
	merge_results($thread->join());
	print STDERR "joined";
    }
    print STDERR "\n";
} else {
    merge_results(parse_logs(\@log_filenames));
}

my $generated_stamp = "Generated on: " . qx(date --rfc-3339=seconds);

# ---------------------------------------------------------------------------------

# now output this as a spreadsheet ... fods ...

print << "EOF"
<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
                 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
                 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
                 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
                 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 xmlns:dc="http://purl.org/dc/elements/1.1/"
                 xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
                 xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
                 xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
                 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
                 xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0"
                 xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0"
                 xmlns:math="http://www.w3.org/1998/Math/MathML"
                 xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0"
                 xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0"
                 xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"
                 xmlns:ooo="http://openoffice.org/2004/office"
                 xmlns:ooow="http://openoffice.org/2004/writer"
                 xmlns:oooc="http://openoffice.org/2004/calc"
                 xmlns:dom="http://www.w3.org/2001/xml-events"
                 xmlns:xforms="http://www.w3.org/2002/xforms"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:rpt="http://openoffice.org/2005/report"
                 xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2"
                 xmlns:xhtml="http://www.w3.org/1999/xhtml"
                 xmlns:grddl="http://www.w3.org/2003/g/data-view#"
                 xmlns:tableooo="http://openoffice.org/2009/table"
                 xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0"
                 xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0"
                 xmlns:css3t="http://www.w3.org/TR/css3-text/"
                 office:version="1.2"
                 grddl:transformation="http://docs.oasis-open.org/office/1.2/xslt/odf2rdf.xsl"
                 office:mimetype="application/vnd.oasis.opendocument.spreadsheet">
   <office:styles>
      <number:date-style style:name="isodatenum">
         <number:year number:style="long"/>
         <number:text>-</number:text>
         <number:month number:style="long"/>
         <number:text>-</number:text>
         <number:day number:style="long"/>
      </number:date-style>
      <number:percentage-style style:name="percent-number">
        <number:number number:decimal-places="2" number:min-integer-digits="1"/>
        <number:text>%</number:text>
      </number:percentage-style>
      <style:style style:name="boldheader" style:family="table-cell" style:parent-style-name="Default">
         <style:text-properties fo:font-style="italic" fo:font-weight="bold"/>
      </style:style>
      <style:style style:name="isodate" style:family="table-cell" style:parent-style-name="Default"/>
      <style:style style:name="percent" style:family="table-cell" style:parent-style-name="Default"
       style:data-style-name="percent-number"/>
   </office:styles>
   <office:body>
      <office:spreadsheet>
         <table:table table:name="Graphs">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>$generated_stamp</text:p>
               </table:table-cell>
            </table:table-row>
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Total downloads:</text:p>
               </table:table-cell>
            </table:table-row>
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="float"
                office:value="$total_downloads"/>
            </table:table-row>
	 </table:table>
         <table:table table:name="ProductData">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Date</text:p>
               </table:table-cell>
EOF
;

# ---------------------------------------------------------------------------------

# By Product sheet

my @prods = sort keys %products;
for my $product (@prods) {
print << "EOF"
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>$product</text:p>
               </table:table-cell>
EOF
	    ;
}
print << "EOF"
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Total</text:p>
               </table:table-cell>
            </table:table-row>
EOF
;

my $row = 1;

my $colcount = @prods;
my $colname = coltoref ($colcount);
# print STDERR "cols: $colcount - colname $colname @prods\n";

for my $date (sort keys %date_product_count) {
print << "EOF"
            <table:table-row>
EOF
;
    print_date_cell("isodate", $date);
    for my $product (@prods) {
	my $count = $date_product_count{$date}->{$product};
	$count = 0 if (!defined $count);
print << "EOF"
               <table:table-cell office:value-type="float" office:value="$count"/>
EOF
;
    }
    $row++;
print << "EOF"
               <table:table-cell table:formula="of:=SUM([.B$row:.$colname$row])" office:value-type="float"/>
            </table:table-row>
EOF
;
}

# Summary / formulae
{
    print << "EOF"
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Total</text:p>
               </table:table-cell>
EOF
    ;
    my $col;
    for ($col = 1; $col <= $colcount + 1; $col++) {
	my $ref = coltoref ($col);
	print ("               <table:table-cell table:formula=\"of:=SUM([.$ref"."2:.$ref$row])\" office:value-type=\"float\"/>\n");
    }

print << "EOF"
            </table:table-row>
EOF
    ;
}

# Summary as %ages ...

{
    print << "EOF"
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Percent</text:p>
               </table:table-cell>
EOF
    ;
    my $col;
    $row++;
    my $totalref = coltoref($colcount + 1) . "$row";
    for ($col = 1; $col <= $colcount + 1; $col++) {
	my $ref = coltoref ($col);
	print ("               <table:table-cell table:style-name=\"percent\" table:formula=\"of:=[.$ref$row]/[.$totalref]\" office:value-type=\"percentage\"/>\n");
    }

print << "EOF"
            </table:table-row>
         </table:table>
EOF
    ;
}

# ---------------------------------------------------------------------------------

# By version sheet

# First collapse trivial / invalid versions - under 0.2%
my @todelete = ();
my $threshold = (2 * $total_downloads) / 1000;
for my $version (keys %allversions) {
    my $total = 0;
    for my $date (keys %date_version_count) {
	my $count = $date_version_count{$date}->{$version};
	$count = 0 if(!defined $count);
	$total = $total + $count;
    }
    if ($total < $threshold) {
#	print STDERR "collapsing trivial version '$version' count $total into 'invalid'\n";
	push @todelete, $version;
	for my $date (keys %date_version_count) {
	    my $count = $date_version_count{$date}->{$version};
	    if (defined $count) {
		if (!defined $date_version_count{$date}->{'invalid'}) {
		    $date_version_count{$date}->{'invalid'} = $count;
		} else {
		    $date_version_count{$date}->{'invalid'} += $count;
		}
	    }
	}
    }
}
if (@todelete) {
    for my $version (@todelete) {
	delete $allversions{$version};
    }
    $allversions{'invalid'} = 1; # so we get the result
}

print << "EOF"
         <table:table table:name="Versions">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Date</text:p>
               </table:table-cell>
EOF
;
for my $version (sort keys %allversions) {
print << "EOF"
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>$version</text:p>
               </table:table-cell>
EOF
	    ;
}
print << "EOF"
            </table:table-row>
EOF
    ;
    for my $date (sort keys %date_version_count) {
print << "EOF"
            <table:table-row>
EOF
;
        print_date_cell("isodate", $date);
        for my $ver (sort keys %allversions) {
	    my $count = $date_version_count{$date}->{$ver};
	    $count = 0 if(!defined $count);
print << "EOF"
               <table:table-cell office:value-type="float" office:value="$count"/>
EOF
;
	}
print << "EOF"
            </table:table-row>
EOF
;
    }

print << "EOF"
         </table:table>
EOF
    ;

# ---------------------------------------------------------------------------------

#   misc. debugging / information

print << "EOF"
         <table:table table:name="Files">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Name</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>count</text:p>
               </table:table-cell>
            </table:table-row>
EOF
    ;

    for my $file (sort { $all_files_list{$b} <=> $all_files_list{$a} } keys %all_files_list) {
	my $count = $all_files_list{$file};
print << "EOF"
            <table:table-row>
               <table:table-cell office:value-type="string">
                  <text:p>$file</text:p>
               </table:table-cell>
               <table:table-cell office:value-type="float" office:value="$count"/>
            </table:table-row>
EOF
	    ;
    }

print << "EOF"
	 </table:table>
EOF
    ;

# ---------------------------------------------------------------------------------

# end of spreadsheet ...

print << "EOF"
      </office:spreadsheet>
   </office:body>
</office:document>
EOF
;
