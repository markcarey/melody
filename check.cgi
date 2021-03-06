#!/usr/bin/perl -w

# Melody, based on Movable Type (r) Open Source (C) 2001-2009 Six Apart, Ltd.
# This program is distributed under the terms of the
# GNU General Public License, version 2.
#
# $Id$

use strict;
sub BEGIN {
    my $dir;
    if (eval { require File::Spec; 1; }) {
        if (!($dir = $ENV{MT_HOME})) {
            if ($0 =~ m!(.*[/\\])!) {
                $dir = $1;
            } else {
                $dir = './';
            }
            $ENV{MT_HOME} = $dir;
        }
        unshift @INC, File::Spec->catdir($dir, 'lib');
        unshift @INC, File::Spec->catdir($dir, 'extlib');
    }
}

my $cfg_exist;
my $static_path = q();
my $cgi_path;
if ((-f File::Spec->catfile($ENV{MT_HOME}, 'config.cgi')) ||
    (-f File::Spec->catfile($ENV{MT_HOME}, 'mt.cfg'))) {
    $cfg_exist = 1;
    my $file_handle = open(CFG, $ENV{MT_HOME}.'/mt.cfg') || open(CFG, $ENV{MT_HOME}.'/config.cgi');
    my $line;
    while ($line = <CFG>) {
        next if $line !~ /\S/ || $line =~ /^#/;
        if ($line =~ s/StaticWebPath[\s]*([^\n]*)/$1/) {
            $static_path = $line;
            chomp($static_path);
        }
        elsif ($line =~ s/CGIPath[\s]*([^\n]*)/$1/) {
            $cgi_path = $line;
            chomp($cgi_path);
        }
    }
    if ( !$static_path && $cgi_path ) {
        $cgi_path .= '/' if $cgi_path !~ m|/$|;
        $static_path = $cgi_path . 'mt-static/';
    }
}

local $| = 1;

use CGI;
my $cgi = new CGI;
my $view = $cgi->param("view");
my $version = $cgi->param("version");
# $version ||= '__PRODUCT_VERSION_ID__';

my ($mt, $LH);
my $lang = $cgi->param("language") || $cgi->param("__lang");
eval {
    require MT::App::Wizard;
    $mt = MT::App::Wizard->new();
    
    require MT::Util;
    $lang ||= MT::Util::browser_language();
    
    my $cfg = $mt->config;
    $cfg->PublishCharset('utf-8');
    $cfg->DefaultLanguage($lang);
    require MT::L10N;
    if ( $mt ) {
        $LH = $mt->language_handle;
        $mt->set_language($lang);
    }
    else {
        MT::L10N->get_handle($lang);
    }
};

