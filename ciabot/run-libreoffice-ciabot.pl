#!/usr/bin/perl -w

use POSIX;

if ( ! -d 'core' ) {
    print STDERR "Not a directory with libreoffice repos!\n";
    exit 1;
}

sub error($) {
    my ( $message ) = @_;
    print STDERR "$message\n";
}

sub get_branches() {
    my %branches;
    if ( open REFS, "git show-ref |" ) {
        while ( <REFS> ) {
            chomp;
            if ( /^([^ ]*) refs\/remotes\/origin\/(.*)/ ) {
                if ( $2 ne 'HEAD' ) {
                    $branches{$2} = $1;
                }
            }
        }
        close REFS;
    }
    else {
        error( "Cannot call git show-ref." );
    }

    return \%branches;
}

sub timestamp() {
        return strftime("[%Y-%m-%d %H:%M:%S]", localtime);
}

sub report($$$) {
    my ( $repo, $old_ref, $new_ref ) = @_;
    my %old = %{$old_ref};
    my %new = %{$new_ref};
    my $ciabot = "timeout 60 libreoffice-ciabot.pl";
    my $ciaproxy = "| ( cd ~/bin/irker-cia-proxy/; python irker-cia-proxy.py -s )";

    foreach my $key ( keys %new ) {
        my $branch_name = $key;
        $branch_name = '' if ( $branch_name eq 'master' );
        if ($branch_name =~ /aoo\//) {
            next;
        }

        my $old_head = $old{$key};
        my $new_head = $new{$key};

        if ( defined( $old_head ) ) {
            if ( $old_head ne $new_head ) {
                my $ret = system("git rev-parse -q --verify $new_head^2 >/dev/null");
                if ($ret != 0) {
                    # not a merge commit, announce every commit

                    # limit the number of commits we report
                    my $limit = 25;
                    if ( `git rev-list $new_head ^$old_head | wc -l` > 25 ) {
                        # something is wrong - probably a big rebase,
                        # or something, report just 1 commit
                        $limit = 1;
                    }
                    if ( open COMMITS, "git rev-list -n $limit $new_head ^$old_head | tac |" ) {
                        while ( <COMMITS> ) {
                            chomp;
                            print timestamp() . " Sending report about $_ in $key\n";
                            if (!$test) {
                                if ($repo eq "si-gui")
                                {
                                    qx(perl -I ~/bin ~/bin/sigui-bugzilla.pl $repo $_ $branch_name);
                                } else {
                                    qx($ciabot $repo $_ $branch_name $ciaproxy);
                                    qx(perl -I ~/bin ~/bin/libreoffice-bugzilla.pl $repo $_ $branch_name);
                                }
                            } else {
                                print "$ciabot '$repo' '$_' '$branch_name' $ciaproxy\n";
                                print "perl -I ~/bin ~/bin/libreoffice-bugzilla.pl '$repo' '$_' '$branch_name'\n";
                            }
                        }
                        close COMMITS;
                    }
                    else {
                        error( "Cannot call git rev-list." );
                    }
                } else {
                    # just process the merge commit itself
                    print timestamp() . " Sending report about $new_head in $key\n";
                    if (!$test) {
                        qx($ciabot $repo $new_head $branch_name $ciaproxy);
                        # no libreoffice-bugzilla.pl call for the merge commit
                    } else {
                        print "$ciabot '$repo' '$new_head' '$branch_name' $ciaproxy\n";
                    }
                }
            }
        }
        else {
            # Report the newest commit which is not in master
            if ( open COMMITS, "git rev-list -n 1 $new_head ^refs/remotes/origin/master |" ) {
                while ( <COMMITS> ) {
                    chomp;
                    print timestamp() . " Sending report about $_ in $key (newly created branch)\n";
                    if (!$test) {
                        qx($ciabot $repo $_ $branch_name $ciaproxy);
                        # no libreoffice-bugzilla.pl call for newly created branch
                    } else {
                        print "$ciabot '$repo' '$_' '$branch_name' $ciaproxy\n";
                    }
                }
                close COMMITS;
            }
            else {
                error( "Cannot call git rev-list." );
            }
        }
    }
}

print timestamp() . " Checking for changes in the libreoffice repo & sending reports to CIA.vc.\n";

@all_repos = (
    "binfilter",
    "core",
    "dictionaries",
    "help",
    "si-gui",
);

$test = 0;

if ($test) {
    @all_repos = ("test");
}

chomp( my $cwd = `pwd` );

my %old_ref;
foreach $repo (@all_repos) {
    chdir "$cwd/$repo";
    qx(git fetch origin);
    qx(git fetch --tags origin);
    $old_ref{$repo} = get_branches();
}

while ( 1 ) {
    foreach $repo (@all_repos) {
        chdir "$cwd/$repo";

        # update
        qx(git fetch origin);
        qx(git fetch --tags origin);
        my $new_ref = get_branches();

        # report
        report( $repo, $old_ref{$repo}, $new_ref );
        $old_ref{$repo} = $new_ref;
    }

    if (!$test) {
        # check every 5 minutes
        print timestamp() . " Sleeping for 5 minutes...\n";
        sleep 5*60;
    } else {
        print "Hit enter to report...\n";
        <STDIN>;
    }
}

# vim:set shiftwidth=4 softtabstop=4 expandtab:
