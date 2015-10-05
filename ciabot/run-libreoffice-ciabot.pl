#!/usr/bin/perl -w

use POSIX;
use File::Basename;

open STDOUT, '>', dirname($0) . "/ciabot.out";
open STDERR, '>', dirname($0) . "/ciabot.err";

my $suffix = "";
my $cwd;

$cwd = `pwd`;
chomp $cwd;

if ( ! -d 'core' && ! -d 'core.git' ) {
    print STDERR "Not a directory with libreoffice repos!\n";
    exit 1;
}
if ( -d 'core.git' ) {
    $suffix=".git"
}
sub error($) {
    my ( $message ) = @_;
    print STDERR "$message\n";
}

#
# Get a list of filtered branch HEADs
#
# Gets all branches, except HEAD.
#
# @returns \%{ branch name => git branch head hashval }
#
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

#
# Should we generate Bugzilla comments?
#
# Report all commits for all repositories except 'core'. For 'core'
# just report libreoffice-* and master branches to Bugzilla.
#
# @returns true, if this commit should be reported to Bugzilla.
#
sub is_valid_bugzilla_commit($$) {
   my ( $repo, $branch ) = @_;
   return 1 if ( $repo ne 'core' );
   return 1 if ( $branch eq '' );
   return ( $branch =~ /^(libreoffice-[^\/]*|master)$/ );
}

sub timestamp() {
        return strftime("[%Y-%m-%d %H:%M:%S]", localtime);
}

#
# Report all branch changes to IRC and bugzilla.
#
# We just report changes filtered by is_valid_bugzilla_report to Bugzilla
# but inform IRC off all changes.
#
# $1 = repository name
# $2 = hashref of old branch heads (@see get_branches).
# $3 = hashref of new branch heads (@see get_branches).
#
sub report($$$) {
    my ( $repo, $old_ref, $new_ref ) = @_;
    my %old = %{$old_ref};
    my %new = %{$new_ref};
    my $ciabot = "timeout 60 $cwd/libreoffice-ciabot.pl";
    my $ciaproxy = "| ( cd $cwd && python irker-cia-proxy.py -s )";

    foreach my $key ( keys %new ) {
        my $branch_name = $key;
        $branch_name = '' if ( $branch_name eq 'master' );
        if ($branch_name =~ /aoo\/|distro\//) {
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
                                    qx(perl -I $cwd $cwd/sigui-bugzilla.pl $repo $_ $branch_name);
                                } else {
                                    if ( is_valid_bugzilla_commit( $repo, $branch_name ) ) {
					my $branch = $branch_name;
					$branch = 'master' if ($branch eq '');
					print "reporting to bugzilla: $_ and branch $branch";
                                        qx(python $cwd/libreoffice-bugzilla2.py -r $repo -c $_ -b $branch >> /home/ciabot/bugzilla.log);
                                    }
                                    qx($ciabot $repo $_ $branch_name $ciaproxy);
                                }
                            } else {
                                if ( is_valid_bugzilla_commit( $repo, $branch_name ) ) {
                                    print "python $cwd/libreoffice-bugzilla2.py -r '$repo' -c '$_' -b '$branch_name'\n";
                                }
                                print "$ciabot '$repo' '$_' '$branch_name' $ciaproxy\n";
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
    "core",
    "dictionaries",
    "help",
    "si-gui",
    "online",
    "contrib/dev-tools",
);

$test = 0;

if ($test) {
    @all_repos = ("test");
}


my %old_ref;
foreach $repo (@all_repos) {
    chdir "$cwd/$repo$suffix";
    qx(git fetch origin);
    qx(git fetch --tags origin);
    $old_ref{$repo} = get_branches();
}

while ( 1 ) {
    foreach $repo (@all_repos) {
        chdir "$cwd/$repo$suffix";

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
        print timestamp() . " Sleeping for 1 minute...\n";
        sleep 1*60;
    } else {
        print "Hit enter to report...\n";
        <STDIN>;
    }
}

# vim:set shiftwidth=4 softtabstop=4 expandtab:
