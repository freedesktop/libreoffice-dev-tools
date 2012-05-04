#!/usr/bin/perl -w
#
# This script parses, and interprets the output from:
#   pg_dump -a downloadstats -f stats_counter -F plain -t stats_counter
# on a mirrorbrain server, thus:
#   cat stats_counter | ./dlstats.pl --libo  > /tmp/output.fods
#
# It also parses the mirrorbrain data from an Apache server ...
# wget http://download.services.openoffice.org/stats/csv/201201.csv # etc ...
# cat 201201.csv 201202.csv 201203.csv | dlstats.pl --csv > /tmp/output.fods
#
# It also parses raw sql reload dumps
#
use strict;

# segment by Date, then by Product, then count
my %data;
my %products;
my %prod_names;
my %byregion;
my %countries;
my %byversion;
my %allversions;
my $total_downloads = 0;

# FIXME: ODF is -incredibly- lame in this regard ... we badly want R1C1 style referencing here [!]
sub coltoref($)
{
    my $col = shift;
    die ("odff needs R1C1") if ($col > 25);
    return chr (ord('A') + $col);
}

my $log_format;
for my $arg (@ARGV) {
    die "pass --csv --libo or --sql" if ($arg eq '--help' || $arg eq '-h');
    $log_format = 'c' if ($arg eq '--csv' || $arg eq '-c');
    $log_format = 'l' if ($arg eq '--libo' || $arg eq -'l');
    $log_format = 's' if ($arg eq '--sql' || $arg eq -'s');
}
defined $log_format || die "you must pass a format type";
# select the format you want

print STDERR "Log format: $log_format\n";

# Analysing stats:
#
# grep for 'multi' - yields the Windows installer ... (also grep for 'all_lang') - all of them [!]
# grep for 'Linux' and 'en-US' yields total Linux main binary downloads ...
# grep for 'Mac' and 'en-US' yields total Mac main binary numbers ...

while (<STDIN>) {
    chomp();
    my $line = $_;
    my ($id, $date, $product, $osname, $version, $lang, $country, $count);

    $line =~ s/[\s\r\n]*$//;
#    print STDERR "line '$line'\n";

    my $type;
    my $clean_product;

    if ($log_format eq 'l' && # a database dump from mirrorbrain:
#    17424    2011-01-25      LibO	Win-x86	3.3.0	        all_lang	qa	1
	$line =~ m/^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$/) {
	($id, $date, $product, $osname, $version, $lang, $country, $count) = ($1, $2, $3, $4, $5, $6, $7, $8);

#	print "$count downloads on date $date, os $osname $lang\n";

	if ($date lt '2011-01-25') {
#	    print STDERR "ignoring $date\n";
	    next
	}

	$prod_names{$product} = 1;
	# Ignore Mac / Linux help packs etc.
	if (($osname =~ /Linux/ || $osname =~ /MacOS/) && $lang eq 'en-US') {
	    $clean_product = $osname;
	}
	# Detect Windows distinctions
 	if (($product eq 'LibO' || $product eq 'LO' || $product eq 'BrOffice') &&
	    $osname =~ /Win/ && ($lang =~ /multi/ || $lang =~ /all_lang/)) {
	    $clean_product = "$osname-$lang";
	}

	# Detect PortableOffice distinctions
	if ($product eq 'LibreOfficePortable') {
	    $clean_product = "Portable";
	}

	# Detect DVD image
	if ($product eq 'LibO-DVD') {
	    $clean_product = "DVD";
 	}

	# Count product downloads by region
	if (defined $clean_product) {
	    $type = 'product';
	} else {
#	    print STDERR "lang pack line '$line'\n";
	    $type = 'lang pack';
        }

    } elsif ($log_format eq 'c' &&
#    2012-01-03,OOo,3.3.0,Linux_x86-64_langpack-deb,as,se,1
	     $line =~ m/^\s*(\S+),(\S+),(\S+),(\S+),(\S+),(\S+),(\d+)\s*$/) {
	my $project;
	($date, $project, $version, $product, $lang, $country, $count) = ($1, $2, $3, $4, $5, $6, $7);
#	ERROR - convert the product ! ... to
#	    $clean_product and $type ...
	if ($project =~ m/SDK/i) {
	    $product = 'sdk';
	}
	if ($product =~ m/langpack/i) {
	    $type = 'lang pack';
	} else {
	    $type = 'product'
	}
	$prod_names{$product} = 1;
	$clean_product = $product;
	$clean_product =~ s/_langpack//;
	$clean_product =~ s/_install//;
	$clean_product =~ s/-wJRE//;
	$clean_product =~ s/-deb//;
	$clean_product =~ s/-rpm//;

#	print STDERR "$count downloads of $clean_product on date $date, of $lang from $country\n";
    } elsif ($log_format eq 's') {
#       INSERT INTO `clean_downloads` (`date`, `product`, `os`, `language`, `version`, `downloads`) VALUES
#       ('2008-12-21', 'OpenOffice.org', 'winwjre', 'es', '3.0.0ï¿½', 1),
	if ( $line =~ m/^\('(\S+)',\s*'(\S+)',\s*'(\S+)',\s*'(\S+)',\s*'([^']+)',\s*(\d+)\s*\)[,;]\s*$/) {
	    my $project;
	    ($date, $project, $product, $country, $version, $count) = ($1, $2, $3, $4, $5, $6);

	    if ($product =~ m/langpack/) {
		$type = 'lang pack';
	    } else {
		$type = 'product';
	    }

	    if ($product =~ m/linux/i) {
		$clean_product = "linux";
	    } elsif ($product =~ m/win/i) {
		$clean_product = "win";
	    } elsif ($product =~ m/mac/i) {
		$clean_product = "mac";
	    } elsif ($product =~ m/solar/i) {
		$clean_product = "solaris";
	    } else {
		$clean_product = "other";
	    }
	    if ($product =~ m/64/) {
		$clean_product = $clean_product . "64";
	    }

	    if ($version =~ m/^(\d+\.\d+\.\d+)/) {
		$version = $1;
	    } elsif ($version =~ m/^(\d+\.\d+)/) {
		$version = $1 . ".0";
	    } elsif ($version =~ m/^(\d+)/) {
		$version = $1 . ".0.0";
	    } elsif ($version =~ /^(...\d\d\d_m\d+)/) {
		$version = $1;
	    } else {
#		print STDERR "invalid version: '$version'\n";
		$version = 'invalid';
	    }

#	    print STDERR "$count downloads of $product on date $date, from $country\n";
# INSERT INTO `clean_downloads_summary` (`product`, `os`, `language`, `date`, `downloads`, `smooth_downloads`) VALUES'
#       ('BrOffice.org', 'linuxintel', 'pt-BR', '2008-10-13', 155, 155),
	} elsif ( $line =~ m/^\('(\S+)',\s*'(\S+)',\s*'(\S+)',\s*'(\S+)',\s*'([^']+)',\s*(\d+)\s*\)[,;]\s*$/) { # need new regex
	    # odd - duplicate data ? ignore it ...
	} else {
#	    print STDERR "malformed sql line '$line'\n";
	    next;
	}
    } else {
	print STDERR "malformed line '$line'\n";
	next;
    }

    # Accumulate versions by date for products
    if ($type eq 'product') {
	my $byver;
	if (!defined $byversion{$date}) {
	    my %byver = ();
	    $byversion{$date} = \%byver;
	}
	my $norc_ver = $version; # remove 3.4.2-1 (rc1) type versions
	$norc_ver =~ s/\-\d$//;
	$allversions{$norc_ver} = 1;
	if (!defined $byversion{$date}->{$norc_ver}) {
	    $byversion{$date}->{$norc_ver} = 0;
	}
	$byversion{$date}->{$norc_ver} += $count;
    }

    my %hash;
    $byregion{$type} = \%hash if (!defined $byregion{$type});
    $byregion{$type}->{$country} = 0 if (!defined $byregion{$type}->{$country});
    $byregion{$type}->{$country} += $count;
    $countries{$country} = 1;

    if (!defined $clean_product) {
#	    print "uninteresting line '$line'\n";
	next;
    }

    $total_downloads += $count;

    $products{$clean_product} = 1;
    if (!defined $data{$date}) {
	my %byproduct;
	$data{$date} = \%byproduct;
    }
    if (!defined ($data{$date}->{$clean_product})) {
	$data{$date}->{$clean_product} = 0;
    }
    $data{$date}->{$clean_product} += $count;