sub trans_templ {
    my($text) = @_;
    return $mt->translate_templatized($text) if $mt;
    $text =~ s!(<MT_TRANS(?:\s+((?:\w+)\s*=\s*(["'])(?:<[^>]+?>|[^\3]+?)+?\3))+?\s*/?>)!
        my($msg, %args) = ($1);
        #print $msg;
        while ($msg =~ /\b(\w+)\s*=\s*(["'])((?:<[^>]+?>|[^\2])*?)\2/g) {  #"
            $args{$1} = $3;
        }
        $args{params} = '' unless defined $args{params};
        my @p = map decode_html($_),
                split /\s*%%\s*/, $args{params};
        @p = ('') unless @p;
        my $translation = translate($args{phrase}, @p);
        $translation =~ s/([\\'])/\\$1/sg if $args{escape};
        $translation;
    !ge;
    $text;
}

sub translate {
    return (
        $mt ? $mt->translate(@_)
            : $LH ? $LH->maketext(@_)
                  : merge_params(@_)
    );
}

sub decode_html {
    my($html) = @_;
    if ($cfg_exist && (eval 'use MT::Util; 1')) {
        return MT::Util::decode_html($html);
    } else {
        $html =~ s#&quot;#"#g;
        $html =~ s#&lt;#<#g;
        $html =~ s#&gt;#>#g;
        $html =~ s#&amp;#&#g;
    }
    $html;
}

sub merge_params {
    my ($msg, @param) = @_;
    my $cnt = 1;
    foreach my $p (@param) {
        $msg =~ s/\[_$cnt\]/$p/g;
        $cnt++;
    }
    $msg;
}

local( *CSS ) ;
open( CSS, $ENV{MT_HOME}.'/check.css' );
my $css = do { local( $/ ) ; <CSS> } ;
close(CSS);

$css =~ s{\$static_path}{$static_path}gi;

print "Content-Type: text/html; charset=utf-8\n\n";
if (!$view) {
    print trans_templ(<<HTML);

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <meta http-equiv="content-language" content="$lang" />
    
    <title><MT_TRANS phrase="Melody System Check"> [check.cgi]</title>
    
    <style type=\"text/css\">
        <!--
$css        
        //-->
    </style>

</head>

HTML
    if ($static_path) {
        print "<body class=\"has-static\">\n";
    } else {
        print "<body>\n";
    }
    print trans_templ(<<HTML);
<div id="header"><h1><MT_TRANS phrase="Melody System Check"> [check.cgi]</h1></div>

<div id="content">
<p class="msg msg-info"><MT_TRANS phrase="The check.cgi script provides you with information on your system's configuration and determines whether you have all of the components you need to run Melody."></p>
HTML
}

my $is_good = 1;
my (@REQ, @DATA, @OPT);

my @CORE_REQ = (
    [ 'Algorithm::Diff', 1.1902, 1],
    [ 'Cache', 2.04, 1],
    [ 'CGI', 3.50, 1 ],
    [ 'Class::Accessor', 0.22, 1 ],
    [ 'Class::Data::Inheritable', 0.06, 1],
    [ 'Class::Trigger', '0.1001', 1 ],
    [ 'Data::ObjectDriver', 0.06, 1 ],
    [ 'Digest::SHA1', 0.06, 1 ],
    [ 'File::Copy::Recursive', 0.23, 1],
    [ 'Heap::Fibonacci', 0.71, 1],
    [ 'HTML::Diff', 0.561, 1],
    [ 'HTML::Parser', 3.66, 0 ],
    [ 'Image::Size', 2.93, 1 ],
    [ 'JSON', 2.12, 1],
    [ 'Jcode', 0.88, 1],
    [ 'Locale::Maketext', 1.13, 1],
    [ 'Log::Dispatch', 2.26, 1],
    [ 'Log::Log4Perl', 1.30, 1],
    [ 'Lucene::QueryParser', 1.04, 1],
    [ 'LWP', 5.831, 1 ],
    [ 'Params::Validate', 0.73, 1],
    [ 'Sub::Install', 0.925, 1],
    [ 'TheSchwartz', 1.07, 0],
    [ 'URI', 1.36, 0],
    [ 'version', 0.76, 0],
    [ 'YAML::Tiny', 1.12, 1 ],
);

my @CORE_DATA = (
    [ 'DBI', 1.21, 0, translate('DBI is required to store data in database.') ],
    [ 'DBD::mysql', 0, 0, translate('DBI and DBD::mysql are required if you want to use the MySQL database backend.') ],
    [ 'DBD::Pg', 1.32, 0, translate('DBI and DBD::Pg are required if you want to use the PostgreSQL database backend.') ],
    [ 'DBD::SQLite', 0, 0, translate('DBI and DBD::SQLite are required if you want to use the SQLite database backend.') ],
    [ 'DBD::SQLite2', 0, 0, translate('DBI and DBD::SQLite2 are required if you want to use the SQLite 2.x database backend.') ],
);

my @CORE_OPT = (
    [ 'Archive::Tar', 0, 0, translate('Archive::Tar is needed in order to archive files in backup/restore operation.')],
    [ 'Archive::Zip', 0, 0, translate('Archive::Zip is needed in order to archive files in backup/restore operation.')],
    [ 'Attribute::Params::Validate', 1.7, 0, ''],
    [ 'bignum', 0.23, 0, ''], 
    [ 'Cache::Memcached', 0, 0, translate('Cache::Memcached and memcached server/daemon is needed in order to use memcached as caching mechanism used by Melody.')],
    [ 'Crypt::DH', 0.96, 0, translate('This module and its dependencies are required in order to allow commenters to be authenticated by OpenID providers ')],
    [ 'Crypt::DSA', 0, 0, translate('Crypt::DSA is optional; if it is installed, comment registration sign-ins will be accelerated.')],
    [ 'Crypt::SSLeay', 0, 0, translate('This module and its dependencies are required in order to allow commenters to be authenticated by OpenID providers that require SSL support.')],
    [ 'GD', 0, 0, translate('This module is needed if you would like to be able to create thumbnails of uploaded images.')],
    [ 'IO::Compress::Gzip', 0, 0, translate('IO::Compress::Gzip is needed in order to compress files in backup/restore operation.')],
    [ 'IO::Scalar', 2.110, 0, translate('IO::Scalar is needed in order to archive files in backup/restore operation.')],
    [ 'IO::Uncompress::Gunzip', 0, 0, translate('IO::Uncompress::Gunzip is required in order to decompress files in backup/restore operation.')],
    [ 'IPC::Run', 0, 0, translate('This module is needed if you would like to be able to use NetPBM as the image driver for Melody.')],
    [ 'Image::Magick', 0, 0, translate('Image::Magick is optional; It is needed if you would like to be able to create thumbnails of uploaded images.') ],
    [ 'MIME::Charset', 0.044, 0, translate('MIME::Charset is required for sending mail via SMTP Server.')],
    [ 'MIME::EncWords', 0.96, 0, translate('MIME::EncWords is required for sending mail via SMTP Server.')],
    [ 'Mail::Sendmail', 0, 0, translate('Mail::Sendmail is required for sending mail via SMTP Server.')],
    [ 'Net::OpenID::Consumer', 1.03, 0, translate('This module and its dependencies are required in order to allow commenters to be authenticated by OpenID providers ')],
    [ 'Path::Class', 0, 0, ''],
    [ 'SOAP::Lite', '0.710.08', 0, translate('SOAP::Lite is optional; It is needed if you wish to use the Melody XML-RPC server implementation.') ],
    [ 'XML::Atom', 0, 0, translate('XML::Atom is required in order to use the Atom API.')],
    [ 'XML::LibXML', 0, 0, translate('XML::LibXML is required in order to use the Atom API.')],
    [ 'XML::NamespaceSupport', 1.09, 0, translate('XML::NamespaceSupport is needed in order to archive files in backup/restore operation.')],
    [ 'XML::Parser', 2.23, 0, ''],
    [ 'XML::SAX', 0.96, 0, translate('XML::SAX is needed in order to archive files in backup/restore operation.')],
    [ 'XML::Simple', 2.14, 0, translate('XML::Simple is needed in order to archive files in backup/restore operation.')],
    [ 'XML::XPath', 0, 0, ''],
);

use Cwd;
my $cwd = '';
{
    my($bad);
    local $SIG{__WARN__} = sub { $bad++ };
    eval { $cwd = Cwd::getcwd() };
    if ($bad || $@) {
        eval { $cwd = Cwd::cwd() };
        if ($@ && $@ !~ /Insecure \$ENV{PATH}/) {
            die $@;
        }
    }
}

my $ver = ref($^V) eq 'version' ? $^V->normal : ( $^V ? join('.', unpack 'C*', $^V) : $] );
my $perl_ver_check = '';
if ($] < 5.008008) {  # our minimal requirement for support
    $perl_ver_check = <<EOT;
<p class="warning"><MT_TRANS phrase="The version of Perl installed on your server ([_1]) is lower than the minimum supported version ([_2]). Please upgrade to at least Perl [_2]." params="$ver%%5.8.8"></p>
EOT
}
my $config_check = '';
if (!$cfg_exist) {
    $config_check = <<CONFIG;
<p class="warning"><MT_TRANS phrase="Melody configuration file was not found."></p>
CONFIG
}
my $server = $ENV{SERVER_SOFTWARE};
my $inc_path = join "<br />\n", @INC;
print trans_templ(<<INFO);
<h2 id="system-info"><MT_TRANS phrase="System Information"></h2>
$perl_ver_check
$config_check
INFO
if ($version) {
    # sanitize down to letters numbers dashes and period
    $version =~ s/[^a-zA-Z0-9\-\.]//g;
print trans_templ(<<INFO);
<ul class="version">
    <li><strong><MT_TRANS phrase="Melody version:"></strong> <code>$version</code></li>
</ul>
INFO
}
print trans_templ(<<INFO);
<ul>
	<li><strong><MT_TRANS phrase="Current working directory:"></strong> <code>$cwd</code></li>
	<li><strong><MT_TRANS phrase="Melody home directory:"></strong> <code>$ENV{MT_HOME}</code></li>
	<li><strong><MT_TRANS phrase="Operating system:"></strong> $^O</li>
	<li><strong><MT_TRANS phrase="Perl version:"></strong> <code>$ver</code></li>
	<li><strong><MT_TRANS phrase="Perl include path:"></strong><br /> <code>$inc_path</code></li>
INFO
if ($server) {
print trans_templ(<<INFO);
    <li><strong><MT_TRANS phrase="Web server:"></strong> <code>$server</code></li>
INFO
}

## Try to create a new file in the current working directory. This
## isn't a perfect test for running under cgiwrap/suexec, but it
## is a pretty good test.
my $TMP = "test$$.tmp";
local *FH;
if (open(FH, ">$TMP")) {
    close FH;
    unlink($TMP);
    print trans_templ('    <li><MT_TRANS phrase="(Probably) Running under cgiwrap or suexec"></li>' . "\n");
}

print "\n\n</ul>\n";

exit if $ENV{QUERY_STRING} && $ENV{QUERY_STRING} eq 'sys-check';

#if ($mt) {
#    my $req = $mt->registry("required_packages");
#    foreach my $key (keys %$req) {
#        next if $key eq 'DBI';
#        my $pkg = $req->{$key};
#        push @REQ, [ $key, $pkg->{version} || 0, 1, $pkg->{label}, $key, $pkg->{link} ];
#    }
#    my $drivers = $mt->object_drivers;
#    foreach my $key (keys %$drivers) {
#        my $driver = $drivers->{$key};
#        my $label = $driver->{label};
#        my $link = 'http://search.cpan.org/dist/' . $driver->{dbd_package};
#        $link =~ s/::/-/g;
#        push @DATA, [ $driver->{dbd_package}, $driver->{dbd_version}, 0,
#            $mt->translate("The [_1] database driver is required to use [_2].", $driver->{dbd_package}, $label),
#            $label, $link ];
#    }
#    unshift @DATA, [ 'DBI', 1.21, 0, translate('DBI is required to store data in database.') ]
#        if @DATA;
#    my $opt = $mt->registry("optional_packages");
#    foreach my $key (keys %$opt) {
#        my $pkg = $opt->{$key};
#        push @OPT, [ $key, $pkg->{version} || 0, 0, $pkg->{label}, $key, $pkg->{link} ];
#    }
#}
@REQ  = @CORE_REQ;  #unless @REQ;
@DATA = @CORE_DATA; #unless @DATA;
@OPT  = @CORE_OPT;  #unless @OPT;

for my $list (\@REQ, \@DATA, \@OPT) {
    my $data = ($list == \@DATA);
    my $req = ($list == \@REQ);
    my $type;
    my $phrase = translate("Checking for");
    if ($data) {
        $type = translate("Data Storage");
    } elsif ($req) {
        $type = translate("Required");
    } else {
        $type = translate("Optional");
    }
    print trans_templ(qq{<h2><MT_TRANS phrase="[_1] [_2] Modules" params="$phrase%%$type"></h2>\n\t<div>\n});
    if (!$req && !$data) {
        print trans_templ(<<MSG);
    <p class="msg msg-info"><MT_TRANS phrase="The following modules are <strong>optional</strong>. If your server does not have these modules installed, you only need to install them if you require the functionality that the module provides."></p>

MSG
    }
    if ($data) {
        print trans_templ(<<MSG);
        <p class="msg msg-info"><MT_TRANS phrase="Some of the following modules are required by the various data storage options in Melody. In order run the system, your server needs to have DBI and at least one of the other modules installed."></p>

MSG
    }
    my $got_one_data = 0;
    my $dbi_is_okay = 0;
    for my $ref (@$list) {
        my($mod, $ver, $req, $desc) = @$ref;
#        if ('CODE' eq ref($desc)) {
#            $desc = $desc->();
#        }
        if (!$desc && $req) {
               $desc = trans_templ(qq{<MT_TRANS phrase="[_1] is required for standard Melody application functionality" params="$mod">});
        }
        print "<blockquote>\n" if $mod =~ m/^DBD::/;
        print "    <h3>$mod" .
            ($ver ? " (version &gt;= $ver)" : "") . "</h3>";
        eval("use $mod" . ($ver ? " $ver;" : ";"));
        if ($@) {
            $is_good = 0 if $req;
            my $link = 'http://search.cpan.org/perldoc?' . $mod;
            my $msg = $ver ?
                      trans_templ(qq{<p class="warning"><MT_TRANS phrase="Either your server does not have <a href="[_2]">[_1]</a> installed, the version that is installed is too old, or [_1] requires another module that is not installed." params="$mod%%$link"> }) :
                      trans_templ(qq{<p class="warning"><MT_TRANS phrase="Your server does not have <a href="[_2]">[_1]</a> installed, or [_1] requires another module that is not installed." params="$mod%%$link"> });
            $msg   .= $desc .
                      trans_templ(qq{ <MT_TRANS phrase="Please consult the installation instructions for help in installing [_1]." params="$mod"></p>\n\n});
            print $msg . "\n\n";
        } else {
            if ($data) {
                $dbi_is_okay = 1 if $mod eq 'DBI';
                if ($mod eq 'DBD::mysql') {
                    if ($DBD::mysql::VERSION == 3.0000) {
                        print trans_templ(qq{<p class="warning"><MT_TRANS phrase="The DBD::mysql version you have installed is known to be incompatible with Melody. Please install the current release available from CPAN."></p>});
                    }
                }
                if (!$dbi_is_okay) {
                    print trans_templ(qq{<p class="warning"><MT_TRANS phrase="The $mod is installed properly, but requires an updated DBI module. Please see note above regarding the DBI module requirements."></p>});
                } else {
                    $got_one_data = 1 if $mod ne 'DBI';
                }
            }
            print trans_templ(qq{<p class="installed"><MT_TRANS phrase="Your server has [_1] installed (version [_2])." params="$mod%%} . $mod->VERSION . qq{"></p>\n\n});
        }
        print "</blockquote>\n" if $mod =~ m/^DBD::/;
    }
    $is_good &= $got_one_data if $data;
    print "\n\t</div>\n\n";
}

if ($is_good && $cfg_exist) {
    if (!$view) {
    print trans_templ(<<HTML);
    
    <div class="msg msg-success">
        <h2><MT_TRANS phrase="Melody System Check Successful"></h2>
        <p><strong><MT_TRANS phrase="You're ready to go!"></strong> <MT_TRANS phrase="Your server has all of the required modules installed; you do not need to perform any additional module installations. Continue with the installation instructions."></p>
    </div>

</div>

HTML
    }
}

print "</body>\n\n</html>\n";
