#!/usr/bin/perl -w

use FindBin;
use lib "$FindBin::Bin";

use strict;
use warnings;
use Bugzilla;

my @time = localtime;
$time[5] += 1900;
$time[4]++;

my $date_value = sprintf "%04d-%02d-%02d", @time[5,4,3];

sub build_overall_bugstats()
{
    print STDERR "Querying overall / top bug stats\n";
    my $bugserver = $Bugzilla::bugserver;
    my $url = "https://$bugserver/page.cgi?id=weekly-bug-summary.html";

    print STDERR "  + $url\n";
    my $closed_stats = Bugzilla::read_bugstats($url);

    print STDERR "    many thanks to the top bug squashers:\n";
    for my $name (sort { $closed_stats->{$b} <=> $closed_stats->{$a} } keys %{$closed_stats}) {
	printf STDERR "        %-20s%2s\n", $name, $closed_stats->{$name};
    }
}

my %bug_to_ver = (
    '4.4' => '79641',
    '4.3' => '75025',
    '4.2' => '65675',
    '4.1' => '60270',
    '4.0' => '54157',
    '3.6' => '44446'
);

my %ver_open;
my %ver_total;

build_overall_bugstats();

print STDERR "Querying for open MABs:\n";
for my $ver (reverse sort keys %bug_to_ver) {
    my $bug = $bug_to_ver{$ver};
    my $base_url = "https://$Bugzilla::bugserver/showdependencytree.cgi?id=" . $bug;
    my $all = Bugzilla::get_deps($base_url);
    my $open = Bugzilla::get_deps($base_url . "&hide_resolved=1");
    my $percent = sprintf("%2d", (($open * 100.0) / $all));
    print STDERR "$ver: $open/$all - $percent%\n";
    $ver_open{$ver} = $open;
    $ver_total{$ver} = $all;
}

my ($reg_all, $reg_open);

print STDERR "Querying for regressions:\n";
my $regression_query="https://$Bugzilla::bugserver/buglist.cgi?columnlist=bug_severity%2Cpriority%2Ccomponent%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc&keywords=regression%2C%20&keywords_type=allwords&list_id=267671&product=LibreOffice&query_format=advanced&order=bug_id&limit=0";
my $regression_open_query="https://$Bugzilla::bugserver/buglist.cgi?keywords=regression%2C%20&keywords_type=allwords&list_id=267687&columnlist=bug_severity%2Cpriority%2Ccomponent%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc&resolution=---&query_based_on=Regressions&query_format=advanced&product=LibreOffice&known_name=Regressions&limit=0";
$reg_all = Bugzilla::get_query($regression_query);
$reg_open = Bugzilla::get_query($regression_open_query);

print STDERR "Querying for bibisection:\n";
my $bibisect_query = "https://$Bugzilla::bugserver/buglist.cgi?n2=1&f1=status_whiteboard&list_id=267679&o1=substring&resolution=---&resolution=FIXED&resolution=INVALID&resolution=WONTFIX&resolution=DUPLICATE&resolution=WORKSFORME&resolution=MOVED&resolution=NOTABUG&resolution=NOTOURBUG&query_based_on=BibisectedAll&o2=substring&query_format=advanced&f2=status_whiteboard&v1=bibisected&v2=bibisected35older&product=LibreOffice&known_name=BibisectedAll&limit=0";
my $bibisect_open_query = "https://$Bugzilla::bugserver/buglist.cgi?n2=1&f1=status_whiteboard&list_id=267685&o1=substring&resolution=---&query_based_on=Bibisected&o2=substring&query_format=advanced&f2=status_whiteboard&v1=bibisected&v2=bibisected35older&product=LibreOffice&known_name=Bibisected&limit=0";

my ($all, $open);
$all = Bugzilla::get_query($bibisect_query);
$open = Bugzilla::get_query($bibisect_open_query);
print STDERR "\n";
print STDERR "* Bibisected bugs open: whiteboard 'bibsected'\n";
print STDERR "\t+ $open (of $all) older ?\n";
print STDERR "\t\t+ http://bit.ly/VQfF3Q\n";
print STDERR "\n";

print STDERR "* all bugs tagged with 'regression'\n";
print STDERR "\t+ $reg_open(+?) bugs open of $reg_all(+?) total\n";
print STDERR "\n";

my %component_count;

my %obsolete_components = ( 'Migration' => 1 );

# custom pieces
$component_count{'Migration'} = 0; # aBugzilla::get_deps("https://$Bugzilla::bugserver/showdependencytree.cgi?id=43489&hide_resolved=1"); - kill for now.
$component_count{'Crashes'} = Bugzilla::get_query("https://$Bugzilla::bugserver/buglist.cgi?keywords=regression&keywords_type=allwords&list_id=296015&short_desc=crash&query_based_on=CrashRegressions&query_format=advanced&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=NEEDINFO&short_desc_type=allwordssubstr&product=LibreOffice&known_name=CrashRegressions");
$component_count{'Borders'} = Bugzilla::get_query("https://$Bugzilla::bugserver/buglist.cgi?keywords=regression&keywords_type=allwords&list_id=296016&short_desc=border&query_based_on=BorderRegressions&query_format=advanced&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=NEEDINFO&short_desc_type=allwordssubstr&product=LibreOffice&known_name=BorderRegressions");

