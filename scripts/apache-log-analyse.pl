#!/usr/bin/perl -w

use Date::Parse;
use Date::Format;

my %bydate;    # date -> page -> count
my %bydate_direct;
my %bydate_wiki; 
my %bydate_google;
my %referrers; # count of referrers by URL

my @month_names = ( 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' );

sub escape_entity($)
{
    my $str = shift;
    $str =~ s/\&/&amp;/g;
    return $str;
}

while (<>) {
    my $line = $_;
    my $slice = $line;
# wiki.documentfoundation.org.log:wiki.documentfoundation.org:80 190.69.122.160 - - [16/Oct/2011:08:17:18 +0200] "GET /Development/Easy_Hacks HTTP/1.1" 200 13665 "https://www.libreoffice.org/get-involved/" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.202 Safari/535.1"
    my ($server, $host, $date, $page, $referrer);
    if ($slice =~ s/^[^:]+:([^:]+):\d+\s+([\d\.]+)\s+-\s+-\s+//) {
	$server = $1; $host = $2;

# [11/Oct/2011:06:26:20 +0200] "GET /Development/Easy_Hacks_by_Difficulty/be HTTP/1.1" 404 5516 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +https://www.google.com/bot.html)"
	if ($slice =~ s/^\[\s*([^\]]+)\s*\]\s+//) {
	    $date = $1;

# "GET /Development/Easy_Hacks HTTP/1.1" 200 13663 "-" "Mozilla/5.0 (compatible; ScoutJet; +http://www.scoutjet.com/)
	    if ($slice =~ s/^\"([^"]+)\"\s+\d+\s+\d+\s+//) {
		$page = $1;
# "https://wiki.documentfoundation.org/Development/Easy_Hacks" "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)"
		if ($slice =~ s/^\"([^"]*)\"//) {
		    $referrer = $1;
		    $referrer = '' if ($referrer eq '-');
#		    printf "line remainder $slice\n";
		} else {
		    die "invalid referrer: $slice";
		}
	    } else {
		die "invalid page fetch: $slice";
	    }
	} else {
	    die "invalid date in: $slice";
	}
    }
    else {
	die "invalid host in $slice";
    }

    # cleanup page
    $page =~ s/^GET\s+//;
    $page =~ s/s*HTTP\s*$//;
    $page =~ s/\s*HTTP\/[\d\.]*$//;

    # Mangle date into year-month
    my ($year, $month, $day);
    if ($date =~ m/([^\/]+)\/([^\/]+)\/([^\:]+):/) {
	$day = $1; $year = $3; $month = 0;
	my $cnt = 1;
	for my $abbr (@month_names) {
	    if ($abbr eq $2) {
		$month = $cnt;
		last;
	    }
	    $cnt++;
	}
	if ($month == 0) {
	    die "month not parseable: $2";
	}
    } else {
	die "invalid date '$date'";
    }

    $referrers{$referrer} = 0 if (!defined $referrers{$referrer});
    $referrers{$referrer} += 1;

    $monthkey = "$year-$month-01";
#    print "Date '$date' -> '$monthkey'\n";
    $bydate{$monthkey} = 0 if (!defined $bydate{$monthkey});
    $bydate_direct{$monthkey} = 0 if (!defined $bydate_direct{$monthkey});
    $bydate_wiki{$monthkey} = 0 if (!defined $bydate_wiki{$monthkey});
    $bydate_google{$monthkey} = 0 if (!defined $bydate_google{$monthkey});
    $bydate{$monthkey} += 1;
    $bydate_direct{$monthkey} += 1 if ($referrer eq '');
    $bydate_wiki{$monthkey} += 1 if ($referrer =~ 'wiki.documentfoundation');
    $bydate_google{$monthkey} += 1 if ($referrer =~ 'google');
}

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
         <table:table table:name="HitsByDate">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Date</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Hits</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Direct</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Direct</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Wiki</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Google</text:p>
               </table:table-cell>
            </table:table-row>
EOF
;
for my $date (sort keys %bydate) {
print << "EOF"
            <table:table-row>
               <table:table-cell table:style-name="isodate" office:value-type="date"
	        office:date-value="$date"/>
               <table:table-cell office:value-type="float" office:value="$bydate{$date}"/>
               <table:table-cell office:value-type="float" office:value="$bydate_direct{$date}"/>
               <table:table-cell office:value-type="float" office:value="$bydate_wiki{$date}"/>
               <table:table-cell office:value-type="float" office:value="$bydate_google{$date}"/>
            </table:table-row>
EOF
;
}
print << "EOF"
         </table:table>
         <table:table table:name="SourceURLs">
            <table:table-row>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>Count</text:p>
               </table:table-cell>
               <table:table-cell table:style-name="boldheader" office:value-type="string">
                  <text:p>URL</text:p>
               </table:table-cell>
            </table:table-row>
EOF
;

for my $ref (sort { $referrers{$b} <=> $referrers{$a} } keys %referrers) {
    my $url = escape_entity($ref);
print << "EOF"
            <table:table-row>
               <table:table-cell office:value-type="float" office:value="$referrers{$ref}"/>
               <table:table-cell office:value-type="string">
                  <text:p>$url</text:p>
               </table:table-cell>
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