# 	print "count for '$date' and '$clean_product' == $data{$date}->{$clean_product} [ added $count ]\n";
}

print STDERR "Dirty product names:\n";
for my $prod (sort keys %prod_names) {
    print STDERR "\t$prod\n";
}

# now output this as a spreadsheet ... fods ...
print << 'EOF'
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
      <style:style style:name="boldheader" style:family="table-cell" style:parent-style-name="Default">
         <style:text-properties fo:font-style="italic" fo:font-weight="bold"/>
      </style:style>
      <style:style style:name="isodate" style:family="table-cell" style:parent-style-name="Default" style:data-style-name="isodatenum"/>
   </office:styles>
   <office:body>
      <office:spreadsheet>
         <table:table table:name="Graphs">
	 </table:table>
         <table:table table:name="ProductData">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Date</text:p>
               </table:table-cell>
EOF
;
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
print STDERR "cols: $colcount - colname $colname @prods\n";

for my $date (sort keys %data) {
print << "EOF"
            <table:table-row>
               <table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="$date"/>
EOF
;
    for my $product (@prods) {
	my $count = $data{$date}->{$product};
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

print << "EOF"
            <table:table-row>
               <table:table-cell/>
EOF
    ;
    my $col;
    for ($col = 1; $col <= $colcount + 1; $col++) {
	my $ref = coltoref ($col);
	print ("               <table:table-cell table:formula=\"of:=SUM([.$ref"."2:.$ref$row])\" office:value-type=\"float\"/>\n");
    }

print << "EOF"
            </table:table-row>
         </table:table>
EOF
    ;


# LangData sheet

print << "EOF"
         <table:table table:name="LangData">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Location</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>product</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>lang-pack</text:p>
               </table:table-cell>
            </table:table-row>
EOF
    ;
    for my $country (sort keys %countries) {
	my $product = 0; my $lang_pack = 0;
	$product += $byregion{'product'}->{$country} if (defined $byregion{'product'}->{$country});
	$lang_pack += $byregion{'lang pack'}->{$country} if (defined $byregion{'lang pack'}->{$country});
print << "EOF"
            <table:table-row>
               <table:table-cell office:value-type="string"><text:p>$country</text:p></table:table-cell>
               <table:table-cell office:value-type="float" office:value="$product"/>
               <table:table-cell office:value-type="float" office:value="$lang_pack"/>
            </table:table-row>
EOF
;
    }

print << "EOF"
         </table:table>
EOF
;

# By version sheet

# First collaps trivial / invalid versions - under 0.1% - particularly for the sql dbase
my @todelete = ();
my $threshold = $total_downloads / 1000;
for my $version (keys %allversions) {
    my $total = 0;
    for my $date (keys %byversion) {
	my $count = $byversion{$date}->{$version};
	$count = 0 if(!defined $count);
	$total = $total + $count;
    }
    if ($total < $threshold) {
	print STDERR "collapsing trivial version '$version' count $total into 'invalid'\n";
	push @todelete, $version;
	for my $date (keys %byversion) {
	    my $count = $byversion{$date}->{$version};
	    if (defined $count) {
		if (!defined $byversion{$date}->{'invalid'}) {
		    $byversion{$date}->{'invalid'} = $count;
		} else {
		    $byversion{$date}->{'invalid'} += $count;
		}
	    }
	}
    }
}
for my $version (@todelete) {
    delete $allversions{$version};
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
    for my $date (sort keys %byversion) {
print << "EOF"
            <table:table-row>
               <table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="$date"/>
EOF
;
        for my $ver (sort keys %allversions) {
	    my $count = $byversion{$date}->{$ver};
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

      </office:spreadsheet>
   </office:body>
</office:document>
EOF
;