my @reg_toquery = ( 'Spreadsheet', 'Presentation', 'Database', 'Drawing', 'Libreoffice', 'Writer', 'BASIC', 'Chart', 'Extensions', 'Formula Editor', 'Impress Remote', 'Installation', 'Linguistic', 'Printing and PDF export', 'UI', 'filters and storage', 'framework', 'graphics stack', 'sdk' );
for my $component (@reg_toquery) {
    my $component_uri = Bugzilla::uri_escape($component);
    $component_count{$component} = Bugzilla::get_query("https://$Bugzilla::bugserver/buglist.cgi?keywords=regression&keywords_type=allwords&list_id=296025&query_format=advanced&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=PLEASETEST&component=$component_uri&product=LibreOffice");
}

print STDERR "\t* ~Component   count net *\n";
for my $component (sort { $component_count{$b} <=> $component_count{$a} } keys %component_count) {
    if (!defined $obsolete_components{$component}) {
	printf STDERR "\t  %12s - %2d (+?)\n", $component, $component_count{$component};
    }
}

print << "EOF"
<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
                 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
                 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
                 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
                 xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0"
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
      <style:style style:name="boldheader" style:family="table-cell" style:parent-style-name="Default">
         <style:text-properties fo:font-style="italic" fo:font-weight="bold"/>
      </style:style>
  <number:date-style style:name="isodatenum">
   <number:year number:style="long"/>
   <number:text>-</number:text>
   <number:month number:style="long"/>
   <number:text>-</number:text>
   <number:day number:style="long"/>
  </number:date-style>
  <style:style style:name="isodate" style:family="table-cell" style:parent-style-name="Default" style:data-style-name="isodatenum">
   <style:text-properties style:text-position=""/>
  </style:style>

   </office:styles>
   <office:body>
      <office:spreadsheet>
         <table:table table:name="Data">

    <table:table-row>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Date</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 3.5</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 3.5</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 3.6</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 3.6</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 4.0</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 4.0</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 4.1</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 4.1</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 4.2</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 4.2</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 4.3</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 4.3</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open 4.4</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed 4.4</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 3.5</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 3.6</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 4.0</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 4.1</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 4.2</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 4.3</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total 4.4</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total Open</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total Closed</text:p>
     </table:table-cell>
    </table:table-row>

    <table:table-row table:style-name="ro1">
     <table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="$date_value" calcext:value-type="date">
      <text:p>$date_value</text:p>
     </table:table-cell>
     <table:table-cell/> <!-- 3.5 -->
     <table:table-cell/>
     <table:table-cell/> <!-- 3.6 -->
     <table:table-cell/>
     <table:table-cell/> <!-- 4.0 -->
     <table:table-cell/>
     <table:table-cell/> <!-- 4.1 -->
     <table:table-cell/>
     <table:table-cell office:value-type="float" office:value="$ver_open{'4.2'}" calcext:value-type="float"/>
     <table:table-cell table:formula="of:=[.T2]-[.J2]" office:value-type="float"  calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_open{'4.3'}" calcext:value-type="float"/>
     <table:table-cell table:formula="of:=[.U2]-[.L2]" office:value-type="float"  calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_open{'4.4'}" calcext:value-type="float"/>
     <table:table-cell table:formula="of:=[.V2]-[.N2]" office:value-type="float"  calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="221" calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_total{'3.6'}" calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_total{'4.0'}" calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_total{'4.1'}" calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_total{'4.2'}" calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_total{'4.3'}" calcext:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$ver_total{'4.4'}" calcext:value-type="float"/>
     <table:table-cell table:formula="of:=[.B2]+[.D2]+[.F2]+[.H2]+[.J2]+[.L2]+[.N2]" office:value-type="float"/>
     <table:table-cell table:formula="of:=SUM([.P2:.V2])-[.W2]" office:value-type="float"/>
    </table:table-row>

    <table:table-row/>
    <table:table-row/>
    <table:table-row>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Date</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Open</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Closed</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Total</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>Date</text:p>
     </table:table-cell>
EOF
;

my @output_order = ( 'Spreadsheet', 'Presentation', 'Database', 'Drawing',
		     'Libreoffice', 'Borders', 'Crashes', 'BASIC', 'Writer/RTF',
		     'Writer', 'Migration',
             'Chart', 'Extensions', 'Formula Editor', 'Impress Remote',
             'Installation', 'Linguistic', 'Printing and PDF export', 'UI',
             'filters and storage', 'framework', 'graphics stack', 'sdk' );

for my $foo (@output_order) {
    print << "EOF"
     <table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">
      <text:p>$foo</text:p>
     </table:table-cell>
EOF
;
}

print << "EOF"
    </table:table-row>
    <table:table-row>
EOF
;

print << "EOF"
     <table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="$date_value" calcext:value-type="date">
      <text:p>$date_value</text:p>
     </table:table-cell>
     <table:table-cell office:value-type="float" office:value="$reg_open" calcext:value-type="float"/>
     <table:table-cell table:formula="of:=[.D6]-[.B6]" office:value-type="float"/>
     <table:table-cell office:value-type="float" office:value="$reg_all" calcext:value-type="float"/>
     <table:table-cell table:style-name="isodate" table:formula="of:=[.A6]" office:value-type="date" />
EOF
;

for my $foo (@output_order) {
    if (defined $component_count{$foo}) {
	print << "EOF"
	    <table:table-cell office:value-type="float" office:value="$component_count{$foo}" calcext:value-type="float"/>
EOF
;
	} else {
	    print "<table:table-cell/>\n";
	}
}

print << "EOF"
    </table:table-row>
   </table:table>
  </office:spreadsheet>
 </office:body>
</office:document>
EOF
;
